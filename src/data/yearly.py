import csv, os
from datetime import datetime
from typing import List, Optional, Tuple
import ubidots.device.aws as ubidotsaws
import ubidots.device.data as ubidotsdata
import pandas as pd
import requests
import util as utils
from datetime import datetime

class WaterTempRecord:
    def __init__(self, date: str, water_temperature: Optional[float]):
        self.date = date
        self.water_temperature = water_temperature


class Record:
    def __init__(self, date: str, precipitation: float):
        self.date = date
        self.precipitation = precipitation


def year_to_date_temperature_to_csv(site_directory, token: str, variables:List[str]) -> None:
    start, end = utils.this_year()

    # MOVED TO CONFIG.
    # Buoy 1 temperature, buoy 3 temperature, buoy 4 temperature
    #variables = [
    #    # "61788ec5dc917002aa2562e2", Has some bad data
    #    "616e4a88810cbd039c60af03",
    #    "616e476e41ac9d03d99b67ed"
    #]

    agg = ["mean", "min", "max"]
    for method in agg:
        file_path = f"{site_directory}/{datetime.now().year}-temperature-{method}.csv"
        with open(file_path, "w", newline="") as f:
            wtr = csv.writer(f)
            wtr.writerow(["date", datetime.now().year])
            resampled = ubidotsdata.Resample(
                variables=variables,
                aggregation=method,
                join_dataframes=True,
                period="M",
                start=1640995200000,  # 1st Jan 2022
                end=end,
            ).resample(token)

            for day in resampled.results:
                ts = day[0]
                if ts is None:
                    continue

                date = unix_to_local(int(ts)).strftime("%b")

                sum_ = 0.0
                n = 0.0
                for value in day[1:]:
                    if value is None:
                        continue
                    if 30.0 > value > 10.0:
                        sum_ += value
                        n += 1.0
                if sum_ != 0.0 and n != 0.0:
                    res = WaterTempRecord(date=date, water_temperature=sum_ / n)
                    wtr.writerow([res.date, res.water_temperature])
                else:
                    res = WaterTempRecord(date=date, water_temperature=None)
                    wtr.writerow([res.date, res.water_temperature])
                    print(f"Zero division error. Sum = {sum_}, n = {n}")


def year_to_date_precipitation_to_csv(site_directory, aws_token: str, variables: List[str]) -> None:
    print("Getting yearly precipitation from Ubidots.")

    file_path = f"{site_directory}/yearly-precipitation.csv"

    # variables represents aggregate total daily rainfall values.
    start, end = utils.this_year()
    raw_series = ubidotsaws.RawSeries(variables, start, end)

    precipitation = raw_series.get_precipitation(aws_token)

    with open(file_path, mode="w", newline="") as file:
        wtr = csv.writer(file)
        wtr.writerow(["date", datetime.now().year])
        sum = 0.0

        for d in reversed(precipitation.results[0]):
            value, ts = d[0], int(d[1])
            local_date = unix_to_local(ts).strftime("%-d/%-m/%y")
            rec = Record(date=local_date, precipitation=round(value+sum,2))
            sum += value
            wtr.writerow([rec.date, rec.precipitation])


def join_precipitation_datasets(site_directory) -> None:
    print("Joining precipitation datasets")

    files = [
        f"{site_directory}/yearly-precipitation.csv",
        f"{site_directory}/2020-precipitation.csv",
        f"{site_directory}/2021-precipitation.csv",
        f"{site_directory}/2022-precipitation.csv",
        f"{site_directory}/2023-precipitation.csv",
    ]

    df = pd.DataFrame()

    init = True
    for file in files:
        if not os.path.exists(file):
            continue
        else:
            tmp_df = pd.read_csv(file)
            if init:
                df = tmp_df.copy()
                init = False
            else:
                df = pd.merge(df, tmp_df, on="date", how="outer")

    df.to_csv(f"{site_directory}/combined-precipitation.csv", index=False)


def historical_temperature_datasets(site_directory) -> None:
    print("Joining historical temperature datasets")

    agg = ["mean", "min", "max"]

    for method in agg:
        files = [
            f"{site_directory}/{datetime.now().year}-temperature-{method}.csv",
            f"{site_directory}/historical-temperature-{method}.csv",
        ]

        df = pd.DataFrame()

        init = True
        for file in files:
            tmp_df = pd.read_csv(file)
            if init:
                df = tmp_df.copy()
                init = False
            else:
                df = pd.merge(df, tmp_df, on="date", how="outer")

        out_filename = f"{site_directory}/combined-historical-temperature-{method}.csv"
        df.to_csv(out_filename, index=False)


def join_flow_datasets(site_directory, files) -> None:
    print("Joining flow datasets")

    df = pd.DataFrame()

    init = True
    for file in files:
        tmp_df = pd.read_csv(f"{site_directory}/{file}")
        if init:
            df = tmp_df.copy()
            init = False
        else:
            df = pd.merge(df, tmp_df, on="Date", how="outer")

    df.to_csv(f"{site_directory}/combined-dischargerate.csv", index=False)


def ubidots_device_data_resample(
    variables: List[str],
    aggregation: str,
    join_dataframes: bool,
    period: str,
    start: int,
    end: int,
    token: str,
) -> dict:
    url = "https://industrial.api.ubidots.com/api/v1.6/devices/data/resample"
    headers = {"X-Auth-Token": token, "Content-Type": "application/json"}
    data = {
        "variables": variables,
        "aggregation": aggregation,
        "join_dataframes": join_dataframes,
        "period": period,
        "start": start,
        "end": end,
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def ubidots_device_aws_raw_series(variables: List[str], time_range: Tuple[int, int]) -> dict:
    url = "https://industrial.api.ubidots.com/api/v1.6/devices/aws/rawseries"
    headers = {"Content-Type": "application/json"}
    data = {"variables": variables, "time_range": time_range}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def unix_to_local(ts: int) -> datetime:
    return datetime.fromtimestamp(ts / 1000.0)
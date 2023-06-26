import csv
from datetime import datetime
import ubidots.device.aws as ubidotsaws
from typing import List
from dateutil import tz
from pytz import timezone
import util as utils

class Record:
    def __init__(self, date: str, precipitation: float):
        self.date = date
        self.precipitation = precipitation

def weekly_precipitation_to_csv(directory, aws_token: str, variables: List[str]):
    print("Getting weekly precipitation from Ubidots.")

    file_path = f"{directory}/weekly-precipitation.csv"

    # variables, array of variables that represent aggregate daily rainfall total.
    start, end = utils.one_week()
    raw_series = ubidotsaws.RawSeries(variables, start, end)

    precipitation = raw_series.get_precipitation(aws_token)

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Precipitation'])

        # Little bit hacky but Ubidots gives data in three nested lists which needs to be handled in
        # reverse
        for d in range(len(precipitation.results[0])-2, -1, -1):
            data = precipitation.results[0][d]
            value, ts = data[0], int(round(data[1]))
            local_date = utils.unix_to_local(ts).strftime('%m/%d/%Y')

            # When AWS reads less than 1mm this value is likely false, so show zero instead
            cleaned_value = value if value >= 1.0 else 0.0

            rec = Record(local_date, cleaned_value)

            writer.writerow([rec.date, rec.precipitation])

    print("Finished writing precipitation data to CSV.")
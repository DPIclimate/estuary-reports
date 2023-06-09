import csv
import logging
from datetime import timedelta
from typing import List
from ubidots.device.variables import VariablesList
from ubidots.device.data import Aggregation
import util as utils

logger = logging.getLogger(__name__)

class Table:
    def __init__(self):
        self.location = []
        self.daily_value = []
        self.harvest_area = []

    @staticmethod
    def aggregate(token, variable_list, week_start, offset, day_offset):
        daily_agg = Aggregation(
            variables=variable_list.ids.copy(),
            aggregation="mean",
            join_dataframes=False,
            start=week_start + (timedelta(milliseconds=offset).total_seconds() * 1000),
            end=week_start + (timedelta(milliseconds=day_offset).total_seconds() * 1000),
        )
        daily = daily_agg.aggregate(token)
        if daily is not None:
            return daily.results
        else:
            return []

    @staticmethod
    def serialize_csv(filename, data):
        with open(filename, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(data)

    def new(self, variable_list: VariablesList, token: str):
        weekly = Table()

        for cd, ha in zip(variable_list.corresponding_device, variable_list.harvest_area):
            weekly.location.append(cd)
            weekly.harvest_area.append(ha)

        week_start, _week_end = utils.one_week()

        offset = 0
        day_offset = 86400000

        for _ in range(7):
            daily_results = self.aggregate(token, variable_list, week_start, offset, day_offset)

            day_vec = []
            for day in daily_results:
                day_value = day['value'] if day['value'] is not None else 0.0
                day_vec.append(day_value)

            weekly.daily_value.append(day_vec)

            offset += 86400000
            day_offset += 86400000
        return weekly

    def to_csv(self, variable_name, filename):
        logger.info(f"Publishing weekly {variable_name} data to {filename}")

        with open(filename, "a", newline="") as file:
            writer = csv.writer(file)
            print(self.__dict__)
            for i, (loc, ha) in enumerate(zip(self.location, self.harvest_area)):
                day_transpose = []
                for day in self.daily_value:
                    if 0.0 < day[i] < 40.0:
                        day_transpose.append(str(day[i]))
                    else:
                        day_transpose.append("")
                day_transpose.append(loc)
                day_transpose.append(ha)
                writer.writerow(day_transpose)

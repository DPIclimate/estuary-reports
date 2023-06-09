import csv
from typing import List
from ubidots.device.variables import VariablesList
import ubidots.device.data as ubidotsdata
from datetime import datetime, timedelta
import util as utils
import logging
import numpy as np

logger = logging.getLogger(__name__)


class Chart:

    def __init__(self):
        self.data = {}

    class Row:
        def __init__(self, site):
            self.date: List[str] = []
            self.daily_avg: List[str] = []
            self.site = site

    class HarvestArea:
        def __init__(self, variables, name):
            self.variables = variables
            self.name = name

        def to_dict(self):
            return {
                "name": self.name,
                "variables": self.variables
            }


    class HarvestAreaVariables:
        def __init__(self):
            self.harvest_areas = []

        def as_array(self):
            return [ha for ha in self.harvest_areas]

    def new(self, variable_list, config, token: str) -> 'Chart':

        chart = Chart()

        harvest_area_variables = Chart.HarvestAreaVariables()

        # Get a unique list of all harvest areas
        harvest_area_names = np.unique([dev["harvest_area"] for dev in config["devices"]])

        # Create a harvest area object for each harvest area
        for harvest_area_name in harvest_area_names:
            harvest_area = Chart.HarvestArea(variables=[], name=harvest_area_name)
            for id, device, ha in variable_list:
                if ha == harvest_area_name:
                    harvest_area.variables.append(id)
            harvest_area_variables.harvest_areas.append(harvest_area)

        start, end = utils.two_weeks()

        for ha in harvest_area_variables.as_array():
            resampled = ubidotsdata.Resample(
                variables=ha.variables,
                aggregation="mean",
                join_dataframes=True,
                period="24H",
                start=start * 1000,
                end=end * 1000,
            ).resample(token)

            if resampled is None:
                logging.error(f"Error requesting resampled fortnightly chart values.")
                continue

            daily_avg = []
            
            for day in resampled.results:
                ts = round(day[0])/1000
                if ts is None:
                    continue
                if ts < 0 or ts > 9999999999:
                    logging.error(f"Invalid timestamp: {ts}")
                    continue
                try:
                    fmt_time = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
                except ValueError as e:
                    logging.error(f"Error formatting timestamp: {e}")
                    continue

                if fmt_time not in chart.data:
                    chart.data[fmt_time] = {}

                sum = 0.0
                n = 0.0
                for value in day[1:]:
                    if value is None:
                        continue
                    if 0.0 < value < 40.0:
                        sum += value
                        n += 1.0
                if n > 0:
                    chart.data[fmt_time][ha.name] = sum / n

        return chart

    def to_csv(self, filename: str):
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            for date, values in self.data.items():
                row = [date]
                for harvest_area, value in values.items():
                    row.append(str(value))
                writer.writerow(row)


    
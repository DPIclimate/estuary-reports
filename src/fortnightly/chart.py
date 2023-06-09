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
    rows = []

    def __init__(self):
        self.rows = []

    class Row:
        def __init__(self, site, min_val, max_val):
            self.date: List[str] = []
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

        site_names = [ha.name for ha in harvest_area_variables.harvest_areas]
        index = 0
        init = True

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
                if init:
                    ts = day[0]
                    if ts is None:
                        continue
                    fmt_time = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
                    #chart.date.append(fmt_time)

                sum = 0.0
                n = 0.0
                for value in day[1:]:
                    if value is None:
                        continue
                    if 0.0 < value < 40.0:
                        sum += value
                        n += 1.0
                daily_avg.append(sum / n)

            init = False

            #if site_names[index] == "Moonlight":
            #    chart.moonlight = daily_avg
            #elif site_names[index] == "Rocky Point":
            #    chart.rocky_point = daily_avg
            #elif site_names[index] == "Waterfall":
            #    chart.waterfall = daily_avg
            #else:
            #    logging.error("Unknown harvest area found. Append this harvest area before re-running.")

            index += 1

        return chart

    def to_csv(self, variable_name: str):
        filename = f"data/fortnightly-{variable_name}-chart.csv"

        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)

            for day in self.as_array():
                writer.writerow(day)

    def as_array(self) -> List[List[str]]:
        transposed = []
        for date, ml, rp, wf in zip(self.date, self.moonlight, self.rocky_point, self.waterfall):
            day = [date, str(ml), str(rp), str(wf)]
            transposed.append(day)

        return transposed
    
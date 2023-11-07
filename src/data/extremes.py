import logging
import csv
import numpy as np
import time
from datetime import datetime, timedelta
import ubidots.device.variables as ubidotsvariables
import ubidots.device.data as ubidotsdata
import pprint

class Extremes:
    rows = []

    def __init__(self):
        self.rows = []

    class Row:
        def __init__(self, site, min_val, max_val):
            self.site = site
            self.min = min_val
            self.max = max_val

    class HarvestAreaVariables:
        def __init__(self):
            self.harvest_areas = []

        def as_array(self):
            return [ha for ha in self.harvest_areas]
        
    class HarvestArea:
        def __init__(self, variables, name):
            self.variables = variables
            self.name = name

    def new(self, variable_list, config, token):
        harvest_area_variables = Extremes.HarvestAreaVariables()

        # Get a unique list of all harvest areas
        harvest_area_names = np.unique([dev["harvest_area"] for dev in config["devices"]])

        # Create a harvest area object for each harvest area
        for harvest_area_name in harvest_area_names:
            harvest_area = Extremes.HarvestArea(variables=[], name=harvest_area_name)
            for id, device, ha in variable_list:
                if ha == harvest_area_name:
                    harvest_area.variables.append(id)
            harvest_area_variables.harvest_areas.append(harvest_area)

        # Loop harvest_area_variables and print the name and variables
        for ha in harvest_area_variables.harvest_areas:
            pprint.pprint(f"{ha.name}: {ha.variables}")

        start, end = Extremes.get_time_range()

        start_ms = int(time.mktime(start.timetuple()) * 1000)
        end_ms = int(time.mktime(end.timetuple()) * 1000)

        site_names = [ha.name for ha in harvest_area_variables.harvest_areas]

        print(f"site_names: {site_names}")

        index = 0
        for ha in harvest_area_variables.as_array():
            weekly_min_agg = ubidotsdata.Aggregation(
                variables=ha.variables,
                aggregation="min",
                join_dataframes=False,
                start=start_ms,
                end=end_ms,
            )

            weekly_min = weekly_min_agg.aggregate(token)

            abs_min = 0.0
            init = True
            if weekly_min is not None and weekly_min.results is not None:
                min_value = min([min_val["value"] for min_val in weekly_min.results if min_val["value"] is not None])
            else:
                min_value = 0.0

            print(f"Min Value for {ha.name}: {min_value}")

            weekly_max_agg = ubidotsdata.Aggregation(
                variables=ha.variables,
                aggregation="max",
                join_dataframes=False,
                start=start_ms,
                end=end_ms,
            )

            weekly_max = weekly_max_agg.aggregate(token)

            abs_max = 0.0
            init = True

            if weekly_max is not None and weekly_max.results is not None:
                max_value = max([max_val["value"] for max_val in weekly_max.results if max_val["value"] is not None])
                if max_value > 100:
                    max_value = 0.0
            else:
                max_value = 0.0

            location = ""
            if ha.name != None:
                location = ha.name

            print(f"Max Value for {ha.name}: {max_value}")

            row = self.Row(location, min_value, max_value)

            self.rows.append(row)

            index += 1

    @staticmethod
    def get_time_range():
        end = datetime.now()
        start = end - timedelta(days=7)
        return start, end
    
    def to_csv(self, filename):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Site', 'Min Value', 'Max Value'])
            for row in self.rows:
                writer.writerow([row.site, row.min, row.max])


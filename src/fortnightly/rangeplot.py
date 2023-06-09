import csv
import logging
from datetime import timedelta, datetime
from typing import List
import ubidots.device.variables as ubidotsvariables
import ubidots.device.data as ubidotsdata
import util as utils
import time

logger = logging.getLogger(__name__)

class RangeValues:
    def __init__(self, location: str, last_week: float, this_week: float, harvest_area: str):
        self.location = location
        self.last_week = last_week
        self.this_week = this_week
        self.harvest_area = harvest_area

class RangePlot:
    def __init__(self, range_values: List[RangeValues]):
        self.range_values = range_values

    @classmethod
    def new(cls, variable_list: ubidotsvariables.VariablesList, token: str) -> 'RangePlot':
        # ---- Last Week ---- #
        start, end = utils.one_week()

        print(f"start: {start}, end: {end}")

        this_week_agg = ubidotsdata.Aggregation(
            variables=variable_list.ids.copy(),
            aggregation="mean",
            join_dataframes=False,
            start=start,
            end=end,
        )

        try:
            this_week = this_week_agg.aggregate(token)
        except Exception as e:
            logger.error(f"Error requesting weekly mean: {e}")
            this_week = None

        # ---- This Week ---- #
        start, end = utils.last_week()

        last_week_agg = ubidotsdata.Aggregation(
            variables=variable_list.ids.copy(),
            aggregation="mean",
            join_dataframes=False,
            start=start,
            end=end,
        )

        try:
            last_week = last_week_agg.aggregate(token)
        except Exception as e:
            logger.error(f"Error requesting weekly mean: {e}")
            last_week = None

        range_plot = RangePlot([])

        print(f"last_week: {last_week.__dict__}, this_week: {this_week.__dict__}")

        if last_week is not None and this_week is not None:
            for lw, (tw, (cd, ha)) in zip(last_week.results, zip(this_week.results, zip(variable_list.corresponding_device, variable_list.harvest_area))):
                lw_value = lw if lw is not None else 0.0
                tw_value = tw if tw is not None else 0.0

                values = RangeValues(
                    location=cd,
                    last_week=lw_value,
                    this_week=tw_value,
                    harvest_area=ha,
                )
                range_plot.range_values.append(values)

        return range_plot

    def to_csv(self, variable_name: str, filename: str):

        logger.info(f"Publishing weekly {variable_name} data {filename}")

        with open(filename, "a", newline="") as file:
            writer = csv.writer(file)
            for row in self.range_values:
                if 0.0 < row.this_week['value'] < 40.0 and 0.0 < row.last_week['value'] < 40.0:
                    writer.writerow([
                        row.location,
                        str(row.last_week['value']),
                        str(row.this_week['value']),
                        row.harvest_area,
                    ])
                else:
                    writer.writerow([
                        row.location,
                        "",
                        "",
                        row.harvest_area,
                    ])

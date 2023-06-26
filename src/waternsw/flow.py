from ubidots.device.variables import VariablesList
import ubidots.device.data as ubidotsdata
from datetime import datetime, timedelta
import util as utils
import logging
import json
import csv
import requests
from typing import List
from datetime import datetime
import pprint

logger = logging.basicConfig(level=logging.INFO)

class Request:
    def __init__(self, params, function, version):
        self.params = params
        self.function = function
        self.version = version

    def to_dict(self):
        return {
            "params": self.params,
            "function": self.function,
            "version": self.version
        }

class Params:
    def __init__(self, site_list, start_time, varfrom, interval, varto, datasource, end_time, data_type, multiplier):
        self.site_list = site_list
        self.start_time = start_time
        self.varfrom = varfrom
        self.interval = interval
        self.varto = varto
        self.datasource = datasource
        self.end_time = end_time
        self.data_type = data_type
        self.multiplier = multiplier

    def to_dict(self):
        return {
            "site_list": self.site_list,
            "start_time": self.start_time,
            "varfrom": self.varfrom,
            "interval": self.interval,
            "varto": self.varto,
            "datasource": self.datasource,
            "end_time": self.end_time,
            "data_type": self.data_type,
            "multiplier": self.multiplier
        }

class DischargeRate:
    def __init__(self, error_num, return_field):
        self.error_num = error_num
        self.return_field = return_field

    @classmethod
    def new(cls, start, end, config) -> List['DischargeRate']:

        print(f"Requesting WaterNSW Data for {len(config['sites'])} sites for the period {int(datetime.fromtimestamp(start).strftime('%Y%m%d%H%M%S'))} to {int(datetime.fromtimestamp(end).strftime('%Y%m%d%H%M%S'))}")

        discharge_rate_vec = []

        for site in config['sites']:
            params = Params(
                site_list=site['id'],
                start_time=int(datetime.fromtimestamp(start).strftime('%Y%m%d%H%M%S')),
                varfrom=config['defaults']['params']['varfrom'],
                interval=config['defaults']['params']['interval'],
                varto=config['defaults']['params']['varto'],
                datasource=config['defaults']['params']['datasource'],
                end_time=int(datetime.fromtimestamp(end).strftime('%Y%m%d%H%M%S')),
                data_type=config['defaults']['params']['data_type'],
                multiplier=config['defaults']['params']['multiplier']
            )

            request = Request(
                params=params.to_dict(),
                function=config['defaults']['function'],
                version=config['defaults']['version']
            )

            req_str = json.dumps(request.to_dict())

            url = f"https://realtimedata.waternsw.com.au/cgi/webservice.exe?{req_str}"

            # Required by WaterNSW for some reason
            USER_AGENT = f"estuary_reports/v1.0"

            headers = {
                "User-Agent": USER_AGENT
            }

            res = requests.get(url, headers=headers).json()

            discharge_rate_vec.append(cls(error_num=res['error_num'], return_field=res['return']))

        return discharge_rate_vec

    def to_csv(self, time_range: str, filename: str):
        logging.info(f"Publishing discharge rate data to {filename}")

        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            if time_range == "fortnightly":
                writer.writerow(['Date', 'Volume', 'Quality'])
            elif time_range == "yearly":
                writer.writerow(['Date', f'{datetime.now().year}', 'Quality'])

            sum = 0.0
            monthly_sum = 0.0
            last_month = None
            for trace in self.return_field['traces'][0]['trace']:
                date_str = str(trace['t']) # e.g. 20220302000000
                date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
                date_str = date.strftime('%Y/%m/%d')

                flow = None
                if time_range == "fortnightly":
                    flow = float(trace['v'])
                    writer.writerow([date_str, round(flow,2), trace['q']])
                elif time_range == "yearly":
                    flow = float(trace['v'])
                    writer.writerow([date_str, round(flow,2), trace['q']])

    @classmethod
    def generate(cls, time_range: str, site_directory, config):
        logging.info("Generating discharge rate datasets")

        start, end = None, None
        if time_range == "fortnightly":
            start, end = utils.two_weeks()
        elif time_range == "yearly":
            start, end = utils.this_year()
        else:
            raise ValueError("Unknown time range specified. Append this range before re-running")

        print(f"Time Strings: {int(datetime.fromtimestamp(start/1000).strftime('%Y%m%d%H%M%S'))}, {int(datetime.fromtimestamp(end/1000).strftime('%Y%m%d%H%M%S'))}")

        try:
            discharge_rates = cls.new(start/1000, end/1000, config)
            for site in discharge_rates:
                filename = f"{site_directory}/{time_range}-{site.return_field['traces'][0]['site']}.csv"
                for s in config["sites"]:
                    if str(s["id"]) == site.return_field['traces'][0]['site']:
                        filename = f"{site_directory}/{time_range}-{s['name']}.csv"
                site.to_csv(time_range, filename)
        except Exception as e:
            logging.error(f"There was an error: {e}")
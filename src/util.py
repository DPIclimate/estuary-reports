import datetime
from typing import List, Tuple
import json

def get_config(filename: str = "config.json"):
    try:
        with open(filename) as f:
            return json.load(f)
    except FileNotFoundError:
        print("config.json not found. Please create one with the required format:")
    except json.decoder.JSONDecodeError:
        print("config.json is not valid JSON. Please check the file and try again.")

def unix_to_local(unix_time: int) -> datetime.datetime:
    datetime_ts = datetime.datetime.fromtimestamp(unix_time / 1000, datetime.timezone.utc)
    return datetime_ts.astimezone(datetime.timezone(datetime.timedelta(hours=10)))

def next_10_days() -> Tuple[int, int]:
    today = datetime.date.today()
    start = datetime.datetime.combine(today - datetime.timedelta(days=1), datetime.time.min, datetime.timezone.utc)
    end = start + datetime.timedelta(days=10)
    return (int(start.timestamp()) * 1000, int(end.timestamp()) * 1000)

def this_year(millis: bool) -> Tuple[int, int]:
    utc_time_now = datetime.datetime.now(datetime.timezone.utc)
    ts_now = int(utc_time_now.timestamp())
    local_time_now = utc_time_now.astimezone(datetime.timezone(datetime.timedelta(hours=10)))
    start_of_year = datetime.datetime(local_time_now.year, 1, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=10)))
    start_of_year_ts = int(start_of_year.timestamp())
    if not millis:
        return (start_of_year_ts, ts_now)
    return (start_of_year_ts * 1000, ts_now * 1000)

def one_week() -> Tuple[int, int]:
    time_now = datetime.datetime.now(datetime.timezone.utc)
    local_time_now = time_now.astimezone(datetime.timezone(datetime.timedelta(hours=10)))
    midnight_today = datetime.datetime.combine(local_time_now.date(), datetime.time.min, datetime.timezone(datetime.timedelta(hours=10)))
    last_week = midnight_today - datetime.timedelta(days=7)
    return (int(last_week.timestamp()) * 1000, int(time_now.timestamp()) * 1000)

def two_weeks() -> Tuple[int, int]:
    time_now = datetime.datetime.now(datetime.timezone.utc)
    local_time_now = time_now.astimezone(datetime.timezone(datetime.timedelta(hours=10)))
    midnight_today = datetime.datetime.combine(local_time_now.date(), datetime.time.min, datetime.timezone(datetime.timedelta(hours=10)))
    last_two_weeks = midnight_today - datetime.timedelta(days=14)
    return (int(last_two_weeks.timestamp()), int(time_now.timestamp()))

def last_week() -> Tuple[int, int]:
    last_week_end = int(datetime.datetime.now(datetime.timezone.utc).timestamp()) * 1000 - 604800000
    last_week_start = last_week_end - 604800000
    return (last_week_start, last_week_end)

def weekly_column_names() -> List[str]:
    last_week, _now = one_week()
    unix_time = last_week
    col_names = []
    for _ in range(7):
        local_day = unix_to_local(unix_time).strftime("%A")
        col_names.append(local_day)
        unix_time += 86400000
    return col_names

def unix_range_to_timestring(unix_range: Tuple[int, int]) -> Tuple[str, str]:
    start_unix = datetime.datetime.fromtimestamp(unix_range[0] / 1000, datetime.timezone.utc)
    start_local = start_unix.astimezone(datetime.timezone(datetime.timedelta(hours=10))).strftime("%Y%m%d%H%M%S")
    end_unix = datetime.datetime.fromtimestamp(unix_range[1] / 1000, datetime.timezone.utc)
    end_local = end_unix.astimezone(datetime.timezone(datetime.timedelta(hours=10))).strftime("%Y%m%d%H%M%S")
    return (start_local, end_local)


class Config:
    """
    Configuration from `config.json`.
    """
    def __init__(self, directory: str, name: str, devices: List[dict], variables: List[str], harvest_areas: str, files: List[dict], water_nsw: dict):
        self.directory = directory
        self.name = name
        self.devices = [Device(**device) for device in devices]
        self.variables = variables
        self.harvest_areas = harvest_areas
        self.files = [FileConfig(**file) for file in files]
        self.water_nsw = WaterNsw(**water_nsw)

    @classmethod
    def from_file(cls, file_path: str) -> 'Config':
        """
        Reads from `config.json` and returns a `Config` object.
        """
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
    
    @classmethod
    def from_site(cls, site) -> 'Config':
        config_dict = site
        return cls(**config_dict)

class Device:
    """
    Device information from `config.json`.
    """
    def __init__(self, name: str, location: str, harvest_area: str, buoy_number: str):
        self.name = name
        self.location = location
        self.harvest_area = harvest_area
        self.buoy_number = buoy_number

class FileConfig:
    """
    File configuration from `config.json`.
    """
    def __init__(self, filepath: str, name: str, chart_id: str, dynamic: bool, columns: List[str]):
        self.output_dir = filepath
        self.output_name = name
        self.chart_id = chart_id
        self.dynamic_headers = dynamic
        self.columns = columns

class WaterNsw:
    """
    Water NSW configuration from `config.json`.
    """
    def __init__(self, sites: List[dict], defaults: dict):
        self.sites = [WaterNswSite(**site) for site in sites]
        self.defaults = WaterNswDefaults(**defaults)

class WaterNswSite:
    """
    Water NSW site information from `config.json`.
    """
    def __init__(self, name: str, id: str):
        self.name = name
        self.id = id

class WaterNswDefaults:
    """
    Water NSW default configuration from `config.json`.
    """
    def __init__(self, params: List[str], function: str, version: str):
        self.parameters = params
        self.function = function
        self.version = version

class WaterNswParams:
    """
    Water NSW parameters from `config.json`.
    """
    def __init__(self, variable_range: List[int], interval: int, data_source: str, data_type: str, multiplier: int):
        self.variable_range = variable_range
        self.interval = interval
        self.data_source = data_source
        self.data_type = data_type
        self.multiplier = multiplier
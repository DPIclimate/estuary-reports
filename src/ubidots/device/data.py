import logging
import requests
import json
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class Aggregation:
    def __init__(self, variables: List[str], aggregation: str, join_dataframes: bool, start: int, end: Optional[int] = None):
        self.variables = variables
        self.aggregation = aggregation
        self.join_dataframes = join_dataframes
        self.start = start
        self.end = end

    def aggregate(self, token: str) -> Optional['Response']:
        logger.info(f"Getting {self.aggregation} aggregate data from ubidots.")
        url = "https://industrial.api.ubidots.com.au/api/v1.6/data/stats/aggregation/"
        headers = {
            "X-Auth-Token": token,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(self.__dict__))
            response.raise_for_status()
            json_res = response.json()
            return Response(**json_res)
        except Exception as e:
            logger.error(f"Error requesting aggregate data: {e}")
            return None

class Response:
    def __init__(self, results: List['Value']):
        self.results = results

class Value:
    def __init__(self, value: Optional[float], timestamp: int):
        self.value = value
        self.timestamp = timestamp

class Resample:
    def __init__(self, variables: List[str], aggregation: str, join_dataframes: bool, period: str, start: int, end: int):
        self.variables = variables
        self.aggregation = aggregation
        self.join_dataframes = join_dataframes
        self.period = period
        self.start = start
        self.end = end

    def resample(self, token: str) -> Optional['ResampleResult']:
        logger.info("Getting resampled data from ubidots.")
        url = "https://industrial.api.ubidots.com.au/api/v1.6/data/stats/resample/"
        headers = {
            "X-Auth-Token": token,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(self.__dict__))
            response.raise_for_status()
            json_res = response.json()
            print(f"\nJSON RESPONSE: {json_res}\n")
            return ResampleResult(**json_res)
        except Exception as e:
            logger.error(f"Error requesting resampled data: {e}")
            return None

class ResampleResult:
    def __init__(self, results: List[List[Optional[float]]], columns: List[str]):
        self.results = results
        self.columns = columns

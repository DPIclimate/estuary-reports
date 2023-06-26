import requests
from typing import List
from datetime import datetime
import util as utils

class Precipitation:
    def __init__(self, results: List[List[List[float]]], columns: List[List[str]]):
        self.results = results
        self.columns = columns

class RawSeries:
    def __init__(self, variables: List[str], start: int, end: int = None):
        self.variables = variables
        self.columns = ["value.value", "timestamp"]
        self.join_dataframes = False
        self.start = start
        self.end = end if end is not None else int(datetime.now().timestamp())

    def get_precipitation(self, aws_token: str) -> Precipitation:
        url = "https://industrial.api.ubidots.com.au/api/v1.6/data/raw/series"

        headers = {
            "X-Auth-Token": aws_token,
            "Content-Type": "application/json"
        }

        data = {
            "variables": self.variables,
            "columns": self.columns,
            "join_dataframes": self.join_dataframes,
            "start": self.start,
            "end": self.end
        }

        print(f"Getting data from: {self.start} and {self.end}")

        response = requests.post(url, headers=headers, json=data)

        if response.status_code != 200:
            raise Exception(f"Error getting precipitation data: {response.text}")

        return Precipitation(response.json()["results"], response.json()["columns"])
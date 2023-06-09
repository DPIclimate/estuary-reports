import logging
import requests
from typing import List

logging.basicConfig(level=logging.INFO)

class Device:
    def __init__(self, url: str, id: str, label: str, name: str, last_activity: int):
        self.url = url
        self.id = id
        self.label = label
        self.name = name
        self.last_activity = last_activity

class Devices:
    def __init__(self, count: int, results: List[Device]):
        self.count = count
        self.results = results

async def get_all_devices(token: str) -> Devices:
    logging.info("Getting device list from Ubidots")

    url = "https://industrial.api.ubidots.com.au/api/v2.0/devices/"

    client = requests.Session()
    client.headers.update({"X-Auth-Token": token})
    response = client.get(url).json()

    return Devices(response["count"], [Device(**device) for device in response["results"]])
import json
import logging
import os
from typing import List
import requests
from requests.exceptions import RequestException


class Variables:
    def __init__(self, count: int, results: List):
        self.count = count
        self.results = results


class Variable:
    def __init__(self, id: str, name: str, last_activity: int):
        self.id = id
        self.name = name
        self.last_activity = last_activity


class VariablesList:
    def __init__(self, name: str):
        self.name = name
        self.ids = []
        self.corresponding_device = []
        self.harvest_area = []

    def __iter__(self):
        return iter(zip(self.ids, self.corresponding_device, self.harvest_area))
    
    @classmethod
    def new(cls, variable: str, config: dict, token: str):
        variable_list = VariablesList(variable)
        logging.info("Getting refined variable list from config.json")

        all_devices = get_all_devices(token)
        #print(f"all_devices: {all_devices}")
        for device in all_devices["results"]:
            print(device)
            if any(dev["name"] == device["name"] for dev in config["devices"]):
                print(f"Device Name: {device['name']}")
                all_variables = list_variables(device["id"], token)
                for var in all_variables["results"]:
                    if var["name"] == variable:
                        location = "unknown"
                        harvest_area = "unknown"
                        for dev in config["devices"]:
                            if dev["name"] == device["name"]:
                                location = dev["location"]
                                harvest_area = dev["harvest_area"]
                                break
                        variable_list.add_variable_and_device(
                            var["id"], location, harvest_area
                        )
                        break
        return variable_list

    @classmethod
    def new_from_cache(cls, directory, variable: str):
        filename = f"{directory}/{variable}-variable-list.json"
        with open(filename) as f:
            data = json.load(f)
        variable_list = cls(data["name"])
        variable_list.ids = data["ids"]
        variable_list.corresponding_device = data["corresponding_device"]
        variable_list.harvest_area = data["harvest_area"]
        return variable_list


    def add_variable_and_device(self, variable_id: str, device_name: str, harvest_area: str):
        self.ids.append(variable_id)
        self.corresponding_device.append(device_name)
        self.harvest_area.append(harvest_area)


    def cache(self, directory, variable: str):
        filename = f"cache/{directory}/{variable}-variable-list.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            json.dump(self.__dict__, f, indent=4)


def list_variables(device_id: str, token: str) -> dict:
    """List all variables for a device."""
    logging.info("Getting variables list from Ubidots.")
    url = f"https://industrial.api.ubidots.com.au/api/v2.0/devices/{device_id}/variables/"
    headers = {"X-Auth-Token": token}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error getting variables for device {device_id}: {e}")
        raise


def get_all_devices(token: str) -> dict:
    """Get all devices from Ubidots."""
    url = "https://industrial.api.ubidots.com.au/api/v2.0/devices/"
    headers = {"X-Auth-Token": token}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logging.error(f"Error getting devices list: {e}")
        raise

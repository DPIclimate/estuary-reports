import requests
import os
from typing import List
import logging

logging.basicConfig(level=logging.INFO)

def upload_dataset(file_path: str, chart_id: str, dw_key: str) -> None:
    logging.info(f"Exporting {file_path} to datawrapper.de...")

    # Read in the file as a raw string
    with open(file_path, 'r') as file:
        body = file.read()

    url = f"https://api.datawrapper.de/v3/charts/{chart_id}/data"

    headers = {
        "Authorization": f"Bearer {dw_key}",
        "Content-Type": "text/csv"
    }

    response = requests.put(url, headers=headers, data=body)

    response.raise_for_status()

def publish_chart(chart_id: str, dw_key: str) -> None:
    logging.info(f"Publishing chart at https://datawrapper.dwcdn.net/{chart_id}/")

    url = f"https://api.datawrapper.de/v3/charts/{chart_id}/publish"

    headers = {
        "Authorization": f"Bearer {dw_key}"
    }

    response = requests.post(url, headers=headers)

    response.raise_for_status()

def all_files_to_datawrapper(site_directory, config, dw_key) -> None:
    # ---- Write csv's to datawrapper ---- //
    for file in config['files']:
        filepath = f"{site_directory}/{file['filepath']}"
        chart_id = file['chart_id']
        try:
            upload_dataset(filepath, chart_id, dw_key)
            publish_chart(chart_id, dw_key)
        except Exception as e:
            logging.error(f"Error uploading/publishing data: {e}")
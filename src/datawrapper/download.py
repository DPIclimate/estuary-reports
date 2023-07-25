import requests
import os, time
from typing import List
import logging

logging.basicConfig(level=logging.INFO)

def download_image(output_filename: str, chart_id: str, dw_key: str) -> None:

    url = f"https://api.datawrapper.de/v3/charts/{chart_id}/export/png?unit=px&width=800&mode=rgb&plain=false&borderWidth=10"

    headers = {
        "Authorization": f"Bearer {dw_key}",
        "accept": "*/*"
    }

    for i in range(2):
        try:
            logging.info(f"Downloading image from datawrapper.de (Attempt: {i+1}) to {output_filename}")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            with open(output_filename, 'wb') as f:
                f.write(response.content)
            logging.info(f"Downloaded image from datawrapper.de to {output_filename}")
            return
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading image from datawrapper.de: {e}")
            if i == 0:
                logging.info(f"Retrying image download for {output_filename}")
                time.sleep(5)
                continue
            else:
                return
import requests
import os
from typing import List
import logging

logging.basicConfig(level=logging.INFO)

def download_image(output_filename: str, chart_id: str, dw_key: str) -> None:
    logging.info(f"Downloading image from datawrapper.de to {output_filename}")

    url = f"https://api.datawrapper.de/v3/charts/{chart_id}/export/png?unit=px&width=800&mode=rgb&plain=false&borderWidth=10"

    headers = {
        "Authorization": f"Bearer {dw_key}",
        "accept": "*/*"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        response = None
        logging.error(f"Error downloading image from datawrapper.de: {e}")
    if response is not None:
        with open(output_filename, 'wb') as f:
            f.write(response.content)
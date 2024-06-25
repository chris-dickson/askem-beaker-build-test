import logging
import os
from io import BytesIO
from json import JSONDecodeError

import requests
import xarray

logger = logging.getLogger(__name__)

# Get the HMI_SERVER endpoint from the environment variable
hmi_server = os.getenv("HMI_SERVER_URL")

# Define the id
id = "{{id}}"

# Prepare the request URL
url = f"{hmi_server}/datasets/{id}/download-file?filename={{filename}}"

# Make the HTTP GET request to retrieve the dataset
response = requests.get(url, auth={{auth}}, stream=True)

# Check the response status code
if response.status_code <= 300:
    message = f"Dataset retrieved successfully with status code {response.status_code}."
    logger.info(response.content)
else:
    message = f"Dataset retrieval failed with status code {response.status_code}."
    if response.text:
        message += f" Response message: {response.text}"
    logger.error(message)


{{variable_name}} = xarray.open_dataset(BytesIO(response.content))

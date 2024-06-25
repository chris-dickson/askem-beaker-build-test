import os
import requests

from json import JSONDecodeError

# Binary data bytes
file_bytes = {{data}}  # Replace with your binary data

if not isinstance(file_bytes, bytes):
    file_bytes = file_bytes.to_netcdf()

# Get the HMI_SERVER endpoint and auth token from the environment variable
hmi_server = os.getenv('HMI_SERVER_URL')

# Define the id and filename dynamically
id = "{{id}}"
filename = "{{filename}}"

# Prepare the request payload
payload = {'id': id, 'filename': filename}
files = {'file': file_bytes}

# Set the headers with the content type
# headers = {}

# Make the HTTP PUT request to upload the file bytes
url = f'{hmi_server}/datasets/{id}/upload-file'
response = requests.put(url, data=payload, files=files, auth={{auth}})

# Check the response status code
if response.status_code < 300:
    try:
        message = response.json()
    except JSONDecodeError:
        message = f'File uploaded successfully with status code {response.status_code}.'
else:
    message = f'File upload failed with status code {response.status_code}.'
    if response.text:
        message += f' Response message: {response.text}'

message

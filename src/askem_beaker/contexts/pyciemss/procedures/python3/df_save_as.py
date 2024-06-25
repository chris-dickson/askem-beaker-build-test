import requests

# Saving as a temporary file instead of a buffer to save memory
with open("./result.csv") as csv_file:
    upload_response = requests.put('{{data_url}}', data=csv_file)
if upload_response.status_code != 200:
    raise Exception(f"Error uploading dataframe: {upload_response.content}")

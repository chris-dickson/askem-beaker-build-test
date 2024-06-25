import requests
import tempfile

# Saving as a temporary file instead of a buffer to save memory
with tempfile.TemporaryFile() as temp_csv_file:
    {{ var_name|default("df") }}.to_csv(temp_csv_file, index=False, header=True)
    temp_csv_file.seek(0)
    upload_response = requests.put('{{data_url}}', data=temp_csv_file)
if upload_response.status_code != 200:
    raise Exception(f"Error uploading dataframe: {upload_response.content}")

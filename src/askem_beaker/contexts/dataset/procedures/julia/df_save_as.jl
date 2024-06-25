using Dates

_temp_csv_file = tempname()
CSV.write(_temp_csv_file, {{ var_name|default("df") }}, writeheader=true)
_filesize = stat(_temp_csv_file).size
_upload_response = HTTP.put("{{data_url}}", ["content-length" => _filesize], open(_temp_csv_file, "r"))

if _upload_response.status != 200
    error("Error uploading dataframe: $(String(_upload_response.body))")
end

# Cleanup
rm(_temp_csv_file)

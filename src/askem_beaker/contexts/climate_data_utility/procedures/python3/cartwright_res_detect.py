from cartwright.analysis.space_resolution import detect_latlon_resolution
from elwood import elwood
import pandas
import xarray


def open_dataset(filepath):
    filetype = filepath.split(".")[-1]

    dataframe = None

    if filetype == "nc" or filetype == "nc4" or filetype == "netcdf":
        dataframe = elwood.netcdf2df(filepath)
    elif filetype == "csv":
        dataframe = pandas.read_csv(filepath)
    elif filetype == "xlsx" or filetype == "xls":
        dataframe = pandas.read_excel(filepath)

    if dataframe is None:
        raise AssertionError("The dataframe could not be created.")

    return dataframe


dataframe = open_dataset(f"{{filepath}}")
geo_columns = {{geo_columns}}

if dataframe is None:
    raise AssertionError("The dataframe could not be created.")

# get the lat/lon coordinates from the dataframe
lat = dataframe[geo_columns["lat_column"]].to_numpy()
lon = dataframe[geo_columns["lon_column"]].to_numpy()

# detect the spatial resolution
resolution = detect_latlon_resolution(lat, lon)

# parse resolution response into a string

result_string = f"The spatial resolution of the dataset is {resolution.square.uniformity} with a resoltuion of {resolution.square.resolution} {resolution.square.unit}. The resolution error is {resolution.square.error}."

result_string

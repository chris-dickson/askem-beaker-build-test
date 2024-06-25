import numpy as np
import xarray as xr
from flowcast.regrid import regrid_1d, RegridType
import io


def load_dataset(dataset) -> xr.Dataset:
    """
    Load the dataset from the given filepath.

    Args:
        dataset (bytes or xarray.Dataset): The dataset to regrid.

    Returns:
        xr.Dataset: The loaded dataset.
    """
    if isinstance(dataset, bytes):
        # Load the dataset using xarray
        dataset = xr.open_dataset(dataset)

    return dataset


def regrid_dataset(dataset, target_resolution: tuple):
    """
    Regrid the dataset at the given filepath to the given target resolution.

    Args:
        dataset (bytes or xarray.Dataset): The dataset to regrid.
        target_resolution (tuple): The target resolution to regrid to, e.g. (0.5, 0.5).
    """
    # Load the dataset
    dataset = load_dataset(dataset)

    # Calculate the spacing between consecutive latitude and longitude values
    lat_spacing = dataset.lat.values[1] - dataset.lat.values[0]
    lon_spacing = dataset.lon.values[1] - dataset.lon.values[0]

    original_resolution = (lon_spacing, lat_spacing)

    # Check if regridding is necessary
    if original_resolution == target_resolution or "lat" not in dataset.dims or "lon" not in dataset.dims:
        # Skip regridding
        return dataset

    # Raw geo coordinates at target resolution
    lats = np.arange(-90, 90, target_resolution[1])
    lons = np.arange(-180, 180, target_resolution[0])

    # Crop geo coordinates around the dataset's maximum extents
    min_lat = dataset.lat.data.min()
    max_lat = dataset.lat.data.max()
    min_lon = dataset.lon.data.min()
    max_lon = dataset.lon.data.max()
    
    if min_lon >= 0.0:
        lons = np.arange(0, 360, target_resolution[0])

    lats = lats[(lats + target_resolution[1] / 2 >= min_lat) & (lats - target_resolution[1] / 2 <= max_lat)]
    lons = lons[(lons + target_resolution[0] / 2 >= min_lon) & (lons - target_resolution[0] / 2 <= max_lon)]

    # Get all data variables minus bounds
    data_nobounds = [v for v in dataset.variables if not str(v).endswith("_bnds") and v not in dataset.dims]

    # Regrid each feature individually along lat/lon
    def regrid_2d_latlon(ds, feature, ag):
        regridded = regrid_1d(ds[feature], lats, "lat", aggregation=ag, low_memory=True)
        regridded = regrid_1d(regridded, lons, "lon", aggregation=ag, low_memory=True)
        return regridded

    method = RegridType.{{aggregation}}
    regridded_dataset = xr.Dataset({
        feature: regrid_2d_latlon(dataset, feature, method) for feature in data_nobounds
    })

    # Persist attributes after regridding.
    # Copy attributes from source variables
    for var_name, var in dataset.variables.items():
        if var_name in regridded_dataset.variables:
            regridded_dataset[var_name].attrs.update(var.attrs)

    # Copy attributes from source coordinates
    for coord_name, coord in dataset.coords.items():
        if coord_name in regridded_dataset.coords:
            regridded_dataset[coord_name].attrs.update(coord.attrs)

    return regridded_dataset


regrid_dataset({{dataset}}, {{target_resolution}})

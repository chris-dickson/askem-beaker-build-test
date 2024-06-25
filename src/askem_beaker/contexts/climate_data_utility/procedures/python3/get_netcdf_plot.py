import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap

plot_variable_name = {{plot_variable_name}}
lat_col = "{{lat_col}}"
lon_col = "{{lon_col}}"
time_slice_index = {{time_slice_index}}

ds = {{dataset}}

# cmip6 datasets contain a main variable id for meaning
if plot_variable_name is None:
    plot_variable_name = ds.attrs.get("variable_id", None)

if plot_variable_name is None:
    plot_variable_name = list(ds.data_vars)[0]

# Show the first variable by default.
variable_to_visualize = ds[plot_variable_name]

# Choose a specific time index (e.g., 0 for the first time step)
time_index = time_slice_index
variable_at_time = variable_to_visualize.isel(time=time_index)

lons = variable_at_time[lon_col][:]
lats = variable_at_time[lat_col][:]
units = variable_at_time.units

name = variable_at_time.long_name


# Get some parameters for the Stereographic Projection
lon_0 = lons.mean()
lat_0 = lats.mean()

m = Basemap(width=5000000, height=3500000, resolution='l', projection='stere', lat_ts=40, lat_0=lat_0, lon_0=lon_0)

# Because our lon and lat variables are 1D,
# use meshgrid to create 2D arrays
# Not necessary if coordinates are already in 2D arrays.
lon, lat = np.meshgrid(lons, lats)
xi, yi = m(lon, lat)


# Plot Data
cs = m.pcolor(xi, yi, np.squeeze(variable_at_time))

# Add Grid Lines
m.drawparallels(np.arange(-80.0, 81.0, 10.0), labels=[1, 0, 0, 0], fontsize=10)
m.drawmeridians(np.arange(-180.0, 181.0, 10.0), labels=[0, 0, 0, 1], fontsize=10)

# Add Coastlines, States, and Country Boundaries
m.drawcoastlines()
m.drawstates()
m.drawcountries()

# Add Colorbar
cbar = m.colorbar(cs, location='bottom', pad="10%")
cbar.set_label(units)

# Add Title
plt.title(name)

plt.show()

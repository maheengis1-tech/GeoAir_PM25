"""
data_loader.py
Handles locating and reading the correct SATPM (V6GL03 CNN PM2.5) .nc file
for a given year and month, and preparing it as a CRS-aware DataArray.

Filename pattern on disk (confirmed from actual files):
    V6GL03.CNNPM25.AS.{YYYYMM}-{YYYYMM}.nc
e.g. V6GL03.CNNPM25.AS.201801-201801.nc

Some systems (browsers/OneDrive) rewrite dots as underscores when a file is
uploaded/downloaded, so this loader accepts either separator automatically.

Confirmed NetCDF structure:
    Variable : PM25            (units: ug/m3)
    Dims     : lat (7000), lon (8000)
    lat range: -9.995 .. 59.995   (ascending)
    lon range: 65.005 .. 144.995  (ascending)
    CRS      : geographic, WGS84 (EPSG:4326) - not embedded in file, must set manually
"""

import os
import glob
import xarray as xr

VARIABLE_NAME = "PM25"
CRS = "EPSG:4326"


def find_nc_file(data_dir: str, year: int, month: int) -> str:
    """
    Look inside data_dir/<year>/ for a file matching the SATPM naming
    pattern for the given year/month, regardless of '.' or '_' separators.

    Raises FileNotFoundError with a clear message if nothing matches.
    """
    ym = f"{year}{month:02d}"
    year_dir = os.path.join(data_dir, str(year))

    if not os.path.isdir(year_dir):
        raise FileNotFoundError(f"No data folder found for year {year}: {year_dir}")

    # Match both dot- and underscore-separated naming
    patterns = [
        os.path.join(year_dir, f"V6GL03.CNNPM25.AS.{ym}-{ym}.nc"),
        os.path.join(year_dir, f"V6GL03_CNNPM25_AS_{ym}-{ym}.nc"),
        os.path.join(year_dir, f"*{ym}-{ym}*.nc"),  # fallback, loose match
    ]

    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]

    raise FileNotFoundError(
        f"No .nc file found for {year}-{month:02d} in {year_dir}. "
        f"Expected something like V6GL03.CNNPM25.AS.{ym}-{ym}.nc"
    )


def load_pm25(nc_path: str) -> xr.DataArray:
    """
    Open the .nc file, pull out the PM25 variable, and attach spatial
    metadata (dimension names + CRS) so rioxarray can clip/export it later.
    """
    ds = xr.open_dataset(nc_path)

    if VARIABLE_NAME not in ds.data_vars:
        raise KeyError(
            f"Expected variable '{VARIABLE_NAME}' not found in {nc_path}. "
            f"Available variables: {list(ds.data_vars)}"
        )

    da = ds[VARIABLE_NAME]

    # rioxarray needs to know which dims are x/y
    da = da.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=False)
    da = da.rio.write_crs(CRS, inplace=False)

    return da

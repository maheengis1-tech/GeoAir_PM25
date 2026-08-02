"""
export_utils.py
Handles all four download formats: CSV, GeoTIFF, ASCII Grid, PNG.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr


def export_csv(stats: dict, out_path: str):
    """Writes the summary statistics dict to a single-row CSV."""
    df = pd.DataFrame([stats])
    df.to_csv(out_path, index=False)
    return out_path


def export_geotiff(clipped: xr.DataArray, out_path: str):
    """Writes the clipped raster to GeoTIFF using rioxarray."""
    clipped.rio.to_raster(out_path)
    return out_path


def export_ascii_grid(clipped: xr.DataArray, out_path: str):
    """
    Writes the clipped raster to an Esri ASCII Grid (.asc) file.
    rioxarray/rasterio support 'AAIGrid' as a GDAL driver name directly.
    """
    clipped.rio.to_raster(out_path, driver="AAIGrid")
    return out_path


def export_png_map(clipped: xr.DataArray, out_path: str, title: str = "PM2.5 (ug/m3)"):
    """
    Renders the clipped raster as a map image with a professional color scale
    and saves it as PNG.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    im = clipped.plot.imshow(
        ax=ax,
        cmap="YlOrRd",          # professional AQI-style scale (light -> dark = worse)
        add_colorbar=True,
        cbar_kwargs={"label": "PM2.5 (ug/m3)"},
    )
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path

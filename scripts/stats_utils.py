"""
stats_utils.py
Computes summary statistics and PM2.5 category breakdown for a clipped raster.
"""

import numpy as np
import xarray as xr

# US EPA-style PM2.5 breakpoints (ug/m3) - adjust if your project needs WHO bands instead
PM25_CATEGORIES = [
    ("Good",                0,    12.0),
    ("Moderate",            12.1, 35.4),
    ("Unhealthy (Sensitive)",35.5, 55.4),
    ("Unhealthy",           55.5, 150.4),
    ("Very Unhealthy",      150.5, 250.4),
    ("Hazardous",           250.5, np.inf),
]


def compute_summary_stats(clipped: xr.DataArray) -> dict:
    """
    Returns mean, max, min, std over valid (non-NaN) pixels in the clipped array.
    """
    values = clipped.values
    valid = values[~np.isnan(values)]

    if valid.size == 0:
        raise ValueError("No valid PM2.5 pixels found inside the AOI - check that the "
                          "shapefile overlaps the data extent (lat -10..60, lon 65..145).")

    return {
        "mean": float(np.mean(valid)),
        "max": float(np.max(valid)),
        "min": float(np.min(valid)),
        "std": float(np.std(valid)),
        "valid_pixel_count": int(valid.size),
    }


def categorize_pixels(clipped: xr.DataArray) -> dict:
    """
    Buckets valid pixels into PM2.5 categories and returns pixel counts per category.
    """
    values = clipped.values
    valid = values[~np.isnan(values)]

    counts = {}
    for label, low, high in PM25_CATEGORIES:
        counts[label] = int(np.sum((valid >= low) & (valid < high)))

    return counts


def monthly_trend(data_dir: str, year: int, up_to_month: int, gdf) -> list:
    """
    Computes mean PM2.5 within the AOI for Jan through up_to_month of the given year,
    for the trend chart. Skips months whose .nc file isn't available.
    """
    from scripts.data_loader import find_nc_file, load_pm25
    from scripts.clip_utils import clip_to_aoi

    trend = []
    for m in range(1, up_to_month + 1):
        try:
            nc_path = find_nc_file(data_dir, year, m)
            da = load_pm25(nc_path)
            clipped = clip_to_aoi(da, gdf)
            stats = compute_summary_stats(clipped)
            trend.append({"month": m, "mean": stats["mean"]})
        except (FileNotFoundError, ValueError):
            trend.append({"month": m, "mean": None})

    return trend

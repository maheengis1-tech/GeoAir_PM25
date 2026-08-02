"""
clip_utils.py
Clips a PM25 DataArray to an AOI polygon uploaded by the user as a shapefile (.zip).
"""

import os
import zipfile
import tempfile
import geopandas as gpd
import xarray as xr


def extract_shapefile_zip(zip_path: str, extract_to: str) -> str:
    """
    Unzips an uploaded shapefile .zip and returns the path to the .shp file.
    """
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_to)

    # Search recursively - Windows "Compress to zip" often nests files inside
    # a subfolder rather than putting them at the top level.
    shp_path = None
    for root, _dirs, files in os.walk(extract_to):
        for f in files:
            if f.lower().endswith(".shp"):
                shp_path = os.path.join(root, f)
                break
        if shp_path:
            break

    if not shp_path:
        raise FileNotFoundError(
            "No .shp file found inside the uploaded zip. Make sure the zip "
            "contains .shp, .shx, .dbf (and ideally .prj) files - either "
            "directly at the top level or inside one subfolder."
        )

    return shp_path


def load_aoi(shp_path: str) -> gpd.GeoDataFrame:
    """
    Reads the AOI shapefile and reprojects it to EPSG:4326 to match the raster.
    """
    gdf = gpd.read_file(shp_path)
    if gdf.crs is None:
        raise ValueError("Uploaded shapefile has no CRS defined - cannot reproject safely.")
    gdf = gdf.to_crs("EPSG:4326")
    return gdf


def clip_to_aoi(da: xr.DataArray, gdf: gpd.GeoDataFrame) -> xr.DataArray:
    """
    Clips the PM25 raster to the AOI geometry. Pixels outside the AOI become NaN.
    """
    clipped = da.rio.clip(gdf.geometry.values, gdf.crs, drop=True, invert=False)
    return clipped


def aoi_area_km2(gdf: gpd.GeoDataFrame) -> float:
    """
    Computes AOI area in km2 by reprojecting to an equal-area CRS (World Mollweide)
    before measuring, since EPSG:4326 degrees aren't suitable for area calculations.
    """
    gdf_eq = gdf.to_crs("ESRI:54009")  # World Mollweide (equal-area)
    area_m2 = gdf_eq.geometry.area.sum()
    return area_m2 / 1_000_000
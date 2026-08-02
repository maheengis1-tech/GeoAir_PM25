# GeoAir PM₂.₅ Explorer

Interactive Satellite-Based Air Quality Analysis Tool built on the SATPM
(V6GL03 CNN PM2.5, ACAG/WashU) monthly dataset.

## Confirmed data format

- **Variable name:** `PM25` (units: ug/m3)
- **Dims:** `lat` (7000), `lon` (8000) — 0.01° resolution
- **Extent:** lat -9.995 to 59.995, lon 65.005 to 144.995 (Asia region)
- **CRS:** not embedded in the file — treated as EPSG:4326 (WGS84)
- **Filename pattern:** `V6GL03.CNNPM25.AS.{YYYYMM}-{YYYYMM}.nc`
  (loader also accepts underscores instead of dots, since some upload/download
  tools rewrite `.` to `_`)

## Setup

```bash
cd GeoAir_PM25
pip install -r requirements.txt
```

Place your monthly `.nc` files inside `data/<year>/`, e.g.:

```
data/2018/V6GL03.CNNPM25.AS.201801-201801.nc
data/2018/V6GL03.CNNPM25.AS.201802-201802.nc
```

## Run

```bash
streamlit run app.py
```

## Workflow

1. Upload an AOI shapefile as a `.zip` (must contain `.shp`, `.shx`, `.dbf`,
   and ideally `.prj`)
2. Select year and month from the sidebar
3. Click **Generate Analysis**
4. Dashboard automatically:
   - Locates and reads the matching `.nc` file
   - Reprojects the AOI to match the raster (EPSG:4326)
   - Clips PM2.5 to the AOI
   - Computes mean / max / min / std, and PM2.5 category pixel counts
   - Renders the map and monthly trend chart
5. Download results as CSV, GeoTIFF, ASCII Grid, or PNG

## Project structure

```
GeoAir_PM25/
├── data/<year>/*.nc     # source SATPM files, organized by year
├── uploads/              # temp storage for uploaded AOI shapefiles (per session)
├── outputs/               # generated CSV / GeoTIFF / ASCII / PNG files
├── scripts/
│   ├── data_loader.py    # finds + reads the right .nc file
│   ├── clip_utils.py     # shapefile handling + AOI clip
│   ├── stats_utils.py    # summary stats, categories, monthly trend
│   └── export_utils.py   # CSV / GeoTIFF / ASCII / PNG export
├── app.py                 # Streamlit dashboard
└── requirements.txt
```

## Notes / things to double check before presenting this as a portfolio piece

- **PM2.5 category breakpoints** in `stats_utils.py` currently use US EPA
  bands. If your target audience expects WHO guideline bands instead, swap
  the `PM25_CATEGORIES` list.
- **AOI area** is computed via reprojection to World Mollweide (equal-area).
  This is accurate for most AOI sizes but always sanity-check against a known
  area for your test AOI.
- **Monthly trend** currently reruns the full clip+stats pipeline for every
  month from Jan up to the selected month — fine for demo-sized AOIs, but for
  very large AOIs or a full year of data this will be slow. Worth caching
  results by (year, month, AOI hash) if you scale this up.
- Tested end-to-end with your uploaded January 2018 file and a sample AOI —
  clipping, stats, and all four export formats confirmed working.

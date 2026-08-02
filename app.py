"""
app.py
GeoAir PM2.5 Explorer - Interactive Satellite-Based Air Quality Analysis Tool

Run with:
    streamlit run app.py
"""

import os
import uuid
import streamlit as st
import matplotlib.pyplot as plt

from scripts.data_loader import find_nc_file, load_pm25
from scripts.clip_utils import extract_shapefile_zip, load_aoi, clip_to_aoi, aoi_area_km2
from scripts.stats_utils import compute_summary_stats, categorize_pixels, monthly_trend
from scripts.export_utils import export_csv, export_geotiff, export_ascii_grid, export_png_map

DATA_DIR = "data"
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(page_title="GeoAir PM2.5 Explorer", layout="wide")
st.title("🛰 GeoAir PM₂.₅ Explorer")
st.caption("Interactive Satellite-Based Air Quality Analysis Tool")

# ---------------- SIDEBAR ----------------
st.sidebar.header("Controls")

uploaded_zip = st.sidebar.file_uploader("Upload Shapefile (.zip)", type=["zip"])

available_years = sorted(
    [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
) if os.path.isdir(DATA_DIR) else []

year = st.sidebar.selectbox("Year", available_years if available_years else ["2024"])
month = st.sidebar.selectbox("Month", list(range(1, 13)), format_func=lambda m: f"{m:02d}")

generate = st.sidebar.button("Generate Analysis", type="primary", use_container_width=True)

# ---------------- MAIN LOGIC ----------------
if generate:
    if uploaded_zip is None:
        st.warning("Please upload an AOI shapefile (.zip) first.")
        st.stop()

    session_id = str(uuid.uuid4())[:8]
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    zip_path = os.path.join(session_dir, "aoi.zip")
    with open(zip_path, "wb") as f:
        f.write(uploaded_zip.getbuffer())

    try:
        with st.spinner("Reading shapefile and NetCDF data..."):
            shp_path = extract_shapefile_zip(zip_path, session_dir)
            gdf = load_aoi(shp_path)

            nc_path = find_nc_file(DATA_DIR, int(year), int(month))
            da = load_pm25(nc_path)

            clipped = clip_to_aoi(da, gdf)
            stats = compute_summary_stats(clipped)
            categories = categorize_pixels(clipped)
            area_km2 = aoi_area_km2(gdf)

        # ---------------- SUMMARY CARD ----------------
        st.subheader("📋 AOI Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Area", f"{area_km2:,.0f} km²")
        c2.metric("Mean PM₂.₅", f"{stats['mean']:.1f} µg/m³")
        c3.metric("Highest Pixel", f"{stats['max']:.1f}")
        c4.metric("Lowest Pixel", f"{stats['min']:.1f}")

        st.divider()

        col_map, col_stats = st.columns([2, 1])

        # ---------------- MAP ----------------
        with col_map:
            st.subheader("🗺 PM₂.₅ Map")
            fig, ax = plt.subplots(figsize=(7, 6))
            clipped.plot.imshow(ax=ax, cmap="YlOrRd", cbar_kwargs={"label": "µg/m³"})
            ax.set_title(f"PM2.5 - {year}-{int(month):02d}")
            st.pyplot(fig)

        # ---------------- STATS ----------------
        with col_stats:
            st.subheader("📊 Statistics")
            st.write(f"**Mean:** {stats['mean']:.2f} µg/m³")
            st.write(f"**Maximum:** {stats['max']:.2f} µg/m³")
            st.write(f"**Minimum:** {stats['min']:.2f} µg/m³")
            st.write(f"**Std Dev:** {stats['std']:.2f} µg/m³")
            st.write(f"**Valid pixels:** {stats['valid_pixel_count']:,}")

            st.subheader("🔥 PM₂.₅ Categories")
            st.bar_chart(categories)

        # ---------------- MONTHLY TREND ----------------
        st.subheader("📈 Monthly Trend")
        with st.spinner("Computing trend across available months..."):
            trend = monthly_trend(DATA_DIR, int(year), int(month), gdf)
        trend_months = [t["month"] for t in trend if t["mean"] is not None]
        trend_values = [t["mean"] for t in trend if t["mean"] is not None]
        if trend_values:
            st.line_chart({"PM2.5 mean (µg/m³)": trend_values}, x_label="Month")
        else:
            st.info("Not enough monthly data available yet to plot a trend.")

        # ---------------- DOWNLOADS ----------------
        st.subheader("📥 Downloads")
        out_prefix = os.path.join(OUTPUT_DIR, f"{session_id}_{year}_{month:02d}")

        csv_path = export_csv(stats, out_prefix + ".csv")
        tif_path = export_geotiff(clipped, out_prefix + ".tif")
        asc_path = export_ascii_grid(clipped, out_prefix + ".asc")
        png_path = export_png_map(clipped, out_prefix + ".png",
                                   title=f"PM2.5 - {year}-{int(month):02d}")

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            with open(csv_path, "rb") as f:
                st.download_button("⬇ CSV", f, file_name=os.path.basename(csv_path))
        with d2:
            with open(tif_path, "rb") as f:
                st.download_button("⬇ GeoTIFF", f, file_name=os.path.basename(tif_path))
        with d3:
            with open(asc_path, "rb") as f:
                st.download_button("⬇ ASCII Grid", f, file_name=os.path.basename(asc_path))
        with d4:
            with open(png_path, "rb") as f:
                st.download_button("⬇ PNG", f, file_name=os.path.basename(png_path))

    except FileNotFoundError as e:
        st.error(f"File not found: {e}")
    except KeyError as e:
        st.error(f"Data structure error: {e}")
    except ValueError as e:
        st.error(f"{e}")

else:
    st.info("Upload an AOI shapefile and click **Generate Analysis** to begin.")




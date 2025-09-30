import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from branca.colormap import linear
from datetime import timedelta
import os

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="HAB Monitoring - South Australia", layout="wide")
st.title("🌊 Harmful Algal Bloom Monitoring - South Australia")

# ---------------------------
# Load data
# ---------------------------
@st.cache_data
def load_data(file_path="HarmfulAlgalBloom_MonitoringSites.csv", coords_csv="site_coordinates.csv"):
    if not os.path.exists(file_path):
        st.error(f"Data file '{file_path}' not found.")
        st.stop()
    if not os.path.exists(coords_csv):
        st.error(f"Coordinates file '{coords_csv}' not found.")
        st.stop()

    df = pd.read_csv(file_path, parse_dates=["Date_Sample_Collected"])
    coords_df = pd.read_csv(coords_csv)
    df = df.merge(coords_df, on="Site_Description", how="left")
    return df

df = load_data()

# ---------------------------
# Sidebar filters
# ---------------------------
with st.sidebar:
    st.header("🔎 Filters")

    # Species filter
    all_species = sorted(df['Result_Name'].dropna().unique())
    default_species = [s for s in all_species if "Karenia" in s] or all_species[:1]
    species_selected = st.multiselect(
        "Select species",
        options=all_species,
        default=default_species
    )

    # Date filter
    min_date, max_date = df['Date_Sample_Collected'].min(), df['Date_Sample_Collected'].max()
    last_week_start = max_date - timedelta(days=7)
    date_range = st.date_input(
        "Date range",
        [last_week_start, max_date],
        min_value=min_date,
        max_value=max_date
    )
    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = min_date, max_date

# ---------------------------
# Apply filters
# ---------------------------
mask = (
    df['Result_Name'].isin(species_selected) &
    df['Date_Sample_Collected'].between(start_date, end_date) &
    df['Result_Value_Numeric'].notna()
)
filtered = df.loc[mask]

st.sidebar.write(f"Showing **{len(filtered)} of {len(df)} records**")

# ---------------------------
# Map
# ---------------------------
if not filtered.empty:
    # Base map centered on South Australia
    m = folium.Map(location=[-34.9, 138.6], zoom_start=6, tiles=None, control_scale=True)

    # Hybrid basemap: Esri Satellite + OpenStreetMap labels
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Esri Satellite", overlay=False
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="OpenStreetMap", name="Labels", overlay=True
    ).add_to(m)
    folium.LayerControl().add_to(m)

    # Color scale (legend) for cell count
    colormap = linear.YlOrRd_09.scale(
        filtered['Result_Value_Numeric'].min(),
        filtered['Result_Value_Numeric'].max()
    )
    colormap.caption = "Cell count (cells/L)"
    colormap.add_to(m)
    colormap.position = "bottomleft"

    # Add sample points
    for _, row in filtered.iterrows():
        if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
            color = colormap(row['Result_Value_Numeric'])
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=(
                    f"<b>Site:</b> {row['Site_Description']}<br>"
                    f"<b>Species:</b> {row['Result_Name']}<br>"
                    f"<b>Date:</b> {row['Date_Sample_Collected'].date()}<br>"
                    f"<b>Cell count:</b> {row['Result_Value_Numeric']:,} {row.get('Units','')}"
                )
            ).add_to(m)

    # Display map
    st.markdown('<div style="border:2px solid #ccc; border-radius:8px; padding:4px;">', unsafe_allow_html=True)
    st_folium(m, width=1150, height=700)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("No data matches the selected filters.")

# ---------------------------
# Disclaimer
# ---------------------------
st.markdown("""
<div style="font-size:11px; color:#666; margin-top:10px;">
<strong>Disclaimer:</strong> This is a research product using publicly available South Australian Government data.
No liability is assumed by the author or the University of Adelaide. Users should obtain independent advice.
</div>
""", unsafe_allow_html=True)



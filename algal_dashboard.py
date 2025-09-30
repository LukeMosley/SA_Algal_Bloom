import streamlit as st
import folium
from streamlit_folium import st_folium
from branca.element import Element
from branca.colormap import LinearColormap
import pandas as pd
import os
from datetime import timedelta

# ---------------------------
# Load data + coordinates
# ---------------------------
@st.cache_data
def load_data(file_path, coords_csv="site_coordinates.csv"):
    df = pd.read_excel(file_path, sheet_name=0)
    df['Date_Sample_Collected'] = pd.to_datetime(df['Date_Sample_Collected'])

    if not os.path.exists(coords_csv):
        st.error(f"⚠️ Coordinates file '{coords_csv}' not found. "
                 f"Please generate site_coordinates.csv first.")
        st.stop()

    coords_df = pd.read_csv(coords_csv)
    return df.merge(coords_df, on="Site_Description", how="left")


# ---------------------------
# Build Streamlit app
# ---------------------------
def main():
    st.set_page_config(page_title="HAB Monitoring - South Australia", layout="wide")

    # ---------------------------
    # Custom styles
    # ---------------------------
    st.markdown("""
        <style>
        /* Remove top padding and footer */
        .block-container {padding-top: 0.25rem; padding-bottom: 0.25rem;}
        header, footer {visibility: hidden;}

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            font-size: 12px;
            padding: 0.25rem 0.5rem 0.5rem 0.5rem;
            width: 360px !important;
        }
        section[data-testid="stSidebar"] .stMarkdown p {
            margin-bottom: 0.2rem;
        }
        .sidebar-card {
            border: 1px solid #d0d0d0;
            border-radius: 8px;
            padding: 6px;
            margin-top: 0.2rem;
            background: #fff;
        }

        /* Map container styling */
        .map-container {
            border: 2px solid #ccc;
            border-radius: 8px;
            padding: 4px;
            margin: 0 auto;
        }
        .leaflet-control-zoom {z-index: 10000 !important;}
        </style>
        """, unsafe_allow_html=True
    )

    st.markdown(
        '<div style="font-size:14px; margin:0 0 6px 0;"><b>Interactive viewer for algal monitoring data in South Australia</b></div>',
        unsafe_allow_html=True
    )

    # ---------------------------
    # File paths and data
    # ---------------------------
    file_path = "HarmfulAlgalBloom_MonitoringSites_-1125610967936090616.xlsx"
    coords_csv = "site_coordinates.csv"
    df = load_data(file_path, coords_csv)

    # ---------------------------
    # Sidebar filters (always visible)
    # ---------------------------
    with st.sidebar:
        st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
        st.markdown("**Filters**")

        all_species = sorted(df['Result_Name'].dropna().unique())
        default_species = [s for s in all_species if "Karenia" in s] or all_species[:1]
        species_selected = st.multiselect(
            "Select species", options=all_species, default=default_species
        )

        min_date, max_date = df['Date_Sample_Collected'].min(), df['Date_Sample_Collected'].max()
        last_week_start = max_date - timedelta(days=7)
        date_range = st.date_input(
            "Date range", [last_week_start, max_date],
            min_value=min_date, max_value=max_date
        )
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        else:
            start_date, end_date = min_date, max_date

        st.markdown('</div>', unsafe_allow_html=True)

    # Filter dataset
    mask = (
        df['Result_Name'].isin(_]()


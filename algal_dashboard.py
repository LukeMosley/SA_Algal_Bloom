import pandas as pd
import folium
from branca.colormap import LinearColormap
from streamlit_folium import st_folium
import streamlit as st
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

    # Custom styles
    st.markdown(
        """
        <style>
        .block-container {padding-top: 0.25rem; padding-bottom: 0.25rem;}
        header, footer {visibility: hidden;}
        section[data-testid="st"] {font-size: 12px; padding: 0.25rem 0.5rem 0.5rem 0.5rem; width: 360px !important;}
        section[data-testid="st"] .stMarkdown p {margin-bottom: 0.2rem;}
        .-card {border: 1px solid #d0d0d0; border-radius: 8px; padding: 6px; margin-top: 0.2rem; background: #fff;}
        div[data-baseweb="select"] .css-1uccc91-singleValue,
        div[data-baseweb="select"] span {font-size: 11px !important; line-height: 1.1 !important;}
        div[data-baseweb="select"] .css-1m4v56a {font-size: 11px !important; padding: 4px 6px !important;}
        div[data-baseweb="select"] .css-1rhbuit-multiValue {margin: 2px 0 !important;}
        .map-container {border: 2px solid #ccc; border-radius: 8px; padding: 4px; margin: 0 auto;}
        .leaflet-control-zoom {z-index: 10000 !important; transform: scale(1) !important;}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "<h4><b>Interactive viewer of harmful algal bloom monitoring data in South Australia</b></h4>",
        unsafe_allow_html=True
    )

    # File paths
    file_path = "HarmfulAlgalBloom_MonitoringSites_-1125610967936090616.xlsx"
    coords_csv = "site_coordinates.csv"
    
    # Load dataset
    df = load_data(file_path, coords_csv)

    # ---------------------------
    # Sidebar toggle
    # ---------------------------
    sidebar_expanded = st.sidebar.checkbox("Show Filters", value=True)

    if sidebar_expanded:
        with st.sidebar:
            st.markdown('<div class="-card">', unsafe_allow_html=True)
            st.markdown("**Filters**")

            all_species = sorted(df['Result_Name'].dropna().unique())
            default_species = [s for s in all_species if "Karenia" in s] or all_species[:1]
            species_selected = st.multiselect(
                "Select species", 
                options=all_species, 
                default=default_species
            )

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

            st.markdown('</div>', unsafe_allow_html=True)
    else:
        all_species = sorted(df['Result_Name'].dropna().unique())
        default_species = [s for s in all_species if "Karenia" in s] or all_species[:1]
        species_selected = default_species
        min_date, max_date = df['Date_Sample_Collected'].min(), df['Date_Sample_Collected'].max()
        start_date, end_date = max_date - timedelta(days=7), max_date

    # ---------------------------
    # Filter dataset
    # ---------------------------
    mask = (
        df['Result_Name'].isin(species_selected) &
        df['Date_Sample_Collected'].between(start_date, end_date) &
        df['Result_Value_Numeric'].notna()
    )
    sub_df = df[mask]

    st.write(f"{len(sub_df)} of {len(df)} records shown")

    # ---------------------------
    # Map
    # ---------------------------
    m = folium.Map(location=[-34.9, 138.6], zoom_start=6, tiles="Esri.WorldImagery", control_scale=True)

    # Add color scale (bottom-left)
    colormap = LinearColormap(
        colors=['green', 'yellow', 'red'],
        vmin=1, vmax=500000,
        caption="Cell count (cells/L)"
    )
    colormap.add_to(m)
    colormap.position = 'bottomleft'

    # Add markers
    for _, row in sub_df.iterrows():
        if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
            value = row['Result_Value_Numeric']
            color = colormap(value if pd.notna(value) else 1)
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=(
                    f"<b>{row['Site_Description']}</b><br>"
                    f"{row['Date_Sample_Collected'].date()}<br>"
                    f"{row['Result_Name']}<br>"
                    f"{value:,} {row.get('Units','')}"
                )
            ).add_to(m)

    # Responsive map height
    map_height = max(400, min(1000, st.session_state.get("map_height", 600)))
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st_folium(m, width=1200, height=map_height)
    st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown(
        """
        <div style="font-size:11px; color:#666; margin-top:10px;">
        <strong>Disclaimer</strong> – this is a research product that utilises publicly available 
        South Australian Government data 
        (<a href="https://experience.arcgis.com/experience/5f0d6b22301a47bf91d198cabb030670" target="_blank">source</a>). 
        No liability is assumed by the author (A/Prof. Luke Mosley) or the University of Adelaide 
        for the use of this system or the data, which may be in error and/or out of date. 
        Users should obtain their own independent advice.
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

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
    # Detect file extension and read accordingly
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path, sheet_name=0)
    else:
        df = pd.read_csv(file_path)
    df['Date_Sample_Collected'] = pd.to_datetime(df['Date_Sample_Collected'])
    
    if not os.path.exists(coords_csv):
        st.error(f"⚠️ Coordinates file '{coords_csv}' not found. Please generate site_coordinates.csv first.")
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
        padding: 0.5rem 0.75rem 0.75rem 0.75rem;
        width: 360px !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p {margin-bottom: 0.3rem;}
    .sidebar-card {
        border: 1px solid #d0d0d0;
        border-radius: 8px;
        padding: 6px;
        margin-top: 0.2rem;
        background: #fff;
    }

    /* Multiselect token styling */
    div[data-baseweb="select"] .css-1uccc91-singleValue,
    div[data-baseweb="select"] span {font-size: 11px !important; line-height: 1.1 !important;}
    div[data-baseweb="select"] .css-1m4v56a {font-size: 11px !important; padding: 4px 6px !important;}
    div[data-baseweb="select"] .css-1rhbuit-multiValue {margin: 2px 0 !important;}

    /* Map container styling */
    .map-container {
        border: 2px solid #ccc;
        border-radius: 8px;
        padding: 4px;
        margin: 0 auto;
        width: 100%;
        max-width: none;
    }

    /* Move zoom buttons to top-right */
    .leaflet-control-zoom {
        position: absolute !important;
        top: 10px !important;
        right: 10px !important;
        left: auto !important;
        z-index: 10000 !important;
    }

    /* Force legend vertical, top-left */
    .folium-map .branca-colormap,
    .leaflet-container .branca-colormap {
        position: absolute !important;
        top: 10px !important;
        left: 10px !important;
        right: auto !important;
        bottom: auto !important;
        width: 35px !important;
        height: 180px !important;
        font-size: 10px !important;
        background: rgba(255,255,255,0.95);
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 4px;
        z-index: 10000 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .branca-colormap .caption {
        font-size: 9px !important;
        text-align: center;
        margin-top: 2px;
        color: #333 !important;  /* Dark text for caption */
    }
    /* Improve tick text readability: white text with black outline */
    .branca-colormap text {
        fill: white !important;
        stroke: black !important;
        stroke-width: 0.5 !important;
        text-anchor: middle !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:18px; margin:0 0 6px 0;"><b>Interactive viewer for algal monitoring data in South Australia</b></div>',
                unsafe_allow_html=True)

    # ---------------------------
    # File paths and data
    # ---------------------------
    file_path = "HarmfulAlgalBloom_MonitoringSites_-1125610967936090616.csv"  # Update to .csv if that's your new filename
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
        species_selected = st.multiselect("Select species", options=all_species, default=default_species)

        # Handle empty selection gracefully
        if not species_selected:
            species_selected = all_species[:1]  # Default to first if none selected

        min_date, max_date = df['Date_Sample_Collected'].min(), df['Date_Sample_Collected'].max()
        last_week_start = max_date - timedelta(days=7)
        date_range = st.date_input("Date range (yyyy/mm/dd)", [last_week_start, max_date], min_value=min_date, max_value=max_date)
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        else:
            start_date, end_date = min_date, max_date

        st.markdown('</div>', unsafe_allow_html=True)

    # Filter dataset
    mask = (
        df['Result_Name'].isin(species_selected) &
        df['Date_Sample_Collected'].between(start_date, end_date) &
        df['Result_Value_Numeric'].notna()
    )
    sub_df = df[mask]

    st.sidebar.write(f"{len(sub_df)} of {len(df)} records shown")

    # ---------------------------
    # Map with hybrid style
    # ---------------------------
    m = folium.Map(location=[-34.9, 138.6], zoom_start=6, control_scale=True)

    # Satellite + label layers
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr='Esri', name='Esri Satellite', overlay=False, control=True
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr='Esri', name='Labels', overlay=True, control=True
    ).add_to(m)
    folium.LayerControl().add_to(m)

    # Color scale (vertical)
    colormap = LinearColormap(colors=['green', 'yellow', 'red'], vmin=0, vmax=500000)
    colormap.caption = "Cell Count per L"
    colormap.add_to(m)

    # Add markers
    for _, row in sub_df.iterrows():
        if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
            value = row['Result_Value_Numeric']
            color = colormap(value if pd.notna(value) else 1)
            units = row.get('Units', 'cells/L')  # Default to cells/L for consistency
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=6, color=color, fill=True, fill_color=color, fill_opacity=0.8,
                popup=(f"<b>{row['Site_Description']}</b><br>"
                       f"{row['Date_Sample_Collected'].date()}<br>"
                       f"{row['Result_Name']}<br>"
                       f"{value:,} {units}")
            ).add_to(m)

    # Fit map to data extent (if records exist)
    if not sub_df.empty:
        m.fit_bounds([[sub_df['Latitude'].min(), sub_df['Longitude'].min()],
                      [sub_df['Latitude'].max(), sub_df['Longitude'].max()]])

    # Display map
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st_folium(m, width='100%', height=650)
    st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown("""
    <div style="font-size:11px; color:#666; margin-top:10px;">
    <strong>Disclaimer</strong> – this is a research product that utilises publicly available 
    South Australian Government data 
    (<a href="https://experience.arcgis.com/experience/5f0d6b22301a47bf91d198cabb030670" target="_blank">source</a>). 
    No liability is assumed by the author (A/Prof. Luke Mosley) or the University of Adelaide 
    for the use of this system or the data, which may be in error and/or out of date. 
    Users should obtain their own independent advice.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

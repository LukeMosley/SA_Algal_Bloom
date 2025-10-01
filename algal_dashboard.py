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
    # Check if main data file exists (warn but continue if missing)
    if not os.path.exists(file_path):
        st.warning(f"⚠️ Main data file '{file_path}' not found. Using empty dataset.")
        df = pd.DataFrame()  # Empty DF to proceed
    else:
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

    /* Horizontal colorbar - 1/2 width, above map */
    .colorbar-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 10px;
    }
    .colorbar-container {
        background: linear-gradient(to right, green 0%, yellow 50%, red 100%);
        height: 35px;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 0 5px;
        font-size: 12px;  /* Bigger labels */
        font-weight: bold;
        color: #333;
        max-width: 50%;  /* Half map width */
        width: 100%;  /* Responsive within max */
    }
    .colorbar-labels {
        display: flex;
        justify-content: space-between;
        width: 100%;
        font-size: 11px;
        color: #333;
        margin-top: 2px;
    }
    .colorbar-labels span {
        flex: 1;
        text-align: center;
    }
    .colorbar-units {
        font-size: 10px;
        color: #666;
        margin-left: 10px;
        white-space: nowrap;
    }

    /* Move zoom buttons to top-right */
    .leaflet-control-zoom {
        position: absolute !important;
        top: 10px !important;
        right: 10px !important;
        left: auto !important;
        z-index: 10000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:18px; margin:0 0 6px 0;"><b>Interactive viewer for algal monitoring data in South Australia</b></div>',
                unsafe_allow_html=True)

    # ---------------------------
    # File paths and data
    # ---------------------------
    file_path = "HarmfulAlgalBloom_MonitoringSites_8382667239581124066.csv"
    coords_csv = "site_coordinates.csv"
    #df = load_data(file_path, coords_csv)

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

    # Color scale (used for colors only, not added to map)
    colormap = LinearColormap(colors=['green', 'yellow', 'red'], vmin=0, vmax=500000)

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

    # Display custom horizontal colorbar (1/2 width)
    st.markdown("""
    <div class="colorbar-wrapper">
        <div class="colorbar-container">
            <div class="colorbar-labels">
                <span>0</span>
                <span>100k</span>
                <span>200k</span>
                <span>300k</span>
                <span>400k</span>
                <span>500k</span>
            </div>
        </div>
        <div class="colorbar-units">Cell count per L</div>
    </div>
    """, unsafe_allow_html=True)

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
    Users should consult the official SA Government information (https://www.algalbloom.sa.gov.au/) and/or obtain their own independent advice.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

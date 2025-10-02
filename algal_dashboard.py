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
    if not os.path.exists(file_path):
        st.warning(f"⚠️ Main data file '{file_path}' not found. Using empty dataset.")
        df = pd.DataFrame()
    else:
        if file_path.endswith(('.xlsx', '.xls')):
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
    st.set_page_config(
        page_title="HAB Monitoring - South Australia",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ---------------------------
    # Custom CSS
    # ---------------------------
st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 0.25rem;}
footer {visibility: hidden;}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    font-size: 11px;
    padding: 0.4rem 0.5rem 0.5rem 0.5rem;
    max-width: 350px;
}
section[data-testid="stSidebar"] .stMarkdown p {margin-bottom: 0.25rem;}
.sidebar-card {
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    padding: 6px;
    background: #fff;
    margin-bottom: 0.5rem;
}

/* Horizontal colorbar */
.colorbar-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 2px;
}
.colorbar-container {
    background: linear-gradient(to right, green 0%, yellow 50%, red 100%);
    height: 30px;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 0 5px;
    font-size: 12px;
    font-weight: bold;
    max-width: 95%;
    width: 100%;
}
.colorbar-labels {
    display: flex;
    justify-content: space-between;
    width: 100%;
    font-size: 11px;
    margin-top: 2px;
}
.colorbar-labels span {flex: 1; text-align: center;}
.colorbar-units {
    font-size: 12px;
    color: #000;
    margin-top: 2px;
    text-align: center;
    white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)

    # ---------------------------
    # File paths and data
    # ---------------------------
file_path = "HarmfulAlgalBloom_MonitoringSites_8382667239581124066.csv"
coords_csv = "site_coordinates.csv"
df = load_data(file_path, coords_csv)

 # ---------------------------
    # Sidebar: Title, colorbar, filters
    # ---------------------------
with st.sidebar:
    # Title
    st.markdown(
        '<div style="font-size:18px; font-weight:bold; text-align:center; margin-bottom:0.5rem;">'
        'Harmful Algal Bloom Dashboard – South Australia</div>',
        unsafe_allow_html=True
    )

    # Colorbar
    st.markdown(
        """
        <div class="colorbar-wrapper">
            <div class="colorbar-container">
                <div class="colorbar-labels">
                    <span>0</span><span>100,000</span><span>200,000</span>
                    <span>300,000</span><span>400,000</span><span>>500,000</span>
                </div>
            </div>
        </div>
        <div class="colorbar-units">Cell count per L</div>
        """,
        unsafe_allow_html=True
    )

    # Filters card
    st.markdown('<div class="sidebar-card">Filters</div>', unsafe_allow_html=True)

    # Species filter
    all_species = sorted(df['Result_Name'].dropna().unique())
    default_species = [s for s in all_species if "Karenia" in s] or all_species[:1]
    species_selected = st.multiselect("Select species", options=all_species, default=default_species)
    if not species_selected:
        species_selected = all_species[:1]

    # Date range filter
    min_date, max_date = df['Date_Sample_Collected'].min(), df['Date_Sample_Collected'].max()
    last_week_start = max_date - timedelta(days=7)
    date_range = st.date_input("Date range", [last_week_start, max_date],
                               min_value=min_date, max_value=max_date)
    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = min_date, max_date

# ---------------------------
# Filter dataset
# ---------------------------
mask = (
    df['Result_Name'].isin(species_selected) &
    df['Date_Sample_Collected'].between(start_date, end_date) &
    df['Result_Value_Numeric'].notna()
)
sub_df = df[mask]

st.sidebar.write(f"{len(sub_df)} of {len(df)} records shown")

# ---------------------------
# Map
# ---------------------------
m = folium.Map(
    location=[-34.9, 138.6], 
    zoom_start=6, 
    control_scale=True,
    zoom_control='bottomleft'  # Native positioning for zoom buttons
)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr='Esri', name='Satellite', overlay=False, control=True
).add_to(m)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    attr='Esri', name='Labels', overlay=True, control=True
).add_to(m)
folium.LayerControl(position='bottomright').add_to(m)  # Native positioning for layers

# Color scale
colormap = LinearColormap(colors=['green', 'yellow', 'red'], vmin=0, vmax=500000)

# Add markers
for _, row in sub_df.iterrows():
    if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
        value = row['Result_Value_Numeric']
        color = colormap(value if pd.notna(value) else 1)
        units = row.get('Units', 'cells/L')
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=6, color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=(f"<b>{row['Site_Description']}</b><br>"
                   f"{row['Date_Sample_Collected'].date()}<br>"
                   f"{row['Result_Name']}<br>"
                   f"{value:,} {units}")
        ).add_to(m)

if not sub_df.empty:
    m.fit_bounds([[sub_df['Latitude'].min(), sub_df['Longitude'].min()],
                  [sub_df['Latitude'].max(), sub_df['Longitude'].max()]])

    # ---------------------------
    # Map display (undocked)
    # ---------------------------
    st_folium(m, width='100%', height=600)

# ---------------------------
# Trends Section
# ---------------------------
if not sub_df.empty:
    st.subheader("Trends Over Time")
    
    # Dropdown for species selection (defaults to first available)
    available_species = sorted(sub_df['Result_Name'].unique())
    selected_trend_species = st.selectbox(
        "Select species for trend chart",
        options=available_species,
        index=0  # Defaults to first
    )
    
    # Filter to selected species and prep data for chart
    trend_data = sub_df[sub_df['Result_Name'] == selected_trend_species][['Date_Sample_Collected', 'Result_Value_Numeric']].copy()
    trend_data = trend_data.sort_values('Date_Sample_Collected')
    trend_data['Date_Sample_Collected'] = pd.to_datetime(trend_data['Date_Sample_Collected']).dt.date  # For cleaner x-axis
    
    if not trend_data.empty:
        # Pivot for line chart (dates as index, values as series)
        chart_df = trend_data.set_index('Date_Sample_Collected')['Result_Value_Numeric']
        st.line_chart(chart_df, use_container_width=True, height=400)
        
        # Quick stats below chart
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Max Count", f"{trend_data['Result_Value_Numeric'].max():,.0f}")
        with col2:
            st.metric("Avg Count", f"{trend_data['Result_Value_Numeric'].mean():,.0f}")
        with col3:
            st.metric("Recent (Last Sample)", f"{trend_data['Result_Value_Numeric'].iloc[-1]:,.0f}")
    else:
        st.info("No data available for the selected species in the current filters.")
else:
    st.info("No data to display trends. Adjust filters in the sidebar.")
    
    # ---------------------------
    # Disclaimer
    # ---------------------------
    st.markdown(
        """
        <div style="font-size:11px; color:#666; margin-top:10px; margin-bottom:20px;">
        This application is a research product that utilises publicly available 
        data from the South Australian Government (<a href="https://experience.arcgis.com/experience/5f0d6b22301a47bf91d198cabb030670" target="_blank">
        Algal Data</a>). No liability is accepted 
        by the author (A/Prof. Luke Mosley) or the University of Adelaide for the use 
        of this system or the data it contains, which may be incomplete, inaccurate, 
        or out of date. Users should consult the official South Australian Government 
        information at <a href="https://www.algalbloom.sa.gov.au/" target="_blank">
        https://www.algalbloom.sa.gov.au/</a> and/or obtain independent advice before 
        relying on this information.
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()


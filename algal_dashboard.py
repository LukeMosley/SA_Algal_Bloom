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

    # Markdown intro (no Streamlit title)
    st.markdown("## 🌊 Harmful Algal Bloom Monitoring Map")
    st.markdown("Interactive viewer for algal monitoring data in South Australia.")

    # File paths
    file_path = "HarmfulAlgalBloom_MonitoringSites_-1125610967936090616.xlsx"
    coords_csv = "site_coordinates.csv"
    
    # Load dataset
    df = load_data(file_path, coords_csv)

    # ---------------------------
    # Sidebar filters
    # ---------------------------
    with st.sidebar:
        st.markdown("### Filters")

        # Species selection
        all_species = sorted(df['Result_Name'].dropna().unique())
        species_selected = st.multiselect(
            "**Select species**", 
            options=all_species, 
            default=[s for s in all_species if "Karenia" in s] or all_species[:1]
        )

        # Date range (default = last 7 days)
        min_date, max_date = df['Date_Sample_Collected'].min(), df['Date_Sample_Collected'].max()
        last_week_start = max_date - timedelta(days=7)
        date_range = st.date_input(
            "**Select date range**", 
            [last_week_start, max_date],
            min_value=min_date, 
            max_value=max_date
        )

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

    st.sidebar.write(f"Showing {len(sub_df)} filtered records of {len(df)} total")

    # ---------------------------
    # Map
    # ---------------------------
    m = folium.Map(location=[-34.9, 138.6], zoom_start=6, tiles="Esri.WorldImagery")

    # Define custom green→yellow→red gradient
    colormap = LinearColormap(
        colors=["green", "yellow", "red"],
        vmin=1,
        vmax=500000
    )
    colormap.caption = "Cell count (cells/L)"
    colormap.add_to(m)

    for _, row in sub_df.iterrows():
        if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
            value = row['Result_Value_Numeric']
            color = colormap(value)
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=(
                    f"<b>{row['Site_Description']}</b><br>"
                    f"{row['Date_Sample_Collected'].date()}<br>"
                    f"{row['Result_Name']}<br>"
                    f"{value} {row['Units']}"
                )
            ).add_to(m)

    # Display map with border
    st.markdown(
        """
        <style>
        .map-container {
            border: 2px solid #ccc;
            border-radius: 10px;
            padding: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st_folium(m, width=900, height=600)
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

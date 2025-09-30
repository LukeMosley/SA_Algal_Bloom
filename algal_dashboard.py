import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit as st
import os
from branca.colormap import linear as cm

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

    # Markdown only (no Streamlit title)
    st.markdown("Interactive viewer for algal monitoring data in South Australia.")

    # File path (adjust if needed)
    file_path = "HarmfulAlgalBloom_MonitoringSites_-1125610967936090616.xlsx"
    coords_csv = "site_coordinates.csv"

    # Load dataset
    df = load_data(file_path, coords_csv)

    # ---------------------------
    # Sidebar controls
    # ---------------------------
    with st.sidebar:
        st.markdown("**Filters**")

        # Species selection (default = all Karenia)
        all_species = sorted(df['Result_Name'].dropna().unique())
        default_species = [s for s in all_species if "Karenia" in s] or all_species[:1]
        species_selected = st.multiselect(
            "**Select species**",
            options=all_species,
            default=default_species
        )

        # Date range (default = last week → max_date)
        min_date, max_date = df['Date_Sample_Collected'].min(), df['Date_Sample_Collected'].max()
        last_week_start = max_date - pd.Timedelta(days=7)
        date_range = st.date_input(
            "**Select date range**",
            [last_week_start, max_date],
            min_value=min_date,
            max_value=max_date
        )

        # Handle edge case if user selects only one date
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        else:
            start_date, end_date = min_date, max_date

    # ---------------------------
    # Filter dataset
    # ---------------------------
    sub_df = df[
        df['Result_Name'].isin(species_selected) &
        df['Date_Sample_Collected'].between(start_date, end_date) &
        df['Result_Value_Numeric'].notna()
    ]

    st.sidebar.write(f"Showing {len(sub_df)} filtered records of {len(df)} total")

    # ---------------------------
    # Map setup (Google Satellite Hybrid)
    # ---------------------------
    m = folium.Map(location=[-34.9, 138.6], zoom_start=6, tiles=None)

    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Maps",
        name="Google Satellite Hybrid",
        overlay=False,
        control=True
    ).add_to(m)

    # Define color scale for cell counts
    colormap = cm.linear.GreenRed_09.scale(1, 500000)
    colormap.caption = "Cell count (cells/L)"
    colormap.add_to(m)

    # Add circle markers
    for _, row in sub_df.iterrows():
        if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
            val = row['Result_Value_Numeric']
            color = colormap(val if val <= 500000 else 500000)
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=6,
                color=color,
                fill=True,
                fill_opacity=0.8,
                popup=(
                    f"<b>{row['Site_Description']}</b><br>"
                    f"{row['Date_Sample_Collected'].date()}<br>"
                    f"{row['Result_Name']}<br>"
                    f"{row['Result_Value_Numeric']} {row['Units']}"
                )
            ).add_to(m)

    # Render map in app (with border)
    st.markdown(
        """
        <style>
        .map-container {
            border: 2px solid #ccc;
            border-radius: 8px;
            padding: 5px;
            margin-top: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        st_folium(m, width=900, height=600)
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit as st
import os
import branca.colormap as cm
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
    # Removed title, just keep description
    st.markdown("### Interactive viewer for algal monitoring data in South Australia.")
    
    # File path (adjust if needed)
    file_path = "HarmfulAlgalBloom_MonitoringSites_-1125610967936090616.xlsx"
    coords_csv = "site_coordinates.csv"
    
    # Load dataset
    df = load_data(file_path, coords_csv)
    
    # ---------------------------
    # Sidebar controls (with border)
    # ---------------------------
    with st.sidebar:
        st.markdown("<div style='border:2px solid #ccc; padding:10px; border-radius:8px;'>", unsafe_allow_html=True)
        st.markdown("**Select species**")  # bold
        all_species = sorted(df['Result_Name'].dropna().unique())
        
        # Default = all Karenia species
        default_species = [s for s in all_species if "Karenia" in s]
        species_selected = st.multiselect(
            "", 
            options=all_species, 
            default=default_species if default_species else all_species[:1]
        )

        # Date range (default last week)
        min_date, max_date = df['Date_Sample_Collected'].min(), df['Date_Sample_Collected'].max()
        last_week_start = max_date - timedelta(days=7)
        
        st.markdown("**Select date range**")  # bold
        date_range = st.date_input("", [last_week_start, max_date])
        
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        else:
            start_date, end_date = min_date, max_date

        st.write(f"Showing {len(sub_df)} filtered records of {len(df)} total")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------
    # Filter dataset
    # ---------------------------
    mask = (
        df['Result_Name'].isin(species_selected) &
        df['Date_Sample_Collected'].between(start_date, end_date) &
        df['Result_Value_Numeric'].notna()
    )
    sub_df = df[mask]

    # ---------------------------
    # Map (with satellite-hybrid background + border)
    # ---------------------------
    m = folium.Map(
        location=[-34.9, 138.6], 
        zoom_start=6,
        tiles=None
    )
    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Satellite Hybrid",
        name="Satellite",
        subdomains=["mt0", "mt1", "mt2", "mt3"],
        overlay=False,
        control=True
    ).add_to(m)
    
    # Colour scale
    colormap = cm.linear.GreenRed_09.scale(1, 500000)
    colormap.caption = "Cell concentration (cells/L)"
    colormap.add_to(m)

    for _, row in sub_df.iterrows():
        if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
            val = row['Result_Value_Numeric']
            color = colormap(val if val < 500000 else 500000)
            
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=6,  # fixed size
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=(
                    f"<b>{row['Site_Description']}</b><br>"
                    f"{row['Date_Sample_Collected'].date()}<br>"
                    f"{row['Result_Name']}<br>"
                    f"{val:,} {row['Units']}"
                )
            ).add_to(m)
    
    # Add border around map area
    st.markdown("<div style='border:2px solid #ccc; padding:10px; border-radius:8px;'>", unsafe_allow_html=True)
    st_folium(m, width=900, height=600)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Run app
# ---------------------------
if __name__ == "__main__":
    main()


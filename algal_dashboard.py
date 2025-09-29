import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit as st
import os

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
    st.title("🌊 Harmful Algal Bloom Monitoring Map")
    st.markdown("Interactive viewer for algal monitoring data in South Australia.")
    
    # File path (adjust if needed)
    file_path = "HarmfulAlgalBloom_MonitoringSites_-1125610967936090616.xlsx"
    coords_csv = "site_coordinates.csv"
    
    # Load dataset
    df = load_data(file_path, coords_csv)
    
    # ---------------------------
    # Sidebar controls
    # ---------------------------
    st.sidebar.header("Filters")
    
    # Species selection
    all_species = sorted(df['Result_Name'].dropna().unique())
    species_selected = st.sidebar.multiselect(
        "Select species", 
        options=all_species, 
        default=[s for s in all_species if "Karenia" in s][:2] or all_species[:1]
    )
    
    # Date range
    min_date, max_date = df['Date_Sample_Collected'].min(), df['Date_Sample_Collected'].max()
    date_range = st.sidebar.date_input("Select date range", [min_date, max_date])
    
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
    
    st.sidebar.write(f"Records found: **{len(sub_df)}**")
    
    # ---------------------------
    # Map
    # ---------------------------
    m = folium.Map(location=[-34.9, 138.6], zoom_start=6)
    for _, row in sub_df.iterrows():
        if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=max(3, row['Result_Value_Numeric']**0.3 / 10),  # size scaling
                color="blue",
                fill=True,
                fill_opacity=0.6,
                popup=(
                    f"<b>{row['Site_Description']}</b><br>"
                    f"{row['Date_Sample_Collected'].date()}<br>"
                    f"{row['Result_Name']}<br>"
                    f"{row['Result_Value_Numeric']} {row['Units']}"
                )
            ).add_to(m)
    
    st_folium(m, width=900, height=600)

# ---------------------------
# Run app
# ---------------------------
if __name__ == "__main__":
    main()

import pandas as pd
import folium
from branca.colormap import LinearColormap
from branca.element import Element
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

    # Custom styles to tighten layout and adjust legend positioning
    st.markdown(
        """
        <style>
        /* Remove top padding and footer to maximize map area */
        .block-container {padding-top: 0.25rem; padding-bottom: 0.25rem;}
        header, footer {visibility: hidden;}

        /* Sidebar width + compactness */
        section[data-testid="stSidebar"] {
            font-size: 12px;
            padding: 0.25rem 0.5rem 0.5rem 0.5rem;
            width: 360px !important;
        }
        /* Small spacing for sidebar markdown */
        section[data-testid="stSidebar"] .stMarkdown p {
            margin-bottom: 0.2rem;
        }

        /* Sidebar card border and reduced margin-top */
        .sidebar-card {
            border: 1px solid #d0d0d0;
            border-radius: 8px;
            padding: 6px;
            margin-top: 0.2rem;
            background: #fff;
        }

        /* Make multiselect option chips smaller and less tall */
        /* This targets the baseweb select inside Streamlit's multiselect */
        div[data-baseweb="select"] .css-1uccc91-singleValue,
        div[data-baseweb="select"] span {
            font-size: 11px !important;
            line-height: 1.1 !important;
        }
        /* Selected tokens (chips) */
        div[data-baseweb="select"] .css-1m4v56a {  /* token text */
            font-size: 11px !important;
            padding: 4px 6px !important;
        }
        div[data-baseweb="select"] .css-1rhbuit-multiValue {  /* token box */
            margin: 2px 0 !important;
        }

        /* Map container styling - tighter padding */
        .map-container {
            border: 2px solid #ccc;
            border-radius: 8px;
            padding: 4px;
            margin: 0 auto;
        }

        /* Keep zoom control visible and on top */
        .leaflet-control-zoom {
            z-index: 10000 !important;
            transform: scale(1) !important;
        }

        /* Ensure the branca legend does not overflow */
        .branca-colormap {
            right: 10px !important;
            left: auto !important;
            bottom: 10px !important;
            width: 180px !important;
            font-size: 11px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Very small header text (no icon)
    st.markdown(
        '<div style="font-size:14px; margin:0 0 6px 0;">Interactive viewer for algal monitoring data in South Australia</div>',
        unsafe_allow_html=True
    )

    # File paths
    file_path = "HarmfulAlgalBloom_MonitoringSites_-1125610967936090616.xlsx"
    coords_csv = "site_coordinates.csv"
    
    # Load dataset
    df = load_data(file_path, coords_csv)

    # ---------------------------
    # Sidebar filters (in a card)
    # ---------------------------
    with st.sidebar:
        st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
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

    # ---------------------------
    # Filter dataset
    # ---------------------------
    mask = (
        df['Result_Name'].isin(species_selected) &
        df['Date_Sample_Collected'].between(start_date, end_date) &
        df['Result_Value_Numeric'].notna()
    )
    sub_df = df[mask]

    # Sidebar record count compact
    st.sidebar.write(f"{len(sub_df)} of {len(df)} records shown")

    # ---------------------------
    # Map (satellite) + legend + scale
    # ---------------------------
    m = folium.Map(location=[-34.9, 138.6], zoom_start=6, tiles="Esri.WorldImagery", control_scale=False)

    # Add Leaflet scale control (metric only) via a tiny JS injection
    map_name = m.get_name()  # JS map variable name, e.g., map_123abc
    scale_js = f"""
    <script>
    (function() {{
        try {{
            var map = {map_name};
            // add metric-only scale control in bottom-left
            L.control.scale({{metric:true, imperial:false, position:'bottomleft'}}).addTo(map);
            // ensure zoom control on top
            var z = document.getElementsByClassName('leaflet-control-zoom')[0];
            if (z) z.style.zIndex = 10000;
        }} catch(e) {{ console.log("scale injection err", e); }}
    }})();
    </script>
    """
    m.get_root().html.add_child(Element(scale_js))

    # Color scale (green -> yellow -> red)
    colormap = LinearColormap(colors=["green", "yellow", "red"], vmin=1, vmax=500000)
    colormap.caption = "Cell count (cells/L)"
    colormap.add_to(m)  # default adds bottom-left

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

    # Post-process legend placement (small JS to move & shrink if needed)
    legend_js = f"""
    <script>
    (function() {{
      try {{
        var map = {map_name};
        setTimeout(function() {{
          var el = document.getElementsByClassName('branca-colormap')[0];
          if (el) {{
            el.style.right = '10px';
            el.style.left = 'auto';
            el.style.bottom = '10px';
            el.style.width = '180px';
            el.style.fontSize = '11px';
          }}
        }}, 250);
      }} catch(e) {{ console.log('legend move err', e); }}
    }})();
    </script>
    """
    m.get_root().html.add_child(Element(legend_js))

    # Display map large and centered
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st_folium(m, width=1150, height=720)
    st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer - small, gray text below map
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

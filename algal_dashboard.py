import streamlit as st
import folium
from streamlit_folium import st_folium
from branca.element import Element
import geopandas as gpd

# -------------------------
# Sample data (replace with your own)
# -------------------------
import pandas as pd
import numpy as np
np.random.seed(0)
data = pd.DataFrame({
    "lat": -34 + np.random.rand(20),
    "lon": 138 + np.random.rand(20),
    "value": np.random.uniform(0, 100, 20),
    "species": np.random.choice(["Karenia", "Other"], 20)
})

# -------------------------
# Streamlit layout config
# -------------------------
st.set_page_config(layout="wide")

st.title("🌊 Algal Bloom Dashboard")

# Sidebar filters
with st.sidebar:
    st.markdown("### Filters")
    selected_species = st.multiselect(
        "Select species", 
        options=data["species"].unique(), 
        default=data["species"].unique()
    )
    value_range = st.slider(
        "Value range", 
        float(data["value"].min()), 
        float(data["value"].max()), 
        (float(data["value"].min()), float(data["value"].max()))
    )

# -------------------------
# Filtered data
# -------------------------
filtered = data[
    data["species"].isin(selected_species) &
    (data["value"] >= value_range[0]) &
    (data["value"] <= value_range[1])
]

# -------------------------
# Folium map setup
# -------------------------
m = folium.Map(location=[-34.9, 138.6], zoom_start=7, control_scale=True)

# Hybrid basemap (satellite + labels)
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    attr="Google Hybrid",
    name="Hybrid",
    overlay=False,
    control=True
).add_to(m)

# Add markers
for _, row in filtered.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=6,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.7,
        popup=f"Species: {row['species']}<br>Value: {row['value']:.1f}"
    ).add_to(m)

# -------------------------
# Add vertical legend (bottom-left)
# -------------------------
from branca.colormap import LinearColormap
colormap = LinearColormap(
    colors=["green", "yellow", "red"],
    vmin=data["value"].min(),
    vmax=data["value"].max()
).to_step(5)
colormap.caption = "Value"

m.add_child(colormap)

# Force reposition with injected JS
legend_js = """
<script>
(function() {
  var el = document.getElementsByClassName('branca-colormap')[0];
  if (el) {
    el.style.position = 'absolute';
    el.style.left = '10px';
    el.style.bottom = '10px';
    el.style.width = '20px';
    el.style.height = '150px';
    el.style.zIndex = '9999';
  }
})();
</script>
"""
m.get_root().html.add_child(Element(legend_js))

# -------------------------
# Render map in Streamlit
# -------------------------
st_folium(m, use_container_width=True, height=700)

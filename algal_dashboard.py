import pandas as pd
import folium
from branca.colormap import linear
from streamlit_folium import st_folium
import streamlit as st
import altair as alt
import os
from datetime import timedelta

# ---------------------------
# Load data + coordinates
# ---------------------------
@st.cache_data
def load_data(file_path, coords_csv="site_coordinates.csv"):
    if not os.path.exists(file_path):
        st.warning(f"⚠️ Main data file '{file_path}' not found. Using empty dataset.")
        return pd.DataFrame()

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
    </style>
    """, unsafe_allow_html=True)

    # ---------------------------
    # Load data
    # ---------------------------
    file_path = "HarmfulAlgalBloom_MonitoringSites_8382667239581124066.csv"
    coords_csv = "site_coordinates.csv"
    df = load_data(file_path, coords_csv)

    if df.empty:
        st.error("No data loaded.")
        return

    # ---------------------------
    # Sidebar: Filters
    # ---------------------------
    with st.sidebar:
        st.markdown(
            '<div style="font-size:18px; font-weight:bold; text-align:center; margin-bottom:0.5rem;">'
            'Harmful Algal Bloom Dashboard – South Australia</div>',
            unsafe_allow_html=True
        )

        all_species = sorted(df['Result_Name'].dropna().unique())
        default_species = [s for s in all_species if "Karenia" in s] or all_species[:1]
        species_selected = st.multiselect("Select species", options=all_species, default=default_species)
        if not species_selected:
            species_selected = all_species[:1]

        min_date, max_date = df['Date_Sample_Collected'].min(), df['Date_Sample_Collected'].max()
        last_week_start = max_date - timedelta(days=7)
        date_range = st.date_input(
            "Date range",
            [last_week_start, max_date],
            min_value=min_date, max_value=max_date
        )

        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        else:
            start_date, end_date = min_date, max_date

        st.markdown(
            """
            <div style="font-size:11px; color:#666; margin-top:10px; margin-bottom:20px; padding:10px; border-top:1px solid #ddd;">
            This application is a research product that utilises publicly available 
            data from the South Australian Government. No liability is accepted 
            by the author (A/Prof. Luke Mosley) or the University of Adelaide for the use 
            of this system or the data it contains, which may be incomplete, inaccurate, 
            or out of date. Users should consult the official South Australian Government 
            information at <a href="https://www.algalbloom.sa.gov.au/" target="_blank">
            https://www.algalbloom.sa.gov.au/</a>.
            </div>
            """,
            unsafe_allow_html=True
        )

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
        control_scale=True
    )

    # Basemap + labels
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False, control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Labels", overlay=True, control=True
    ).add_to(m)

    folium.LayerControl(position="bottomright").add_to(m)

    # Viridis colormap
    colormap = linear.viridis.scale(0, 500000)
    colormap.caption = "Cells per L"
    colormap.add_to(m)

    # Add markers
    for _, row in sub_df.iterrows():
        if pd.notna(row.get("Latitude")) and pd.notna(row.get("Longitude")):
            value = row["Result_Value_Numeric"]
            color = colormap(value if pd.notna(value) else 0)
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=(
                    f"<b>{row['Site_Description']}</b><br>"
                    f"{row['Date_Sample_Collected'].date()}<br>"
                    f"{row['Result_Name']}<br>"
                    f"{value:,} {row.get('Units','cells/L')}"
                )
            ).add_to(m)

    if not sub_df.empty:
        m.fit_bounds([
            [sub_df["Latitude"].min(), sub_df["Longitude"].min()],
            [sub_df["Latitude"].max(), sub_df["Longitude"].max()]
        ])

    st_folium(m, width="100%", height=500)

    # ---------------------------
    # Trends Section
    # ---------------------------
    if not df.empty:
        st.subheader("Trends Over Time")

        all_species = sorted(df["Result_Name"].dropna().unique())
        default_trend_species = [s for s in all_species if "Karenia" in s] or all_species[:3]

        selected_trend_species = st.multiselect(
            "Select species for trend chart",
            options=all_species,
            default=default_trend_species
        )

        all_sites = sorted(df["Site_Description"].dropna().unique())
        selected_site = st.selectbox("Filter by site", ["All Sites"] + all_sites, index=0)

        plot_df = df[
            (df["Result_Name"].isin(selected_trend_species)) &
            (df["Result_Value_Numeric"].notna())
        ].copy()

        if selected_site != "All Sites":
            plot_df = plot_df[plot_df["Site_Description"] == selected_site]

        plot_df = plot_df.sort_values("Date_Sample_Collected")

        if not plot_df.empty:
            trend_df = plot_df.pivot_table(
                index="Date_Sample_Collected",
                columns="Result_Name",
                values="Result_Value_Numeric",
                aggfunc="mean"
            ).reset_index()

            trend_melted = trend_df.melt(
                id_vars="Date_Sample_Collected",
                var_name="Species",
                value_name="Cell_Count"
            )

            chart = alt.Chart(trend_melted).mark_line().encode(
                x=alt.X("Date_Sample_Collected:T", title="Date"),
                y=alt.Y("Cell_Count:Q", title="Cell Count per L"),
                color=alt.Color("Species:N", title="Species"),
                tooltip=["Date_Sample_Collected", "Species", "Cell_Count"]
            ).properties(
                width=800,
                height=400,
                title="Trends for Selected Species"
            ).interactive()

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No data available for the selected species and site.")

if __name__ == "__main__":
    main()


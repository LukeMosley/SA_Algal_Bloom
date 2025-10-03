### Overview
This interactive dashboard visualises harmful algal bloom (HAB) monitoring data from South Australian coastal sites. 

Built with Streamlit, it provides real-time filtering by species (e.g., Karenia sp.), date ranges, and sites, overlaid on an interactive satellite map. 

Users can explore cell counts per liter with color-coded markers and view time-series trends for deeper analysis.

The app leverages publicly available data from the South Australian Government Algal Bloom Monitoring Program (https://experience.arcgis.com/experience/5f0d6b22301a47bf91d198cabb030670).

It's designed for the community, scientists, and coastal managers to help them visualise the algal bloom data.

## Key Features:

Interactive Map: Folium-based satellite view with Viridis color scale (purple for low counts, yellow for high).
Filters: Multi-select species (defaults to Karenia), date range (last week by default), and site-specific views.

Trends Chart: Altair-powered line plots for multi-species time series, with zoom/pan.

## Implementation in Python
The code is written in Python.

The main script to implement the dashboard is algal_dashboard.py with the accompanying requirements.txt file for the python libaries used at run time.

The script reads in the latest (manually uploaded) csv file of SA government algal data present in the main folder (HarmfulAlgalBloom_MonitoringSites....csv).

Site coodinates are read from the site_coordinates.csv file (note an additional folder is present in the main repository that contains another script to generate this file from SA government supplies excel file of sites - this only needs to be run if more sites are added by SA Government).

The script is then called from streamlit, and implemented on the streamlit community cloud platform (https://sa-algal-bloom.streamlit.app/).

## Disclaimer
This application is a research product that utilises publicly available data from the South Australian Government. No liability is accepted by the author (A/Prof. Luke Mosley) or Adelaide University for the use of this system or the data it contains, which may be incomplete, inaccurate, or out of date. 
Users should consult the official South Australian Government information at https://www.algalbloom.sa.gov.au/ and/or obtain independent advice before relying on this information.

"""Donor → recipient map (ZIP centroids, flow lines)."""

import streamlit as st
from streamlit_folium import st_folium

from platform_cache import load_hist
from platform_ui import hero, inject_custom_css
from rlc_data import CITIES
from rlc_folium import map_routes_and_sites

st.set_page_config(page_title="Map — Routes", page_icon="🗺️", layout="wide")
inject_custom_css()

hero(
    "Map — donors, recipients, routes",
    "ZIP-level view — green pickups, blue drop-offs, gray flows weighted by pounds (not street GPS).",
    overline="Geospatial · Flow analysis",
)

hist = load_hist()

c1, c2, c3 = st.columns([1, 1, 1])
city = c1.selectbox("Metro", CITIES, index=0)
top_flows = c2.slider("Max flow lines to draw", 20, 200, 100, 10)
min_lbs = c3.number_input("Minimum lbs on a flow", min_value=1.0, value=25.0, step=5.0)

m = map_routes_and_sites(hist, city, top_flows=int(top_flows), min_flow_lbs=float(min_lbs))
st_folium(m, use_container_width=True, height=620)

st.caption("Tip: zoom and use layer controls. Clustering groups nearby markers when zoomed out.")

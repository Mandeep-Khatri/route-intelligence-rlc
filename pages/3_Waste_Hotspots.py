"""Where surplus food concentrates (donor ZIP heat)."""

import streamlit as st
from streamlit_folium import st_folium

from platform_cache import load_hist
from platform_ui import hero, inject_custom_css
from rlc_data import CITIES, aggregate_donor_hotspots
from rlc_folium import map_waste_heatmap

st.set_page_config(page_title="Waste hot spots", page_icon="🔥", layout="wide")
inject_custom_css()

hero(
    "Waste & surplus hot spots",
    "Heat by donor ZIP — target outreach, batching, and new donor recruitment.",
    overline="Demand · Concentration",
)
st.info(
    "**Note:** “Waste” = food **at risk of disposal**. Hotter ZIPs = **more recurring surplus** in historical rescues."
)

hist = load_hist()
city = st.selectbox("Metro", CITIES, index=0, key="hot_city")
top_z = st.slider("Top donor ZIPs to show", 15, 80, 40)

m = map_waste_heatmap(hist, city, top_zips=int(top_z))
st_folium(m, use_container_width=True, height=620)

st.subheader("Ranked donor ZIPs (same filter)")
t = aggregate_donor_hotspots(hist, city).head(top_z)
st.dataframe(t, use_container_width=True, hide_index=True)

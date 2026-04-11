import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from math import radians, sin, cos, sqrt, atan2
from itertools import combinations
from datetime import date
import os

st.set_page_config(page_title="RLC Route Batching Engine", page_icon="\U0001F697", layout="wide")

# === UTILITY FUNCTIONS ===
def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

@st.cache_data
def load_data():
    df = pd.read_csv("all_rescures_all_time_final_nyc_boston_la_chi.csv")
    df["Donor City"] = df["Donor City"].str.strip().str.title()
    df["Donor City"] = df["Donor City"].replace({"Nyc": "New York City", "La": "Los Angeles"})
    df["Rescue Date"] = pd.to_datetime(df["Rescue Date"])
    df["Year"] = df["Rescue Date"].dt.year
    df = df[df["Year"] <= 2026]
    df["Food Category"] = df["Food Category"].fillna("Uncategorized")
    df["Donor Name"] = df["Donor Name"].str.strip()
    geo = pd.read_csv("donor_geocoded.csv")
    geo = geo.dropna(subset=["latitude", "longitude"])
    return df, geo

@st.cache_data
def compute_batching(df, geo, threshold, driver_cost):
    batch_pairs = []
    for city in geo["Donor City"].unique():
        donors = geo[geo["Donor City"] == city]
        for i in range(len(donors)):
            for j in range(i + 1, len(donors)):
                d1 = donors.iloc[i]
                d2 = donors.iloc[j]
                dist = haversine_miles(d1["latitude"], d1["longitude"], d2["latitude"], d2["longitude"])
                if dist <= threshold:
                    batch_pairs.append({
                        "City": city,
                        "Donor_A": d1["Donor Name"],
                        "Donor_B": d2["Donor Name"],
                        "Distance_Miles": round(dist, 3),
                        "Lat_A": d1["latitude"], "Lon_A": d1["longitude"],
                        "Lat_B": d2["latitude"], "Lon_B": d2["longitude"]
                    })
    if not batch_pairs:
        return pd.DataFrame()
    batch_df = pd.DataFrame(batch_pairs)
    df_dates = df[["Donor Name", "Rescue Date"]].drop_duplicates()
    savings_rows = []
    for _, row in batch_df.iterrows():
        dates_a = set(df_dates[df_dates["Donor Name"] == row["Donor_A"]]["Rescue Date"])
        dates_b = set(df_dates[df_dates["Donor Name"] == row["Donor_B"]]["Rescue Date"])
        same_day = len(dates_a & dates_b)
        savings_rows.append({**row.to_dict(), "Same_Day_Pickups": same_day, "Potential_Saving_USD": same_day * driver_cost})
    savings_df = pd.DataFrame(savings_rows)
    savings_df = savings_df.sort_values("Potential_Saving_USD", ascending=False).reset_index(drop=True)
    return savings_df

def build_batch_map(savings_df, geo, city_filter):
    city_geo = geo[geo["Donor City"] == city_filter]
    city_pairs = savings_df[savings_df["City"] == city_filter]
    if city_geo.empty:
        return None
    center_lat = city_geo["latitude"].mean()
    center_lon = city_geo["longitude"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="CartoDB positron")
    for _, row in city_geo.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=7, color="steelblue", fill=True, fill_color="steelblue",
            fill_opacity=0.7, popup=row["Donor Name"], tooltip=row["Donor Name"]
        ).add_to(m)
    for _, pair in city_pairs.iterrows():
        folium.PolyLine(
            locations=[[pair["Lat_A"], pair["Lon_A"]], [pair["Lat_B"], pair["Lon_B"]]],
            color="tomato", weight=2, opacity=0.7,
            tooltip=f"{pair['Donor_A']} <> {pair['Donor_B']}: {pair['Distance_Miles']} mi"
        ).add_to(m)
    return m

def build_distance_map(geo, donor_a, donor_b):
    row_a = geo[geo["Donor Name"] == donor_a].iloc[0]
    row_b = geo[geo["Donor Name"] == donor_b].iloc[0]
    dist = haversine_miles(row_a["latitude"], row_a["longitude"], row_b["latitude"], row_b["longitude"])
    center_lat = (row_a["latitude"] + row_b["latitude"]) / 2
    center_lon = (row_a["longitude"] + row_b["longitude"]) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles="CartoDB positron")
    folium.Marker(
        location=[row_a["latitude"], row_a["longitude"]],
        popup=f"<b>{donor_a}</b><br>{row_a.get('Donor Address', '')}",
        tooltip=donor_a,
        icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
    ).add_to(m)
    folium.Marker(
        location=[row_b["latitude"], row_b["longitude"]],
        popup=f"<b>{donor_b}</b><br>{row_b.get('Donor Address', '')}",
        tooltip=donor_b,
        icon=folium.Icon(color="red", icon="cutlery", prefix="fa")
    ).add_to(m)
    folium.PolyLine(
        locations=[[row_a["latitude"], row_a["longitude"]], [row_b["latitude"], row_b["longitude"]]],
        color="#e74c3c", weight=4, opacity=0.9, dash_array="10",
        tooltip=f"Distance: {dist:.3f} miles ({dist * 5280:.0f} ft)"
    ).add_to(m)
    folium.Marker(
        location=[center_lat, center_lon],
        icon=folium.DivIcon(html=f'<div style="font-size:14px; font-weight:bold; color:#e74c3c; background:white; padding:2px 6px; border-radius:4px; border:1px solid #e74c3c; white-space:nowrap;">{dist:.3f} mi</div>')
    ).add_to(m)
    return m, dist

def geocode_address(address):
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="food_rescue_team8_v1")
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude, location.address
        return None, None, None
    except Exception:
        return None, None, None

def build_proximity_map(new_lat, new_lon, new_name, nearby_df, geo, radius_mi):
    m = folium.Map(location=[new_lat, new_lon], zoom_start=15, tiles="CartoDB positron")
    folium.Marker(
        location=[new_lat, new_lon],
        popup=f"<b>NEW: {new_name}</b>",
        tooltip=f"NEW: {new_name}",
        icon=folium.Icon(color="green", icon="star", prefix="fa")
    ).add_to(m)
    radius_meters = radius_mi * 1609.34
    folium.Circle(
        location=[new_lat, new_lon],
        radius=radius_meters,
        color="green", fill=True, fill_opacity=0.08,
        tooltip=f"Search radius: {radius_mi} mi"
    ).add_to(m)
    for _, row in nearby_df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"<b>{row['Donor Name']}</b><br>Distance: {row['Distance_Miles']:.3f} mi",
            tooltip=f"{row['Donor Name']} ({row['Distance_Miles']:.3f} mi)",
            icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
        ).add_to(m)
        folium.PolyLine(
            locations=[[new_lat, new_lon], [row["latitude"], row["longitude"]]],
            color="#3498db", weight=2, opacity=0.5, dash_array="8",
            tooltip=f"{row['Donor Name']}: {row['Distance_Miles']:.3f} mi"
        ).add_to(m)
    return m

# === MAIN APP ===
st.title("\U0001F697 RLC Route Batching Engine")
st.markdown("**Rescuing Leftover Cuisine** \u2014 Identify nearby donors for batched pickups and explore donor distances.")

df, geo = load_data()

st.sidebar.header("\u2699\uFE0F Settings")
page = st.sidebar.radio("Navigate", ["\U0001F5FA\uFE0F Route Batching Engine", "\U0001F4CF Donor Distance Map", "\U0001F50D New Partner Finder"])

if page == "\U0001F5FA\uFE0F Route Batching Engine":
    st.header("\U0001F5FA\uFE0F Route Batching Engine")
    st.markdown("Find donor pairs close enough to batch into a single pickup trip, reducing driver costs.")
    col1, col2, col3 = st.columns(3)
    with col1:
        threshold = st.slider("Max distance between donors (miles)", 0.1, 1.0, 0.5, 0.05)
    with col2:
        driver_cost = st.slider("Driver cost per trip (\u0024)", 5, 30, 15, 1)
    with col3:
        cities = sorted(geo["Donor City"].unique())
        city_filter = st.selectbox("City", cities)
    savings_df = compute_batching(df, geo, threshold, driver_cost)
    if savings_df.empty:
        st.warning("No batchable pairs found at this threshold.")
    else:
        city_data = savings_df[savings_df["City"] == city_filter]
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Batchable Pairs", f"{len(city_data):,}")
        k2.metric("Same-Day Overlaps", f"{city_data['Same_Day_Pickups'].sum():,}")
        k3.metric(f"Potential Savings (at \u0024{driver_cost}/trip)", f"\u0024{city_data['Potential_Saving_USD'].sum():,}")
        k4.metric("Avg Distance", f"{city_data['Distance_Miles'].mean():.2f} mi" if len(city_data) > 0 else "N/A")
        st.subheader(f"\U0001F30D {city_filter} \u2014 Batchable Donor Pairs")
        batch_map = build_batch_map(savings_df, geo, city_filter)
        if batch_map:
            st_folium(batch_map, width=None, height=500, use_container_width=True)
        st.subheader("\U0001F4CB Top Batchable Pairs")
        st.dataframe(city_data[["Donor_A", "Donor_B", "Distance_Miles", "Same_Day_Pickups", "Potential_Saving_USD"]].head(25), use_container_width=True)
        st.subheader("\U0001F4CA All Cities Summary")
        summary = savings_df.groupby("City").agg(
            Pairs=("Donor_A", "count"),
            Avg_Distance=("Distance_Miles", "mean"),
            Total_Overlaps=("Same_Day_Pickups", "sum"),
            Total_Savings=("Potential_Saving_USD", "sum")
        ).sort_values("Total_Savings", ascending=False)
        st.dataframe(summary, use_container_width=True)
        total = int(savings_df["Potential_Saving_USD"].sum())
        st.success(f"**Total estimated savings across all cities: \u0024{total:,}** (at \u0024{driver_cost}/trip saved)")

elif page == "\U0001F4CF Donor Distance Map":
    st.header("\U0001F4CF Donor Distance Map")
    st.markdown("Select any two donors in the same city to see their locations and the distance between them.")
    ctrl1, ctrl2 = st.columns([2, 1])
    with ctrl1:
        cities = sorted(geo["Donor City"].unique())
        selected_city = st.selectbox("Select City", cities, key="dist_city")
    with ctrl2:
        driver_cost_dist = st.slider("Driver cost per trip (\u0024)", 5, 30, 15, 1, key="dist_driver_cost")
    city_donors = geo[geo["Donor City"] == selected_city]["Donor Name"].sort_values().unique()
    if len(city_donors) < 2:
        st.warning("Need at least 2 geocoded donors in this city.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            donor_a = st.selectbox("\U0001F4CD Donor A", city_donors, index=0, key="donor_a")
        with col2:
            default_b = 1 if len(city_donors) > 1 else 0
            donor_b = st.selectbox("\U0001F4CD Donor B", city_donors, index=default_b, key="donor_b")
        if donor_a == donor_b:
            st.warning("Please select two different donors.")
        else:
            dist_map, dist = build_distance_map(geo, donor_a, donor_b)
            c1, c2, c3 = st.columns(3)
            c1.metric("Distance", f"{dist:.3f} miles")
            c2.metric("Distance (feet)", f"{dist * 5280:,.0f} ft")
            batchable = "\u2705 Yes" if dist <= 0.5 else "\u274C No"
            c3.metric("Batchable (< 0.5 mi)?", batchable)
            df_dates = df[["Donor Name", "Rescue Date"]].drop_duplicates()
            dates_a = set(df_dates[df_dates["Donor Name"] == donor_a]["Rescue Date"])
            dates_b = set(df_dates[df_dates["Donor Name"] == donor_b]["Rescue Date"])
            same_day = len(dates_a & dates_b)
            st.markdown(f"**Same-day pickup overlaps:** {same_day:,} days")
            if dist <= 0.5 and same_day > 0:
                st.success(f"\U0001F4B0 These donors could have saved **\u0024{same_day * driver_cost_dist:,}** if batched (at \u0024{driver_cost_dist}/trip).")
            elif dist > 0.5:
                st.info("These donors are too far apart for efficient batching.")
            st.subheader("\U0001F5FA\uFE0F Map")
            st_folium(dist_map, width=None, height=500, use_container_width=True)
            with st.expander("\U0001F50D Donor Details"):
                row_a = geo[geo["Donor Name"] == donor_a].iloc[0]
                row_b = geo[geo["Donor Name"] == donor_b].iloc[0]
                dc1, dc2 = st.columns(2)
                with dc1:
                    st.markdown(f"**\U0001F7E6 {donor_a}**")
                    st.markdown(f"Address: {row_a.get('Donor Address', 'N/A')}")
                    st.markdown(f"City: {row_a.get('Donor City', 'N/A')}")
                    st.markdown(f"Lat/Lon: {row_a['latitude']:.6f}, {row_a['longitude']:.6f}")
                with dc2:
                    st.markdown(f"**\U0001F7E5 {donor_b}**")
                    st.markdown(f"Address: {row_b.get('Donor Address', 'N/A')}")
                    st.markdown(f"City: {row_b.get('Donor City', 'N/A')}")
                    st.markdown(f"Lat/Lon: {row_b['latitude']:.6f}, {row_b['longitude']:.6f}")

elif page == "\U0001F50D New Partner Finder":
    st.header("\U0001F50D New Partner Proximity Finder")
    st.markdown("Enter a potential new partner's address to see how close they are to existing RLC donors. Nearby donors mean **batching opportunities** from day one!")
    inp1, inp2 = st.columns([3, 1])
    with inp1:
        new_address = st.text_input("\U0001F3E0 New partner address", placeholder="e.g. 100 Summer Street, Boston, MA")
    with inp2:
        new_name = st.text_input("\U0001F4DB Partner name", value="New Partner")
    sl1, sl2 = st.columns(2)
    with sl1:
        search_radius = st.slider("Search radius (miles)", 0.1, 2.0, 0.5, 0.1, key="prox_radius")
    with sl2:
        driver_cost_new = st.slider("Driver cost per trip (\u0024)", 5, 30, 15, 1, key="prox_driver_cost")
    if new_address:
        with st.spinner("\U0001F50E Geocoding address..."):
            lat, lon, resolved = geocode_address(new_address)
        if lat is None:
            st.error("Could not geocode that address. Please try a more specific address.")
        else:
            st.success(f"\U0001F4CD Address resolved to: {resolved}")
            nearby_rows = []
            for _, row in geo.iterrows():
                d = haversine_miles(lat, lon, row["latitude"], row["longitude"])
                if d <= search_radius:
                    nearby_rows.append({
                        "Donor Name": row["Donor Name"],
                        "Donor City": row.get("Donor City", ""),
                        "Donor Address": row.get("Donor Address", ""),
                        "latitude": row["latitude"],
                        "longitude": row["longitude"],
                        "Distance_Miles": round(d, 3)
                    })
            nearby_df = pd.DataFrame(nearby_rows).sort_values("Distance_Miles").reset_index(drop=True) if nearby_rows else pd.DataFrame()
            if nearby_df.empty:
                st.warning(f"No existing donors found within {search_radius} miles of this address.")
            else:
                df_dates = df[["Donor Name", "Rescue Date"]].drop_duplicates()
                donor_days = df_dates.groupby("Donor Name").size().reset_index(name="Rescue_Days")
                nearby_df = nearby_df.merge(donor_days, on="Donor Name", how="left")
                nearby_df["Rescue_Days"] = nearby_df["Rescue_Days"].fillna(0).astype(int)
                nearby_df["Est_Savings"] = nearby_df["Rescue_Days"] * driver_cost_new
                k1, k2, k3 = st.columns(3)
                k1.metric("Nearby Donors", f"{len(nearby_df):,}")
                nearest = nearby_df.iloc[0]
                k2.metric("Nearest Donor", f"{nearest['Donor Name']}")
                k3.metric("Nearest Distance", f"{nearest['Distance_Miles']:.3f} mi")
                st.subheader("\U0001F4CB Nearby Existing Donors")
                display_df = nearby_df[["Donor Name", "Distance_Miles", "Donor City", "Rescue_Days", "Est_Savings"]].copy()
                display_df.columns = ["Donor", "Distance (mi)", "City", "Historical Rescue Days", "Est. Savings (\u0024)"]
                st.dataframe(display_df, use_container_width=True)
                total_savings = int(nearby_df["Est_Savings"].sum())
                st.success(f"\U0001F4B0 **Total estimated batching savings with nearby donors: \u0024{total_savings:,}** (at \u0024{driver_cost_new}/trip saved, based on historical rescue day counts)")
                st.subheader("\U0001F5FA\uFE0F Proximity Map")
                prox_map = build_proximity_map(lat, lon, new_name, nearby_df, geo, search_radius)
                st_folium(prox_map, width=None, height=500, use_container_width=True)
                with st.expander("\U0001F3C6 Top 10 Closest Donors"):
                    for i, row in nearby_df.head(10).iterrows():
                        st.markdown(f"**{i+1}. {row['Donor Name']}** \u2014 {row['Distance_Miles']:.3f} mi \u2014 {row['Rescue_Days']} rescue days \u2014 Est. savings: \u0024{row['Est_Savings']:,}")

# Footer
st.sidebar.divider()
st.sidebar.markdown("**JPMC Data for Good Hackathon** | Team-8")
st.sidebar.markdown(f"Data: {len(df):,} rescues | {len(geo)} geocoded donors")

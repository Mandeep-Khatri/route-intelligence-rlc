import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from math import radians, sin, cos, sqrt, atan2
from itertools import combinations
from datetime import date
import os

st.set_page_config(page_title="RLC Route Batching Engine", page_icon="🚗", layout="wide")

# === UTILITY FUNCTIONS ===
def haversine_miles(lat1, lon1, lat2, lon2):
    """Compute straight-line distance in miles between two lat/lon points."""
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

@st.cache_data
def load_data():
    """Load and clean the rescue data + geocoded donors."""
    df = pd.read_csv("all_rescures_all_time_final_nyc_boston_la_chi.csv")
    
    # Basic cleaning
    df["Donor City"] = df["Donor City"].str.strip().str.title()
    df["Donor City"] = df["Donor City"].replace({"Nyc": "New York City", "La": "Los Angeles"})
    df["Rescue Date"] = pd.to_datetime(df["Rescue Date"])
    df["Year"] = df["Rescue Date"].dt.year
    df = df[df["Year"] <= 2026]
    df["Food Category"] = df["Food Category"].fillna("Uncategorized")
    df["Donor Name"] = df["Donor Name"].str.strip()
    
    # Load geocoded donors
    geo = pd.read_csv("donor_geocoded.csv")
    geo = geo.dropna(subset=["latitude", "longitude"])
    
    return df, geo

@st.cache_data
def compute_batching(df, geo, threshold, driver_cost):
    """Find batchable donor pairs and compute savings."""
    batch_pairs = []
    for city, group in geo.groupby("Donor City"):
        donors = group.reset_index(drop=True)
        for i, j in combinations(range(len(donors)), 2):
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
    
    # Count same-day co-occurrences
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
    """Build a folium map showing batchable pairs for a city."""
    city_geo = geo[geo["Donor City"] == city_filter]
    city_pairs = savings_df[savings_df["City"] == city_filter]
    
    if city_geo.empty:
        return None
    
    center_lat = city_geo["latitude"].mean()
    center_lon = city_geo["longitude"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="CartoDB positron")
    
    # Add donor markers
    for _, row in city_geo.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=7, color="steelblue", fill=True, fill_color="steelblue",
            fill_opacity=0.7, popup=row["Donor Name"], tooltip=row["Donor Name"]
        ).add_to(m)
    
    # Draw lines between batchable pairs
    for _, pair in city_pairs.iterrows():
        folium.PolyLine(
            locations=[[pair["Lat_A"], pair["Lon_A"]], [pair["Lat_B"], pair["Lon_B"]]],
            color="tomato", weight=2, opacity=0.7,
            tooltip=f"{pair['Donor_A']} <> {pair['Donor_B']}: {pair['Distance_Miles']} mi | ${pair['Potential_Saving_USD']:,} savings"
        ).add_to(m)
    
    return m

def build_distance_map(geo, donor_a, donor_b):
    """Build a folium map showing distance between two specific donors."""
    row_a = geo[geo["Donor Name"] == donor_a].iloc[0]
    row_b = geo[geo["Donor Name"] == donor_b].iloc[0]
    
    dist = haversine_miles(row_a["latitude"], row_a["longitude"], row_b["latitude"], row_b["longitude"])
    
    center_lat = (row_a["latitude"] + row_b["latitude"]) / 2
    center_lon = (row_a["longitude"] + row_b["longitude"]) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles="CartoDB positron")
    
    # Marker A
    folium.Marker(
        location=[row_a["latitude"], row_a["longitude"]],
        popup=f"<b>{donor_a}</b><br>{row_a.get('Donor Address', '')}",
        tooltip=donor_a,
        icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
    ).add_to(m)
    
    # Marker B
    folium.Marker(
        location=[row_b["latitude"], row_b["longitude"]],
        popup=f"<b>{donor_b}</b><br>{row_b.get('Donor Address', '')}",
        tooltip=donor_b,
        icon=folium.Icon(color="red", icon="cutlery", prefix="fa")
    ).add_to(m)
    
    # Distance line
    folium.PolyLine(
        locations=[[row_a["latitude"], row_a["longitude"]], [row_b["latitude"], row_b["longitude"]]],
        color="#e74c3c", weight=4, opacity=0.9, dash_array="10",
        tooltip=f"Distance: {dist:.3f} miles ({dist * 5280:.0f} ft)"
    ).add_to(m)
    
    # Distance label at midpoint
    folium.Marker(
        location=[center_lat, center_lon],
        icon=folium.DivIcon(html=f'<div style="font-size:14px;font-weight:bold;color:#e74c3c;background:white;padding:3px 8px;border-radius:4px;border:2px solid #e74c3c;white-space:nowrap">{dist:.3f} mi ({dist * 5280:.0f} ft)</div>')
    ).add_to(m)
    
    return m, dist

# === MAIN APP ===
st.title("🚗 RLC Route Batching Engine")
st.markdown("**Rescuing Leftover Cuisine** — Identify nearby donors for batched pickups and explore donor distances.")

# Load data
df, geo = load_data()

# Sidebar
st.sidebar.header("⚙️ Settings")
page = st.sidebar.radio("Navigate", ["🗺️ Route Batching Engine", "📏 Donor Distance Map"])

if page == "🗺️ Route Batching Engine":
    st.header("🗺️ Route Batching Engine")
    st.markdown("Find donor pairs close enough to batch into a single pickup trip, reducing driver costs.")
    
    # Controls
    col1, col2, col3 = st.columns(3)
    with col1:
        threshold = st.slider("Max distance between donors (miles)", 0.1, 1.0, 0.5, 0.05)
    with col2:
        driver_cost = st.slider("Driver cost per trip ($)", 10, 25, 15, 1)
    with col3:
        cities = sorted(geo["Donor City"].unique())
        city_filter = st.selectbox("City", cities)
    
    # Compute batching
    savings_df = compute_batching(df, geo, threshold, driver_cost)
    
    if savings_df.empty:
        st.warning("No batchable pairs found at this distance threshold.")
    else:
        city_data = savings_df[savings_df["City"] == city_filter]
        
        # Metrics row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Batchable Pairs", f"{len(city_data):,}")
        m2.metric("Same-Day Overlaps", f"{int(city_data['Same_Day_Pickups'].sum()):,}")
        m3.metric("Potential Savings", f"${int(city_data['Potential_Saving_USD'].sum()):,}")
        m4.metric("Avg Distance", f"{city_data['Distance_Miles'].mean():.2f} mi" if len(city_data) > 0 else "N/A")
        
        # Map
        st.subheader(f"📍 {city_filter} — Batchable Donor Pairs")
        batch_map = build_batch_map(savings_df, geo, city_filter)
        if batch_map:
            st_folium(batch_map, width=None, height=500, use_container_width=True)
        
        # Table
        st.subheader("📊 Batchable Pairs Detail")
        display_cols = ["Donor_A", "Donor_B", "Distance_Miles", "Same_Day_Pickups", "Potential_Saving_USD"]
        st.dataframe(
            city_data[display_cols].reset_index(drop=True),
            use_container_width=True,
            column_config={
                "Donor_A": st.column_config.TextColumn("Donor A"),
                "Donor_B": st.column_config.TextColumn("Donor B"),
                "Distance_Miles": st.column_config.NumberColumn("Distance (mi)", format="%.3f"),
                "Same_Day_Pickups": st.column_config.NumberColumn("Same-Day Pickups"),
                "Potential_Saving_USD": st.column_config.NumberColumn("Savings ($)", format="$%d")
            }
        )
        
        # Total across all cities
        st.divider()
        st.subheader("🌍 All Cities Summary")
        summary = savings_df.groupby("City").agg(
            Pairs=("Donor_A", "count"),
            Total_Same_Day=("Same_Day_Pickups", "sum"),
            Total_Savings=("Potential_Saving_USD", "sum")
        ).sort_values("Total_Savings", ascending=False)
        st.dataframe(summary, use_container_width=True)
        total = int(savings_df["Potential_Saving_USD"].sum())
        st.success(f"**Total estimated savings across all cities: ${total:,}** (at ${driver_cost}/trip saved)")

elif page == "📏 Donor Distance Map":
    st.header("📏 Donor Distance Map")
    st.markdown("Select any two donors in the same city to see their locations and the distance between them.")
    
    # City selector
    cities = sorted(geo["Donor City"].unique())
    selected_city = st.selectbox("Select City", cities, key="dist_city")
    
    # Filter donors for this city
    city_donors = geo[geo["Donor City"] == selected_city]["Donor Name"].sort_values().unique()
    
    if len(city_donors) < 2:
        st.warning("Need at least 2 geocoded donors in this city.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            donor_a = st.selectbox("🔵 Donor A", city_donors, index=0, key="donor_a")
        with col2:
            # Default to second donor if available
            default_b = 1 if len(city_donors) > 1 else 0
            donor_b = st.selectbox("🔴 Donor B", city_donors, index=default_b, key="donor_b")
        
        if donor_a == donor_b:
            st.warning("Please select two different donors.")
        else:
            # Build and show map
            dist_map, dist = build_distance_map(geo, donor_a, donor_b)
            
            # Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Distance", f"{dist:.3f} miles")
            c2.metric("Distance (feet)", f"{dist * 5280:,.0f} ft")
            batchable = "✅ Yes" if dist <= 0.5 else "❌ No"
            c3.metric("Batchable (< 0.5 mi)?", batchable)
            
            # Check same-day overlap
            df_dates = df[["Donor Name", "Rescue Date"]].drop_duplicates()
            dates_a = set(df_dates[df_dates["Donor Name"] == donor_a]["Rescue Date"])
            dates_b = set(df_dates[df_dates["Donor Name"] == donor_b]["Rescue Date"])
            same_day = len(dates_a & dates_b)
            
            st.markdown(f"**Same-day pickup overlaps:** {same_day:,} days")
            if dist <= 0.5 and same_day > 0:
                st.success(f"💰 These donors could have saved **${same_day * 15:,}** if batched (at $15/trip).")
            elif dist > 0.5:
                st.info("These donors are too far apart for efficient batching.")
            
            # Map
            st.subheader("🗺️ Map")
            st_folium(dist_map, width=None, height=500, use_container_width=True)
            
            # Details
            with st.expander("📋 Donor Details"):
                row_a = geo[geo["Donor Name"] == donor_a].iloc[0]
                row_b = geo[geo["Donor Name"] == donor_b].iloc[0]
                dc1, dc2 = st.columns(2)
                with dc1:
                    st.markdown(f"**🔵 {donor_a}**")
                    st.markdown(f"Address: {row_a.get('Donor Address', 'N/A')}")
                    st.markdown(f"City: {row_a.get('Donor City', 'N/A')}")
                    st.markdown(f"Lat/Lon: {row_a['latitude']:.6f}, {row_a['longitude']:.6f}")
                with dc2:
                    st.markdown(f"**🔴 {donor_b}**")
                    st.markdown(f"Address: {row_b.get('Donor Address', 'N/A')}")
                    st.markdown(f"City: {row_b.get('Donor City', 'N/A')}")
                    st.markdown(f"Lat/Lon: {row_b['latitude']:.6f}, {row_b['longitude']:.6f}")

# Footer
st.sidebar.divider()
st.sidebar.markdown("**JPMC Data for Good Hackathon**")
st.sidebar.markdown("Team 8 — Rescuing Leftover Cuisine")
st.sidebar.markdown(f"Data: {len(df):,} rescues | {len(geo)} geocoded donors")
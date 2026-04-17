"""Build Folium maps for Streamlit (donors, recipients, flows, heat)."""

from __future__ import annotations

import math

import folium
import pandas as pd
from folium.plugins import HeatMap, MarkerCluster

from rlc_data import aggregate_donor_hotspots, aggregate_flows, aggregate_recipient_sites
from rlc_geo import lookup_zips

# Rough city centers if no points
_CITY_CENTER = {
    "Boston": (42.36, -71.06),
    "Chicago": (41.88, -87.63),
    "Los Angeles": (34.05, -118.25),
    "New York City": (40.71, -74.01),
}


def _base_map(center_lat: float, center_lon: float, zoom: int = 11) -> folium.Map:
    return folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB positron",
    )


def map_routes_and_sites(
    hist: pd.DataFrame,
    city: str,
    top_flows: int = 100,
    min_flow_lbs: float = 25,
) -> folium.Map:
    flows = aggregate_flows(hist, city)
    flows = flows[flows["total_lbs"] >= min_flow_lbs].head(top_flows)
    if flows.empty:
        lat, lon = _CITY_CENTER.get(city, (40.7, -74.0))
        m = _base_map(lat, lon, zoom=10)
        folium.Marker([lat, lon], tooltip="No flows for filters — relax min lbs").add_to(m)
        return m

    zips = list(set(flows["donor_zip"].astype(str)) | set(flows["recipient_zip"].astype(str)))
    coord = lookup_zips(zips)
    if coord.empty:
        lat, lon = _CITY_CENTER.get(city, (40.7, -74.0))
        return _base_map(lat, lon, zoom=10)

    z = coord.set_index("zip")
    lat0, lon0 = coord["latitude"].mean(), coord["longitude"].mean()
    m = _base_map(lat0, lon0, zoom=11)

    donor_totals = aggregate_donor_hotspots(hist, city).set_index("donor_zip")["total_lbs"]
    rec_totals = aggregate_recipient_sites(hist, city).set_index("recipient_zip")["total_lbs"]

    donors_mc = MarkerCluster(name="Donors (pickups)").add_to(m)
    rec_mc = MarkerCluster(name="Recipients (dropoffs)").add_to(m)

    shown_d = set()
    shown_r = set()
    for _, row in flows.iterrows():
        dz, rz = str(row["donor_zip"]), str(row["recipient_zip"])
        if dz in z.index and dz not in shown_d:
            shown_d.add(dz)
            lbs = float(donor_totals.get(dz, row["total_lbs"]))
            r = max(4, min(28, 5 + math.sqrt(lbs / 50)))
            folium.CircleMarker(
                location=[z.loc[dz, "latitude"], z.loc[dz, "longitude"]],
                radius=r,
                color="#1a7f37",
                fill=True,
                fill_color="#34c759",
                fill_opacity=0.55,
                weight=1,
                popup=folium.Popup(f"<b>Donor ZIP {dz}</b><br/>~{lbs:,.0f} lbs (city total)", max_width=220),
            ).add_to(donors_mc)
        if rz in z.index and rz not in shown_r:
            shown_r.add(rz)
            lbs = float(rec_totals.get(rz, row["total_lbs"]))
            r = max(4, min(28, 5 + math.sqrt(lbs / 50)))
            folium.CircleMarker(
                location=[z.loc[rz, "latitude"], z.loc[rz, "longitude"]],
                radius=r,
                color="#1e5aa8",
                fill=True,
                fill_color="#5ac8fa",
                fill_opacity=0.55,
                weight=1,
                popup=folium.Popup(f"<b>Recipient ZIP {rz}</b><br/>~{lbs:,.0f} lbs delivered", max_width=220),
            ).add_to(rec_mc)

        if dz in z.index and rz in z.index:
            w = max(1, min(10, math.log1p(row["total_lbs"])))
            folium.PolyLine(
                locations=[
                    [z.loc[dz, "latitude"], z.loc[dz, "longitude"]],
                    [z.loc[rz, "latitude"], z.loc[rz, "longitude"]],
                ],
                color="#555",
                weight=w,
                opacity=0.35,
                popup=f"{row['total_lbs']:,.0f} lbs | {int(row['rescues'])} rescues",
            ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def map_waste_heatmap(hist: pd.DataFrame, city: str, top_zips: int = 40) -> folium.Map:
    """Heat by donor ZIP total lbs — 'where surplus concentrates'."""
    hot = aggregate_donor_hotspots(hist, city).head(top_zips)
    if hot.empty:
        lat, lon = _CITY_CENTER.get(city, (40.7, -74.0))
        return _base_map(lat, lon, zoom=10)

    zips = hot["donor_zip"].astype(str).tolist()
    coord = lookup_zips(zips)
    if coord.empty:
        lat, lon = _CITY_CENTER.get(city, (40.7, -74.0))
        return _base_map(lat, lon, zoom=10)

    merged = hot.merge(coord, left_on="donor_zip", right_on="zip", how="inner")
    lat0, lon0 = merged["latitude"].mean(), merged["longitude"].mean()
    m = _base_map(lat0, lon0, zoom=11)

    heat_data = [
        [row.latitude, row.longitude, max(0.1, float(row.total_lbs))]
        for row in merged.itertuples()
    ]
    HeatMap(heat_data, min_opacity=0.35, radius=28, blur=22, max_zoom=12).add_to(m)

    for row in merged.itertuples():
        folium.CircleMarker(
            location=[row.latitude, row.longitude],
            radius=max(6, min(40, math.sqrt(row.total_lbs / 30))),
            color="#c43c39",
            fill=True,
            fill_color="#ff6b6b",
            fill_opacity=0.25,
            popup=f"ZIP {row.donor_zip}<br/>{row.total_lbs:,.0f} lbs rescued",
        ).add_to(m)

    return m

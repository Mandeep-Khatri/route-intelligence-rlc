"""Shared loaders for RLC rescue CSV (no Streamlit dependency)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / "all_rescures_all_time_final_nyc_boston_la_chi.csv"

CITIES = ["Boston", "Chicago", "Los Angeles", "New York City"]


def normalize_donor_city(s):
    if pd.isna(s):
        return pd.NA
    x = str(s).strip().lower()
    x = " ".join(x.split())
    if "new york" in x or x == "nyc":
        return "New York City"
    if "boston" in x:
        return "Boston"
    if "chicago" in x:
        return "Chicago"
    if "los angeles" in x or x == "la":
        return "Los Angeles"
    return str(s).strip().title()


def clean_zip(z) -> str | None:
    if pd.isna(z):
        return None
    s = str(z).split(".")[0].strip()
    if not s.isdigit():
        return None
    return s.zfill(5)[-5:]


def donor_zip3(z) -> str | None:
    z5 = clean_zip(z)
    if not z5 or len(z5) < 3:
        return None
    return z5[:3]


def build_all_rescues_dataframe() -> pd.DataFrame:
    """All rescue rows (complete or not) for risk scoring and batching demos."""
    raw = pd.read_csv(CSV_PATH, low_memory=False)
    raw["Rescue Date"] = pd.to_datetime(raw["Rescue Date"], errors="coerce")
    raw["Pounds Rescued"] = pd.to_numeric(raw["Pounds Rescued"], errors="coerce")
    raw["Donor City"] = raw["Donor City"].map(normalize_donor_city)
    raw["donor_zip"] = raw["Donor Zipcode"].map(clean_zip)
    raw["zip3"] = raw["Donor Zipcode"].map(donor_zip3)
    raw["dow"] = raw["Rescue Date"].dt.dayofweek
    raw["dow_name"] = raw["Rescue Date"].dt.day_name()
    lead = raw["Lead Rescuer Name"].fillna("").astype(str).str.strip()
    raw["has_driver_assigned"] = lead.str.len() > 2
    return raw


def build_historical_dataframe() -> pd.DataFrame:
    """Finished rescues with cleaned zips and cities (through today)."""
    raw = pd.read_csv(CSV_PATH, low_memory=False)
    raw["Rescue Date"] = pd.to_datetime(raw["Rescue Date"], errors="coerce")
    raw["Pounds Rescued"] = pd.to_numeric(raw["Pounds Rescued"], errors="coerce")
    raw["Donor City"] = raw["Donor City"].map(normalize_donor_city)

    done = raw[raw["Rescue is Finished"]].copy()
    done = done[done["Pounds Rescued"].notna() & (done["Pounds Rescued"] >= 0)]
    as_of = pd.Timestamp.today().normalize()
    hist = done[done["Rescue Date"] <= as_of].copy()

    hist["donor_zip"] = hist["Donor Zipcode"].map(clean_zip)
    hist["recipient_zip"] = hist["Recipient Zipcode"].map(clean_zip)
    hist["zip3"] = hist["Donor Zipcode"].map(donor_zip3)
    return hist


def aggregate_flows(hist: pd.DataFrame, city: str | None = None) -> pd.DataFrame:
    h = hist if city is None else hist[hist["Donor City"] == city].copy()
    g = (
        h.dropna(subset=["donor_zip", "recipient_zip"])
        .groupby(["Donor City", "donor_zip", "recipient_zip"], dropna=False)
        .agg(total_lbs=("Pounds Rescued", "sum"), rescues=("Pounds Rescued", "count"))
        .reset_index()
        .sort_values("total_lbs", ascending=False)
    )
    return g


def aggregate_donor_hotspots(hist: pd.DataFrame, city: str | None = None) -> pd.DataFrame:
    h = hist if city is None else hist[hist["Donor City"] == city].copy()
    return (
        h.dropna(subset=["donor_zip"])
        .groupby(["Donor City", "donor_zip"])
        .agg(total_lbs=("Pounds Rescued", "sum"), rescues=("Pounds Rescued", "count"))
        .reset_index()
        .sort_values("total_lbs", ascending=False)
    )


def aggregate_recipient_sites(hist: pd.DataFrame, city: str | None = None) -> pd.DataFrame:
    h = hist if city is None else hist[hist["Donor City"] == city].copy()
    return (
        h.dropna(subset=["recipient_zip"])
        .groupby(["Donor City", "recipient_zip"])
        .agg(total_lbs=("Pounds Rescued", "sum"), rescues=("Pounds Rescued", "count"))
        .reset_index()
        .sort_values("total_lbs", ascending=False)
    )

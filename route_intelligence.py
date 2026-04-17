"""Route batching, restaurant value math, and rescue-risk signals from historical rescues."""

from __future__ import annotations

import numpy as np
import pandas as pd

DOW_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def batching_opportunities_for_day(
    hist: pd.DataFrame,
    city: str,
    day: pd.Timestamp,
    *,
    min_stops_in_zip3: int = 2,
) -> pd.DataFrame:
    """Same-day, same-ZIP3 clusters from *finished* history (corridor proxy)."""
    d = hist[(hist["Donor City"] == city) & (hist["Rescue Date"].dt.normalize() == day.normalize())].copy()
    if d.empty:
        return pd.DataFrame()
    if "zip3" not in d.columns and "donor_zip" in d.columns:
        d["zip3"] = d["donor_zip"].map(lambda z: z[:3] if z and len(z) >= 3 else None)

    d = d.dropna(subset=["zip3"])
    g = (
        d.groupby("zip3", dropna=False)
        .agg(
            rescues=("Pounds Rescued", "count"),
            total_lbs=("Pounds Rescued", "sum"),
            unique_donors=("Donor Name", pd.Series.nunique),
        )
        .reset_index()
    )
    g = g[g["rescues"] >= min_stops_in_zip3].sort_values("rescues", ascending=False)
    return g


def batching_savings_table(
    batches: pd.DataFrame,
    *,
    cost_per_solo_trip: float,
    cost_per_extra_stop: float,
) -> pd.DataFrame:
    """If each rescue were its own trip vs one routed trip with add-on stops."""
    if batches.empty:
        return batches
    out = batches.copy()
    out["solo_trips_cost"] = out["rescues"] * cost_per_solo_trip
    out["batched_route_cost"] = cost_per_solo_trip + (out["rescues"] - 1) * cost_per_extra_stop
    out["est_savings_usd"] = out["solo_trips_cost"] - out["batched_route_cost"]
    out["trips_eliminated"] = out["rescues"] - 1
    return out


def restaurant_value_summary(
    *,
    pounds: float,
    rlc_fee_usd: float,
    disposal_proxy_per_lb: float,
) -> dict:
    waste_avoided = pounds * disposal_proxy_per_lb
    net_vs_landfill = waste_avoided - rlc_fee_usd
    return {
        "pounds": pounds,
        "rlc_fee_usd": rlc_fee_usd,
        "waste_cost_avoided_proxy": waste_avoided,
        "net_vs_landfill_proxy": net_vs_landfill,
        "fee_as_pct_of_avoided": (rlc_fee_usd / waste_avoided * 100) if waste_avoided > 0 else np.nan,
    }


def build_dow_risk_profile(all_df: pd.DataFrame, city: str | None = None) -> pd.DataFrame:
    """Incomplete rate by city × day-of-week."""
    d = all_df if city is None else all_df[all_df["Donor City"] == city].copy()
    d = d[d["Rescue Date"].notna() & d["dow"].notna()]
    g = (
        d.groupby(["Donor City", "dow"], dropna=False)
        .agg(
            records=("Rescue is Finished", "count"),
            completed=("Rescue is Finished", "sum"),
        )
        .reset_index()
    )
    g["incomplete_rate"] = 1.0 - (g["completed"] / g["records"].replace(0, np.nan))
    g["dow_name"] = g["dow"].astype(int).map(lambda i: DOW_NAMES[i] if 0 <= i < 7 else "")
    return g.sort_values(["Donor City", "dow"])


def build_zip3_risk_profile(all_df: pd.DataFrame, city: str, min_n: int = 40) -> pd.DataFrame:
    d = all_df[(all_df["Donor City"] == city) & all_df["zip3"].notna()].copy()
    g = (
        d.groupby("zip3", dropna=False)
        .agg(
            records=("Rescue is Finished", "count"),
            completed=("Rescue is Finished", "sum"),
        )
        .reset_index()
    )
    g = g[g["records"] >= min_n].copy()
    g["incomplete_rate"] = 1.0 - (g["completed"] / g["records"])
    return g.sort_values("incomplete_rate", ascending=False)


def build_driver_gap_profile(all_df: pd.DataFrame, city: str | None = None, min_n: int = 200) -> pd.DataFrame:
    """Incomplete rate when no lead rescuer name vs when assigned (dataset is usually always assigned)."""
    d = all_df if city is None else all_df[all_df["Donor City"] == city].copy()
    d["assigned"] = d["has_driver_assigned"]
    g = (
        d.groupby(["Donor City", "assigned"], dropna=False)
        .agg(
            records=("Rescue is Finished", "count"),
            completed=("Rescue is Finished", "sum"),
        )
        .reset_index()
    )
    g = g[g["records"] >= min_n]
    g["incomplete_rate"] = 1.0 - (g["completed"] / g["records"])
    return g


def risk_tier(incomplete_rate: float) -> str:
    if incomplete_rate >= 0.45:
        return "High"
    if incomplete_rate >= 0.30:
        return "Elevated"
    if incomplete_rate >= 0.20:
        return "Watch"
    return "Typical"


def schedule_pickup_risk(
    *,
    city: str,
    dow: int,
    zip3: str,
    driver_assigned: bool,
    dow_table: pd.DataFrame,
    zip3_table: pd.DataFrame,
) -> dict:
    """Blend signals for a hypothetical scheduled pickup."""
    row_d = dow_table[(dow_table["Donor City"] == city) & (dow_table["dow"] == dow)]
    ir_d = float(row_d["incomplete_rate"].iloc[0]) if len(row_d) else 0.25

    zt = zip3_table[zip3_table["zip3"] == zip3]
    ir_z = float(zt["incomplete_rate"].iloc[0]) if len(zt) else ir_d

    # Weight ZIP3 when we have a specific estimate; else lean on DOW
    blended = 0.55 * ir_z + 0.45 * ir_d
    if not driver_assigned:
        blended = min(0.95, blended + 0.12)

    return {
        "blended_incomplete_rate": round(blended, 3),
        "tier": risk_tier(blended),
        "dow_incomplete_rate": round(ir_d, 3),
        "zip3_incomplete_rate": round(ir_z, 3) if len(zt) else None,
    }


def top_open_pickups(all_df: pd.DataFrame, city: str | None = None, limit: int = 15) -> pd.DataFrame:
    """Recent rows that are not finished — ops follow-up list (demo)."""
    d = all_df[~all_df["Rescue is Finished"]].copy()
    if city:
        d = d[d["Donor City"] == city]
    d = d.sort_values("Rescue Date", ascending=False).head(limit)
    cols = [
        "Rescue Date",
        "Donor City",
        "Donor Name",
        "donor_zip",
        "Pounds Rescued",
        "dow_name",
        "has_driver_assigned",
    ]
    cols = [c for c in cols if c in d.columns]
    return d[cols]

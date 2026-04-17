"""Saved analytics figures from the Jupyter pipeline."""

from pathlib import Path

import streamlit as st

from platform_ui import hero, inject_custom_css

BASE = Path(__file__).resolve().parents[1]
FIG_DIR = BASE / "figures"

st.set_page_config(page_title="Charts", page_icon="📈", layout="wide")
inject_custom_css()

hero(
    "Charts & insights",
    "Notebook outputs — regenerate from `rlc_hackathon_analysis.ipynb` when data changes.",
    overline="Analytics · Historical rescues",
)

FIGURES = [
    ("01_monthly_pounds_by_city.png", "Monthly food volume by city"),
    ("02_seasonality_index.png", "Seasonality vs average month"),
    ("03_top_donor_types.png", "Donor types by total pounds"),
    ("04_top_donors_recipients.png", "Top donors and recipients"),
    ("05_dow_peaks_by_city.png", "Weekday demand peaks"),
    ("06_batching_share_by_city.png", "Same-day ZIP3 batching share"),
]

for fname, cap in FIGURES:
    p = FIG_DIR / fname
    if p.is_file():
        st.subheader(cap)
        st.image(str(p), use_container_width=True)
    else:
        st.warning(f"Missing `{fname}` — run the analysis notebook.")

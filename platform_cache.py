"""Streamlit-cached loads (import only from Streamlit pages)."""

import streamlit as st

from rlc_data import build_historical_dataframe
from rlc_geo import lookup_zips


@st.cache_data(ttl=3600, show_spinner="Loading rescue data…")
def load_hist():
    return build_historical_dataframe()


@st.cache_data(ttl=86400, show_spinner="Looking up ZIP coordinates…")
def cached_zip_lookup(zips: tuple[str, ...]):
    return lookup_zips(list(zips))

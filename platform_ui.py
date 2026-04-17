"""Shared Streamlit styling — import and call inject_custom_css() after set_page_config."""

from __future__ import annotations

import html

import streamlit as st


def inject_custom_css() -> None:
    st.markdown(
        """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

  :root {
    --rlc-teal: #0d9488;
    --rlc-teal-dark: #0f766e;
    --rlc-teal-muted: #ccfbf1;
    --rlc-slate-900: #0f172a;
    --rlc-slate-600: #475569;
    --rlc-slate-200: #e2e8f0;
    --rlc-page: #f1f5f9;
    --rlc-card: #ffffff;
    --rlc-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 8px 24px -8px rgba(15, 23, 42, 0.08);
    --rlc-radius: 14px;
  }

  .stApp {
    background: linear-gradient(180deg, var(--rlc-page) 0%, #f8fafc 100%) !important;
  }

  section[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #ffffff 0%, #f8fafc 100%) !important;
    border-right: 1px solid var(--rlc-slate-200) !important;
  }

  section[data-testid="stSidebar"] > div {
    padding-top: 1.25rem;
  }

  [data-testid="stSidebarNav"] {
    padding-top: 0.75rem !important;
  }

  [data-testid="stSidebarNav"] li span {
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    color: var(--rlc-slate-900) !important;
  }

  [data-testid="stSidebarNav"] a:hover {
    background: rgba(13, 148, 136, 0.08) !important;
    border-radius: 8px !important;
  }

  .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1180px !important;
  }

  h1, h2, h3 {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    letter-spacing: -0.025em !important;
    color: var(--rlc-slate-900) !important;
  }

  h1 { font-weight: 700 !important; font-size: 1.75rem !important; }
  h2 { font-weight: 600 !important; color: var(--rlc-teal-dark) !important; font-size: 1.2rem !important; }
  h3 { font-weight: 600 !important; font-size: 1.05rem !important; }

  p, span, label, li {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    color: var(--rlc-slate-600);
  }

  /* Metrics */
  div[data-testid="stMetric"] {
    background: var(--rlc-card) !important;
    border: 1px solid var(--rlc-slate-200) !important;
    border-radius: var(--rlc-radius) !important;
    padding: 1rem 1.15rem !important;
    box-shadow: var(--rlc-shadow) !important;
  }

  div[data-testid="stMetric"] label {
    color: var(--rlc-teal-dark) !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
  }

  div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--rlc-slate-900) !important;
    font-weight: 700 !important;
  }

  /* Hero */
  .rlc-hero-wrap {
    margin-bottom: 1.5rem;
  }
  .rlc-hero {
    position: relative;
    background: linear-gradient(128deg, #0f766e 0%, #0d9488 42%, #14b8a6 100%);
    color: #f8fafc;
    padding: 1.75rem 2rem;
    border-radius: 18px;
    box-shadow: 0 12px 40px -14px rgba(13, 148, 136, 0.55), 0 2px 8px rgba(15, 23, 42, 0.06);
    overflow: hidden;
  }
  .rlc-hero::before {
    content: "";
    position: absolute;
    top: 0; right: 0;
    width: 45%;
    height: 100%;
    background: radial-gradient(ellipse at top right, rgba(255,255,255,0.14) 0%, transparent 65%);
    pointer-events: none;
  }
  .rlc-hero-overline {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    opacity: 0.88;
    margin-bottom: 0.5rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
  }
  .rlc-hero h1 {
    color: #ffffff !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    margin: 0 0 0.5rem 0 !important;
    line-height: 1.25 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: -0.03em !important;
  }
  .rlc-hero p {
    margin: 0;
    opacity: 0.94;
    font-size: 0.98rem;
    line-height: 1.55;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: rgba(248, 250, 252, 0.95) !important;
    max-width: 52rem;
  }

  /* Content panels */
  .rlc-panel {
    background: var(--rlc-card);
    border: 1px solid var(--rlc-slate-200);
    border-radius: var(--rlc-radius);
    padding: 1.25rem 1.4rem;
    margin: 1rem 0;
    box-shadow: var(--rlc-shadow);
  }

  .rlc-panel-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--rlc-teal-dark);
    margin-bottom: 0.75rem;
  }

  /* Buttons */
  div.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #0d9488 0%, #0f766e 100%) !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 0.5rem 1.15rem !important;
    box-shadow: 0 2px 6px rgba(13, 148, 136, 0.35) !important;
  }
  div.stButton > button[kind="primary"]:hover {
    background: #115e59 !important;
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.4) !important;
  }
  div.stButton > button[kind="secondary"] {
    border-radius: 10px !important;
    font-weight: 500 !important;
    border-color: var(--rlc-slate-200) !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #e2e8f0;
    padding: 5px;
    border-radius: 12px;
    border: none !important;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    padding: 0.45rem 1rem !important;
  }
  .stTabs [aria-selected="true"] {
    background: #ffffff !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.1) !important;
    color: var(--rlc-teal-dark) !important;
  }

  /* Inputs */
  .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
    border-radius: 10px !important;
    border-color: var(--rlc-slate-200) !important;
  }

  /* Dataframes */
  div[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--rlc-slate-200) !important;
    box-shadow: var(--rlc-shadow) !important;
  }

  /* Alerts */
  div[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: 1px solid var(--rlc-slate-200) !important;
  }

  /* Do not use overflow:hidden — it clips Streamlit’s expander summary row and can overlap
     the label with the collapse icon (Material font sometimes falls back to text like _arrow_right_). */
  [data-testid="stExpander"] {
    border: 1px solid var(--rlc-slate-200) !important;
    border-radius: 12px !important;
    background: #ffffff !important;
    overflow: visible !important;
  }
  [data-testid="stExpander"] details > summary {
    align-items: center !important;
  }

  /* Streamlit chrome */
  footer { visibility: hidden; height: 0; }
  header[data-testid="stHeader"] {
    background: rgba(255,255,255,0.85) !important;
    backdrop-filter: blur(8px);
  }
</style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, overline: str = "Rescuing Leftover Cuisine · Impact") -> None:
    t = html.escape(title)
    s = html.escape(subtitle)
    o = html.escape(overline)
    st.markdown(
        f'<div class="rlc-hero-wrap"><div class="rlc-hero">'
        f'<div class="rlc-hero-overline">{o}</div>'
        f"<h1>{t}</h1><p>{s}</p></div></div>",
        unsafe_allow_html=True,
    )


def panel_title(text: str) -> None:
    st.markdown(f'<div class="rlc-panel-title">{html.escape(text)}</div>', unsafe_allow_html=True)


def sidebar_brand(app_name: str = "RLC Platform", tagline: str = "Food rescue intelligence") -> None:
    """Call inside `with st.sidebar:` on the home page (optional on others)."""
    st.markdown(
        f"""
<div style="
  font-family: 'Plus Jakarta Sans', sans-serif;
  padding: 0.25rem 0 1rem 0;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 0.75rem;
">
  <div style="font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em; color: #0d9488; text-transform: uppercase;">{html.escape(tagline)}</div>
  <div style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-top: 0.25rem;">{html.escape(app_name)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

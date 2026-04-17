"""Scheduling board: post surplus pickups, driver/rider offers, savings estimates."""

import pandas as pd
import streamlit as st

from platform_marketplace import (
    add_offer,
    add_pickup,
    clear_all_demo,
    load_state,
    mask_contact,
)
from platform_ui import hero, inject_custom_css, sidebar_brand
from rlc_data import CITIES

st.set_page_config(
    page_title="Scheduling & marketplace",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()

hero(
    "Scheduling & community logistics",
    "Donors post surplus (lbs + window). Drivers and riders offer capacity. "
    "Everyone sees rough landfill-cost savings vs a rescue trip — a transparent, nonprofit-friendly board.",
    overline="Logistics · Coordination board",
)

st.caption(
    "Persisted locally to `data/marketplace.json`. Production would use a secure database, auth, and notifications."
)

with st.sidebar:
    sidebar_brand("Scheduling", "Coordinate pickups")
    st.subheader("Savings assumptions")
    disposal = st.number_input(
        "Landfill / hauling proxy ($/lb)",
        min_value=0.0,
        value=0.35,
        step=0.05,
        help="Used when posting a pickup to estimate avoided waste cost.",
        key="mp_disposal",
    )
    trip_default = st.number_input(
        "Typical rescue trip cost ($)",
        min_value=0.0,
        value=35.0,
        step=5.0,
        help="Your estimate for gas/time or stipend for one run.",
        key="mp_trip",
    )
    st.divider()
    if st.button("Clear all demo posts", type="secondary"):
        clear_all_demo()
        st.success("Cleared.")
        st.rerun()

tab_a, tab_b, tab_c = st.tabs(["Post pickup", "Offer a ride", "Live board"])

with tab_a:
    st.markdown("##### Food available — pounds & pickup window")
    c1, c2 = st.columns(2)
    with c1:
        biz = st.text_input("Business / site name", placeholder="e.g. Riverside Kitchen")
        city_p = st.selectbox("City", CITIES, key="pcity")
        zip_p = st.text_input("Donor ZIP", placeholder="02116", max_chars=5)
    with c2:
        lbs = st.number_input("Pounds available", min_value=1.0, value=75.0, step=5.0)
        win = st.text_input("Pickup window", placeholder="Fri 2–5pm, loading dock B")
        trip_p = st.number_input(
            "Expected trip cost to clear this load ($)",
            min_value=0.0,
            value=float(trip_default),
            step=5.0,
            key="trip_pickup",
        )
    contact_p = st.text_input("Contact (email/phone) — shown masked on board", placeholder="ops@restaurant.com")

    waste_est = lbs * disposal
    net_est = waste_est - trip_p
    m1, m2, m3 = st.columns(3)
    m1.metric("Avoided landfill cost (proxy)", f"${waste_est:,.0f}")
    m2.metric("Rescue trip (your estimate)", f"${trip_p:,.0f}")
    m3.metric("Net vs throwing away (proxy)", f"${net_est:,.0f}")

    if st.button("Publish pickup", type="primary", key="pub_pickup"):
        if not zip_p.strip().isdigit() or len(zip_p.strip()) > 5:
            st.error("Enter a numeric ZIP (e.g. 02116).")
        else:
            add_pickup(
                business=biz,
                city=city_p,
                zip_code=zip_p.strip().zfill(5)[-5:],
                pounds=lbs,
                window=win,
                contact=contact_p,
                disposal_per_lb=disposal,
                trip_cost_estimate=trip_p,
            )
            st.success("Pickup posted to the live board.")
            st.balloons()
            st.rerun()

with tab_b:
    st.markdown("##### Driver / rider — offer capacity")
    c1, c2 = st.columns(2)
    with c1:
        dname = st.text_input("Your name or team", placeholder="Alex M.")
        dcity = st.selectbox("Primary city", CITIES, key="dcity")
        cap = st.number_input("Max lbs you can move (one run)", min_value=10.0, value=150.0, step=10.0)
    with c2:
        dwin = st.text_input("When you're available", placeholder="Sat mornings, Sun after 4pm")
        dnotes = st.text_area("Vehicle / notes", placeholder="SUV with coolers", height=68)
    dcontact = st.text_input("Contact — shown masked", placeholder="555-0100", key="dcontact")

    st.info(
        "**Impact framing:** every run you cover helps a business **avoid waste fees** and gets meals "
        "to nonprofits — the board shows **$ proxy** next to each pickup so donors see the value of rescue."
    )
    ex_lbs = 75.0
    ex_save = ex_lbs * disposal
    st.metric(
        "Example donor savings (proxy)",
        f"${ex_save:,.0f}",
        help=f"If you clear ~{ex_lbs:.0f} lbs vs landfill at ${disposal}/lb (sidebar).",
    )

    if st.button("Publish offer", type="primary", key="pub_offer"):
        add_offer(
            name=dname,
            city=dcity,
            capacity_lbs=cap,
            window=dwin,
            contact=dcontact,
            notes=dnotes,
        )
        st.success("Your offer is live on the board.")
        st.rerun()

with tab_c:
    st.markdown("##### Open pickups")
    state = load_state()
    pickups = state.get("pickups", [])
    if not pickups:
        st.info("No pickups yet — post one in the first tab.")
    else:
        df_p = pd.DataFrame(pickups)
        show = df_p[
            [
                "created",
                "business",
                "city",
                "zip",
                "pounds",
                "window",
                "waste_cost_proxy_usd",
                "trip_cost_estimate_usd",
                "net_vs_landfill_proxy_usd",
                "status",
            ]
        ].copy()
        show["contact"] = df_p["contact"].map(mask_contact)
        st.dataframe(show, use_container_width=True, hide_index=True)

    st.markdown("##### Driver & rider offers")
    offers = state.get("offers", [])
    if not offers:
        st.info("No offers yet — volunteers can post in the second tab.")
    else:
        df_o = pd.DataFrame(offers)
        show_o = df_o[
            ["created", "name", "city", "capacity_lbs", "window", "notes", "status"]
        ].copy()
        show_o["contact"] = df_o["contact"].map(mask_contact)
        st.dataframe(show_o, use_container_width=True, hide_index=True)

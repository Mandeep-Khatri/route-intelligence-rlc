"""Route batching engine, restaurant value dashboard, rescue risk flagging."""

import pandas as pd
import streamlit as st

from platform_cache import load_hist
from platform_ui import hero, inject_custom_css, sidebar_brand
from rlc_data import CITIES, build_all_rescues_dataframe
from route_intelligence import (
    batching_opportunities_for_day,
    batching_savings_table,
    build_dow_risk_profile,
    build_driver_gap_profile,
    build_zip3_risk_profile,
    restaurant_value_summary,
    risk_tier,
    schedule_pickup_risk,
    top_open_pickups,
)

st.set_page_config(page_title="Route Intelligence", page_icon="🧭", layout="wide")
inject_custom_css()


@st.cache_data(ttl=3600, show_spinner="Loading full rescue log…")
def load_all_rescues():
    """Defined here so this page works even if an older `platform_cache.py` is missing this helper."""
    return build_all_rescues_dataframe()


hero(
    "Route Intelligence",
    "Batch nearby same-day pickups, show restaurant savings vs fees, and flag historically risky slots — "
    "grounded in RLC’s four-city rescue log.",
    overline="Operations · RLC platform",
)

hist = load_hist()
all_df = load_all_rescues()

tab_batch, tab_rest, tab_risk = st.tabs(
    ["Route batching engine", "Restaurant value dashboard", "Rescue risk flagging"]
)

# --------------------------------------------------------------------------- batching
with tab_batch:
    st.markdown(
        "When pickups land on the **same day** in the **same ZIP3 corridor** (geographic proxy), "
        "the engine groups them into **one routed run** instead of many solo trips — cutting RLC **per-rescue cost** "
        "so savings can support **restaurants** or **driver stipends**."
    )
    c1, c2, c3 = st.columns(3)
    city_b = c1.selectbox("Metro", CITIES, key="batch_city")
    solo_cost = c2.number_input("Cost if each rescue is its own trip ($)", 5.0, 80.0, 17.5, 0.5)
    extra_stop = c3.number_input("Marginal cost per extra stop on same route ($)", 0.0, 30.0, 5.0, 0.5)

    sub = hist[hist["Donor City"] == city_b]
    day_counts = sub.groupby(sub["Rescue Date"].dt.date).size().sort_values(ascending=False).head(40)
    sample_days = list(day_counts.index)
    if not sample_days:
        st.warning("No historical data for this city.")
    else:
        default_d = sample_days[0]
        pick = st.selectbox(
            "Sample calendar day (from high-volume history)",
            options=sample_days,
            format_func=lambda d: f"{d} · {int(day_counts[d])} finished rescues",
            index=0,
        )
        day_ts = pd.Timestamp(pick)
        batches = batching_opportunities_for_day(hist, city_b, day_ts, min_stops_in_zip3=2)
        if batches.empty:
            st.info("No same-day ZIP3 clusters with 2+ stops on this date — try another sample day.")
        else:
            enriched = batching_savings_table(
                batches, cost_per_solo_trip=solo_cost, cost_per_extra_stop=extra_stop
            )
            total_save = enriched["est_savings_usd"].sum()
            trips_cut = int(enriched["trips_eliminated"].sum())
            m1, m2, m3 = st.columns(3)
            m1.metric("ZIP3 batch groups that day", len(enriched))
            m2.metric("Trips eliminated (upper bound)", trips_cut)
            m3.metric("Est. same-day savings (proxy)", f"${total_save:,.0f}")
            st.dataframe(
                enriched.rename(
                    columns={
                        "zip3": "ZIP3 corridor",
                        "rescues": "Rescues (stops)",
                        "total_lbs": "Total lbs",
                        "unique_donors": "Unique donors",
                        "solo_trips_cost": "If solo ($)",
                        "batched_route_cost": "If batched ($)",
                        "est_savings_usd": "Savings ($)",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "ZIP3 ≈ USPS sectional center — a practical batching proxy without street routing. "
                "Production would use drive-time matrices and time windows."
            )

# --------------------------------------------------------------------------- restaurant value
with tab_rest:
    st.markdown(
        "When a donor schedules a pickup, show **landfill / hauling cost avoided** next to the **RLC fee** "
        "so partners see **net savings**, not just an invoice line."
    )
    r1, r2, r3 = st.columns(3)
    lbs_r = r1.number_input("Food available (lbs)", 1.0, 5000.0, 120.0, 5.0, key="rv_lbs")
    fee_r = r2.number_input("RLC pickup fee ($)", 0.0, 500.0, 30.0, 5.0, key="rv_fee")
    disp_r = r3.number_input("Your waste disposal proxy ($/lb)", 0.0, 3.0, 0.35, 0.05, key="rv_disp")

    rv = restaurant_value_summary(pounds=lbs_r, rlc_fee_usd=fee_r, disposal_proxy_per_lb=disp_r)
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Waste cost avoided (proxy)", f"${rv['waste_cost_avoided_proxy']:,.0f}")
    a2.metric("RLC fee", f"${rv['rlc_fee_usd']:,.0f}")
    a3.metric("Net vs throwing away", f"${rv['net_vs_landfill_proxy']:+,.0f}")
    pct = rv["fee_as_pct_of_avoided"]
    a4.metric("Fee as % of avoided waste", f"{pct:.0f}%" if pct == pct else "—")

    if rv["net_vs_landfill_proxy"] >= 0:
        st.success(
            f"**Talking point:** Under these assumptions, the **${fee_r:.0f} fee is lower than the ~${rv['waste_cost_avoided_proxy']:.0f}** "
            "proxy disposal cost — participation is a **net win** before community impact."
        )
    else:
        st.warning(
            "Under these inputs the fee exceeds the disposal proxy — tune **$/lb** or highlight **batching**, "
            "**tax incentives**, and **brand/community** value."
        )

# --------------------------------------------------------------------------- risk
with tab_risk:
    st.markdown(
        "Uses **150k+ records**: **incomplete-rate** patterns by **day-of-week** and **donor ZIP3** (where sample size allows). "
        "Optional **“no driver assigned yet”** bumps risk (demo lever — most historical rows have a lead name)."
    )
    city_r = st.selectbox("Metro", CITIES, key="risk_city")

    dow_full = build_dow_risk_profile(all_df, city_r)
    zip_full = build_zip3_risk_profile(all_df, city_r, min_n=40)
    driver_gap = build_driver_gap_profile(all_df, city_r, min_n=50)

    st.subheader("Simulate a scheduled pickup")
    s1, s2, s3, s4 = st.columns([1, 1, 1, 1])
    dow_i = s1.selectbox(
        "Day of week",
        options=list(range(7)),
        format_func=lambda i: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i],
        key="sim_dow",
    )
    _z0 = str(zip_full.iloc[0]["zip3"]) if len(zip_full) else "021"
    zip3_in = s2.text_input("Donor ZIP3", value=_z0[:3], max_chars=3)
    assigned = s3.checkbox("Driver assigned in system", value=True)
    s4.write("")  # spacer

    zip3_clean = zip3_in.strip().zfill(3)[-3:]
    sig = schedule_pickup_risk(
        city=city_r,
        dow=dow_i,
        zip3=zip3_clean,
        driver_assigned=assigned,
        dow_table=dow_full,
        zip3_table=zip_full,
    )
    tier = sig["tier"]
    color = {"High": "🔴", "Elevated": "🟠", "Watch": "🟡", "Typical": "🟢"}.get(tier, "")
    st.markdown(f"### {color} **Risk tier: {tier}**  ·  blended incomplete history: **{sig['blended_incomplete_rate']:.1%}**")
    if sig["zip3_incomplete_rate"] is not None:
        st.caption(
            f"ZIP3 historical incomplete: **{sig['zip3_incomplete_rate']:.1%}** · "
            f"DOW historical incomplete: **{sig['dow_incomplete_rate']:.1%}**"
        )
    else:
        st.caption(
            f"ZIP3 not in high-sample table — using DOW blend. DOW incomplete: **{sig['dow_incomplete_rate']:.1%}**"
        )

    if tier in ("High", "Elevated"):
        st.error("**Suggested ops play:** pre-assign a driver, offer a stipend bump, or split the pickup window.")
    elif tier == "Watch":
        st.warning("**Suggested ops play:** confirm driver acceptance 24h ahead; keep a backup volunteer.")
    else:
        st.info("**Suggested ops play:** standard scheduling — still confirm day-of.")

    cA, cB = st.columns(2)
    with cA:
        st.markdown("##### Highest historical friction (ZIP3)")
        show_z = zip_full.head(12).copy()
        show_z["tier"] = show_z["incomplete_rate"].map(risk_tier)
        st.dataframe(
            show_z.rename(
                columns={
                    "zip3": "ZIP3",
                    "records": "N",
                    "incomplete_rate": "Incomplete rate",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    with cB:
        st.markdown("##### Incomplete rate by weekday")
        show_d = dow_full.copy()
        show_d["tier"] = show_d["incomplete_rate"].map(risk_tier)
        st.dataframe(
            show_d[["dow_name", "records", "incomplete_rate", "tier"]].rename(
                columns={"records": "N", "incomplete_rate": "Incomplete rate"}
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("##### Recent unclosed rescues (demo queue)")
    st.dataframe(top_open_pickups(all_df, city_r, limit=12), use_container_width=True, hide_index=True)

    # Use a toggle instead of st.expander: some browsers fail to load Material icons for the
    # built-in chevron and show overlapping text like "_arrow_right_" next to the label.
    if st.toggle("Show methodology (for judges)", value=False):
        st.markdown(
            """
            - **Incomplete** = `Rescue is Finished` is false in the historical extract.
            - **ZIP3 signal** only when **at least 40** records in that city/ZIP3.
            - **Blended score** = 0.55×ZIP3 rate + 0.45×city/weekday rate; **+12 pts** if “no driver assigned” in the simulator.
            - **Tiers:** Typical under 20% incomplete, Watch 20–30%, Elevated 30–45%, High 45%+.
            - This is a **hackathon risk lens**, not a production ML model — next step is calibrated models + live dispatch state.
            """
        )

    if len(driver_gap) >= 2:
        st.caption(
            "Lead rescuer field is almost always populated in this data; "
            "“driver assigned” is still useful as a **workflow flag** in a real system."
        )

with st.sidebar:
    sidebar_brand("Route Intelligence", "Batch · Value · Risk")
    st.caption("Three modules aligned to your pitch deck.")

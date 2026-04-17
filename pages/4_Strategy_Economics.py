"""Strategy: donation + rescue vs throwing food away."""

import streamlit as st

from platform_ui import hero, inject_custom_css

st.set_page_config(page_title="Strategy & economics", page_icon="💰", layout="wide")
inject_custom_css()

hero(
    "Strategy & economics",
    "Why rescue beats the dumpster — and how RLC keeps donor costs predictable.",
    overline="Finance · Impact story",
)
st.markdown(
    """
    ### Why partner with a nonprofit (RLC) instead of “just tossing” surplus?

    **Throwing food away is not free.** Businesses often pay for **waste hauling** by weight or pickup; 
    organic bans in several jurisdictions can make landfilling food **more expensive** than routing it to reuse. 
    Spoilage also **shrinks margin** on inventory you already paid for.

    **Donating through RLC** moves food to people who need it. A **coordinated rescue** (volunteer or paid driver funded by 
    grants/donors/partners) turns random trips into **planned routes** — similar idea to how delivery platforms batch stops, 
    but for impact.

    **This is not tax or legal advice** — many donors may qualify for federal or state food-donation incentives; 
    RLC can help document **pounds moved** (your dataset already tracks that).
    """
)

st.divider()
st.subheader("Simple cost sketch (editable assumptions)")

c1, c2 = st.columns(2)
lbs = c1.number_input("Surplus food at risk this week (lbs)", min_value=0.0, value=500.0, step=50.0)
disposal = c2.number_input("Implied disposal / waste cost ($ per lb)", min_value=0.0, value=0.35, step=0.05, help="Hauling + tipping fee proxy; adjust for your market.")

c3, c4 = st.columns(2)
trip = c3.number_input("Cost to fund one rescue trip that clears this food ($)", min_value=0.0, value=35.0, step=5.0)
trips = c4.number_input("Trips needed (batching lowers this)", min_value=1, max_value=50, value=1)

waste_cost = lbs * disposal
rescue_cost = trip * trips
delta = waste_cost - rescue_cost

st.markdown("---")
m1, m2, m3 = st.columns(3)
m1.metric("Rough cost to throw away (proxy)", f"${waste_cost:,.0f}")
m2.metric("Rough cost to rescue (proxy)", f"${rescue_cost:,.0f}")
m3.metric("Difference (throw-away minus rescue)", f"${delta:,.0f}", delta=f"{delta:+,.0f} $")

if delta > 0:
    st.success(
        "Under these assumptions, **paying for rescue(s)** is cheaper than **paying waste fees** for the same weight — "
        "before counting **brand**, **community impact**, or **tax incentives**."
    )
else:
    st.warning(
        "Under these inputs, **disposal looks cheaper** — tighten **batching** (fewer trips), "
        "use **volunteer-led** rescues where possible, or adjust **$/lb** waste assumptions. "
        "Many sites under-count true waste cost (labor, bags, contamination)."
    )

st.divider()
st.subheader("Nonprofit collaboration = lower cost per donor")
st.markdown(
    """
    - **Route batching** (see Map + ZIP3 charts): fewer **trip starts** per pound.
    - **Peak staffing** (weekday charts): align drivers when surplus is predictable.
    - **One relationship, many pickups:** RLC coordinates **many donors** → **shared logistics learning** — like a platform, 
      but mission-driven and **grant-supported** so **local businesses are not “burned”** by ad-hoc courier rates.

    **Pitch to a food business:** “We’d rather pay a **small, predictable rescue fee / in-kind support** and know the food 
    feeds people than **pay the dumpster** and **lose the story**.”
    """
)

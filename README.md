# Route Intelligence for Rescuing Leftover Cuisine

Route Intelligence is a data-driven platform built to improve food rescue operations for Rescuing Leftover Cuisine (RLC).The project combines historical rescue analytics with live operational workflows to reduce routing cost, prevent missed pickups, and make donor value clearly measurable.

## What this project is for

This platform is designed to solve three core operational problems:

1. **Too many separate trips for nearby pickups**  
   Nearby same-day rescues are often handled as independent routes, increasing driver time and per-rescue cost.

2. **Donors see only a fee, not the value of rescue**  
   Restaurants may view pickup fees as an expense unless they can see the waste cost and impact they are avoiding.

3. **High-risk rescues are identified too late**  
   Without early warnings, pickups at risk of going unclaimed may be missed before intervention is possible.

## What was built

### 1) Route Batching Engine
- Detects same-day nearby pickup opportunities (ZIP3 corridor proxy).
- Estimates route consolidation potential, trips eliminated, and cost savings.
- Supports lower per-rescue logistics cost and better route efficiency.

### 2) Restaurant Value Dashboard
- Calculates waste-cost avoided versus pickup fee at scheduling time.
- Shows net value so participation is framed as savings and impact, not only cost.
- Helps improve partner adoption and retention.

### 3) Rescue Risk Flagging
- Uses historical rescue patterns to score risk by city, day-of-week, and corridor signals.
- Surfaces risk tiers (Typical, Watch, Elevated, High).
- Provides an early-warning view for operators to reassign or incentivize before food is wasted.

## Platform scope

Main application: `app.py` (Streamlit)

Pages include:
- Charts & Insights
- Map - Routes
- Waste Hotspots
- Strategy & Economics
- Scheduling & Marketplace
- Route Intelligence

Supporting modules:
- `rlc_data.py` (cleaning and feature preparation)
- `route_intelligence.py` (batching, value logic, risk scoring)
- `rlc_folium.py` and `rlc_geo.py` (map layers and ZIP geocoding)
- `platform_marketplace.py` (pickup and driver offer board persistence)

## Data used

Primary dataset:
- `all_rescures_all_time_final_nyc_boston_la_chi.csv`

Coverage includes rescue records from:
- New York City
- Boston
- Chicago
- Los Angeles

## Run locally

```bash
cd /path/to/repo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pgeocode python-pptx
streamlit run app.py
```

Open: `http://127.0.0.1:8501`

## Optional artifacts

- Analysis notebooks:
  - `rlc_hackathon_analysis.ipynb`
  - `rlc_hackathon_analysis_executed.ipynb`
- Generated visual outputs: `figures/`
- Slide deck: `RLC_Hackathon_Presentation.pptx`

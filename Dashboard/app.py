import os
import streamlit as st

st.set_page_config(
    page_title="Energy Demand & Renewables Dashboard",
    layout="wide",
)

# ---- Header ----
st.title("Energy Demand & Renewables Dashboard")
st.caption(
    "Live monitoring of electricity demand and renewable generation (wind/solar), "
    "with period comparisons and short-term load forecasting."
)

# ---- Environment / Connectivity ----
api_base = os.getenv("ENERGY_API_BASE", "http://127.0.0.1:8000")
st.info(f"Backend API: {api_base}", icon="🔗")

# ---- What the dashboard offers ----
st.subheader("What you can do here")
st.markdown(
    """
- **Live Monitoring**: Explore time series, KPI summaries (last/avg/min/max), threshold alerts, and drill-down.
- **Compare Periods**: Compare two user-selected time windows to identify changes in demand or generation patterns.
- **Energy Mix**: View demand alongside wind and solar generation to understand renewable contribution over time.
- **Forecast**: Generate short-term hourly load forecasts using a weather-enhanced model from the backend.
"""
)

# ---- How it works ----
st.subheader("Workflow (high level)")
st.markdown(
    """
1. Fetch live **energy** data (SMARD) and **weather** data (Open-Meteo) via APIs  
2. Process and store data in **PostgreSQL** (scheduled ingestion)  
3. Serve data through **FastAPI** endpoints (`/timeseries`, `/forecast`)  
4. Visualize and interact with data in **Streamlit**
"""
)

# ---- Guidance ----
st.divider()
st.markdown(
    """
**Start here:** Use the navigation on the left to open a page.  
If a page shows **no data**, trigger ingestion via the backend (`POST /ingest-now`) or select a wider date range.
"""
)

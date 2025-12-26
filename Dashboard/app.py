import streamlit as st

st.set_page_config(
    page_title="Energy Demand & Renewables Dashboard",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Energy Demand & Renewables Dashboard (Live + Forecast)")
st.caption("Dashboard-first build. Backend API will be plugged in next.")

st.markdown(
"""
**Pages**
- **Live Monitoring:** interactive time series + KPIs + thresholds  
- **Compare Periods:** compare two time windows (e.g., this week vs last week)  
- **Forecast:** placeholder to show how we’ll visualize `/forecast` outputs  
"""
)

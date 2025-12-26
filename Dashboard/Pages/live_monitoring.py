import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dateutil import tz
import requests
from streamlit_autorefresh import st_autorefresh

from utils import REGIONS, METRICS, RESOLUTIONS, get_timeseries, pretty_unit

# Auto-refresh (live feel): refresh page every 60 seconds
st_autorefresh(interval=60 * 1000, key="live_refresh")

st.header("📈 Live Monitoring")
st.caption("Live view updates automatically. Data availability depends on source publication delay (SMARD).")

API_BASE = os.getenv("ENERGY_API_BASE", "http://127.0.0.1:8000").rstrip("/")

# Sidebar controls (advanced interactions)
with st.sidebar:
    st.subheader("Controls")
    st.caption("Data Mode: API only")

    region = st.selectbox("Region", REGIONS, index=0)
    metric_label = st.selectbox("Metric", list(METRICS.keys()), index=0)
    metric_key = METRICS[metric_label]
    resolution = st.selectbox("Resolution", RESOLUTIONS, index=1)

    berlin = tz.gettz("Europe/Berlin")
    end = pd.Timestamp.now(tz=berlin).floor("h")
    start_default = end - pd.Timedelta(days=7)
    start = st.date_input("Start date", value=start_default.date())
    end_date = st.date_input("End date", value=end.date())

    # Convert to timestamps
    start_ts = pd.Timestamp(start, tz=berlin)
    end_ts = pd.Timestamp(end_date, tz=berlin) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    st.divider()

    # Manual "ingest now" button for demo/live control
    if st.button("⚡ Ingest latest data now"):
        try:
            r = requests.post(f"{API_BASE}/ingest-now", timeout=120)
            if r.status_code == 200:
                st.success("Ingestion triggered. Page will refresh automatically.")
            else:
                st.error(f"Ingest failed ({r.status_code}): {r.text[:200]}")
        except Exception as e:
            st.error(f"Could not trigger ingestion: {e}")

    st.divider()
    st.subheader("Alert threshold")
    threshold_on = st.checkbox("Enable threshold alert", value=False)
    threshold = st.number_input(
        "Threshold value",
        min_value=0.0,
        value=60000.0 if metric_key == "load" else 15000.0,
        step=500.0,
    )

# Data fetch (API-only)
df = get_timeseries(
    region=region,
    metric_key=metric_key,
    resolution=resolution,
    start=start_ts,
    end=end_ts,
)

if df.empty:
    st.warning("No data returned for this period. Try a different range or resolution.")
    st.stop()

# Ensure correct types/order
df["ts"] = pd.to_datetime(df["ts"])
df = df.sort_values("ts")

# Show latest ingested timestamp (helps users understand delays)
latest_ts = df["ts"].max()
st.caption(f"Latest available timestamp in DB: **{latest_ts}**")

# KPIs (computed from DataFrame)
unit = pretty_unit(metric_key)
last_val = float(df["value"].iloc[-1]) if not df.empty else None
avg_val = float(df["value"].mean()) if not df.empty else None
min_val = float(df["value"].min()) if not df.empty else None
max_val = float(df["value"].max()) if not df.empty else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("Last", f"{last_val:.1f} {unit}" if last_val is not None else "—")
c2.metric("Average", f"{avg_val:.1f} {unit}" if avg_val is not None else "—")
c3.metric("Min", f"{min_val:.1f} {unit}" if min_val is not None else "—")
c4.metric("Max", f"{max_val:.1f} {unit}" if max_val is not None else "—")

# Plot (interactive zoom/brush built-in with Plotly)
fig = px.line(df, x="ts", y="value", title=f"{metric_label} — {region} ({resolution})")
fig.update_layout(xaxis_title="Time", yaxis_title=f"Value ({unit})")
st.plotly_chart(fig, use_container_width=True)

# Threshold highlighting
if threshold_on:
    exceed = df[df["value"] > threshold].copy()
    st.subheader("🚨 Threshold exceedances")
    st.write(f"Threshold: **{threshold:.1f} {unit}**")

    if exceed.empty:
        st.success("No exceedances in the selected time window.")
    else:
        st.error(f"Found **{len(exceed)}** exceedance points.")
        st.dataframe(exceed.sort_values("ts", ascending=False), use_container_width=True)

# Drill-down (advanced interaction): pick a time window inside the selected range
st.subheader("🔎 Drill-down (focus window)")
colA, colB = st.columns(2)
with colA:
    focus_start = st.date_input("Focus start (date)", value=start_ts.date(), key="focus_start")
with colB:
    focus_end = st.date_input(
        "Focus end (date)",
        value=min(end_ts.date(), (start_ts + pd.Timedelta(days=2)).date()),
        key="focus_end",
    )

focus_start_ts = pd.Timestamp(focus_start, tz=berlin)
focus_end_ts = pd.Timestamp(focus_end, tz=berlin) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

df_focus = df[(df["ts"] >= focus_start_ts) & (df["ts"] <= focus_end_ts)]
if df_focus.empty:
    st.info("No data in the focus window.")
else:
    fig2 = px.area(df_focus, x="ts", y="value", title="Focused view")
    fig2.update_layout(xaxis_title="Time", yaxis_title=f"Value ({unit})")
    st.plotly_chart(fig2, use_container_width=True)

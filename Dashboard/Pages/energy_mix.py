import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from dateutil import tz

from utils import get_timeseries

st.header("🌍 Energy Mix (Renewables vs Conventional)")

with st.sidebar:
    mode = "api"
    st.caption("Data Mode: API only")


    berlin = tz.gettz("Europe/Berlin")
    end = pd.Timestamp.now(tz=berlin).floor("H")
    start_default = end - pd.Timedelta(days=7)

    start = st.date_input("Start date", value=start_default.date(), key="mix_start")
    end_date = st.date_input("End date", value=end.date(), key="mix_end")

    start_ts = pd.Timestamp(start, tz=berlin)
    end_ts = pd.Timestamp(end_date, tz=berlin) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    st.divider()
    st.subheader("Highlight")
    peak_threshold = st.slider("Peak load threshold (MW)", 30000, 90000, 65000, step=500)

# We combine multiple metrics (these will become real once API exists)
metrics = {
    "Load": "load",
    "Wind": "wind",
    "Solar": "solar",
}

dfs = {}
for label, key in metrics.items():
    dfs[label] = get_timeseries(
        region="DE",
        metric_key=key,
        resolution="hour",
        start=start_ts,
        end=end_ts,
    ).rename(columns={"value": label})

# merge on timestamp
df = dfs["Load"][["ts", "Load"]].copy()
df = df.merge(dfs["Wind"][["ts", "Wind"]], on="ts", how="inner")
df = df.merge(dfs["Solar"][["ts", "Solar"]], on="ts", how="inner")

# Compute derived columns
df["Renewables"] = df["Wind"] + df["Solar"]
df["Conventional"] = np.clip(df["Load"] - df["Renewables"], 0, None)
df["Renewables Share (%)"] = np.where(df["Load"] > 0, 100 * df["Renewables"] / df["Load"], np.nan)
df["Peak"] = df["Load"] > peak_threshold

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Avg Load (MW)", f"{df['Load'].mean():.0f}")
c2.metric("Avg Renewables Share (%)", f"{df['Renewables Share (%)'].mean():.1f}")
c3.metric("Peak Hours", f"{int(df['Peak'].sum())}")

# Stacked mix chart
mix = df.melt(id_vars=["ts"], value_vars=["Renewables", "Conventional"], var_name="Type", value_name="MW")
fig = px.area(mix, x="ts", y="MW", color="Type", title="Generation Mix (Stacked)")
st.plotly_chart(fig, use_container_width=True)

# Renewables share line
fig2 = px.line(df, x="ts", y="Renewables Share (%)", title="Renewables Share Over Time")
st.plotly_chart(fig2, use_container_width=True)

# Peak table
st.subheader("⏱ Peak Hours (Drill-down table)")
peaks = df[df["Peak"]].sort_values("ts", ascending=False)[["ts", "Load", "Renewables", "Renewables Share (%)"]]
if peaks.empty:
    st.success("No peak hours in this period for the chosen threshold.")
else:
    st.dataframe(peaks, use_container_width=True)

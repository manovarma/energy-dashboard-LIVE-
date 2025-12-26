import streamlit as st
import pandas as pd
import plotly.express as px
from dateutil import tz

from utils import REGIONS, METRICS, RESOLUTIONS, get_timeseries, pretty_unit

st.header("Compare Periods")

with st.sidebar:
    st.subheader("Compare controls")
    st.caption("Data Mode: API only")

    region = st.selectbox("Region", REGIONS, index=0, key="cmp_region")
    metric_label = st.selectbox("Metric", list(METRICS.keys()), index=0, key="cmp_metric")
    metric_key = METRICS[metric_label]
    resolution = st.selectbox("Resolution", RESOLUTIONS, index=1, key="cmp_res")

    berlin = tz.gettz("Europe/Berlin")
    now = pd.Timestamp.now(tz=berlin).floor("h")  # use "h" not "H"

    st.divider()
    st.caption("Period A")
    a_end = st.date_input("A end date", value=now.date(), key="a_end")
    a_days = st.slider("A length (days)", 1, 30, 7, key="a_days")

    # Compute Period A range (show it clearly)
    a_end_ts = pd.Timestamp(a_end, tz=berlin) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    a_start_ts = a_end_ts - pd.Timedelta(days=a_days)
    st.caption(f" Period A range: **{a_start_ts.date()} → {a_end_ts.date()}** ({a_days} days)")

    st.divider()
    st.caption("Period B")
    b_shift = st.slider("Shift B back by (days)", 1, 90, 7, key="b_shift")

    # Compute Period B range (show it clearly)
    b_end_ts = a_end_ts - pd.Timedelta(days=b_shift)
    b_start_ts = b_end_ts - pd.Timedelta(days=a_days)
    st.caption(
        f" Period B range: **{b_start_ts.date()} → {b_end_ts.date()}** "
        f"(shifted back by {b_shift} days)"
    )

# Fetch data
df_a = get_timeseries(region, metric_key, resolution, a_start_ts, a_end_ts)
df_b = get_timeseries(region, metric_key, resolution, b_start_ts, b_end_ts)

if df_a.empty or df_b.empty:
    st.warning("One of the periods returned no data. Try a different date range or resolution.")
    st.stop()

# Ensure time dtype/order
df_a = df_a.copy()
df_b = df_b.copy()
df_a["ts"] = pd.to_datetime(df_a["ts"])
df_b["ts"] = pd.to_datetime(df_b["ts"])
df_a = df_a.sort_values("ts")
df_b = df_b.sort_values("ts")

unit = pretty_unit(metric_key)

# Normalize time axis to compare shapes (relative timeline)
df_a["idx"] = range(len(df_a))
df_b["idx"] = range(len(df_b))
df_a["period"] = "A (most recent)"
df_b["period"] = f"B (-{b_shift}d shift)"

df_cmp = pd.concat([df_a, df_b], ignore_index=True)

st.caption(
    "Both periods are aligned to a **relative time axis** (index within the window) to compare the **shape/pattern**, "
    "not the calendar dates."
)

fig = px.line(
    df_cmp,
    x="idx",
    y="value",
    color="period",
    title=f"{metric_label} — normalized shape comparison ({region})",
)
fig.update_layout(
    xaxis_title="Relative time within period (index)",
    yaxis_title=f"Value ({unit})",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader(" Summary")
col1, col2 = st.columns(2)
with col1:
    st.write("**Period A**")
    st.caption(f"{a_start_ts.date()} → {a_end_ts.date()}")
    st.dataframe(df_a[["ts", "value"]].describe(), use_container_width=True)
with col2:
    st.write("**Period B**")
    st.caption(f"{b_start_ts.date()} → {b_end_ts.date()}")
    st.dataframe(df_b[["ts", "value"]].describe(), use_container_width=True)

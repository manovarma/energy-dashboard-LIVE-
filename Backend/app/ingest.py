import os
import pandas as pd
from dateutil import tz
from sqlalchemy.orm import Session

from .models import TimeSeriesPoint, WeatherPoint
from .smard_client import fetch_index, fetch_series
from .weather_client import fetch_openmeteo_hourly

BERLIN = tz.gettz("Europe/Berlin")

def _upsert_timeseries(db: Session, region: str, metric: str, resolution: str, df: pd.DataFrame):
    # simple approach: delete overlap + insert (fine for course project)
    if df.empty:
        return
    start, end = df["ts"].min(), df["ts"].max()
    db.query(TimeSeriesPoint).filter(
        TimeSeriesPoint.region == region,
        TimeSeriesPoint.metric == metric,
        TimeSeriesPoint.resolution == resolution,
        TimeSeriesPoint.ts >= start,
        TimeSeriesPoint.ts <= end,
    ).delete(synchronize_session=False)

    db.bulk_save_objects([
        TimeSeriesPoint(region=region, metric=metric, resolution=resolution, ts=row.ts, value=float(row.value))
        for row in df.itertuples(index=False)
    ])
    db.commit()

def ingest_smard_metric(db: Session, region: str, metric: str, filter_id: str, resolution: str):
    idx = fetch_index(filter_id=filter_id, region=region, resolution=resolution)

    # Extract timestamps robustly
    timestamps = []
    if isinstance(idx, dict):
        for key in ["timestamps", "data", "values"]:
            if key in idx and isinstance(idx[key], list):
                timestamps = idx[key]
                break
    elif isinstance(idx, list):
        timestamps = idx

    if not timestamps:
        return

    # ✅ Fix C: fetch last N chunks (history)
    N = 60
    for ts_chunk in timestamps[-N:]:
        ts_chunk = int(ts_chunk)

        series = fetch_series(filter_id=filter_id, region=region, resolution=resolution, timestamp=ts_chunk)

        points = series.get("series") or series.get("data") or series.get("values")
        if not points:
            continue

        df = pd.DataFrame(points, columns=["ts_ms", "value"])
        df["ts"] = pd.to_datetime(df["ts_ms"], unit="ms", utc=True)  # store as UTC
        df = df[["ts", "value"]].dropna()

        _upsert_timeseries(db, region=region, metric=metric, resolution=resolution, df=df)


def ingest_weather(db: Session, lat: float, lon: float, timezone: str = "Europe/Berlin"):
    payload = fetch_openmeteo_hourly(lat, lon, timezone=timezone)
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])

    if not times:
        return

    df = pd.DataFrame({
        "ts": pd.to_datetime(times),
        "temperature_2m": hourly.get("temperature_2m", []),
        "windspeed_10m": hourly.get("windspeed_10m", []),
        "precipitation": hourly.get("precipitation", []),
    })
    df["ts"] = df["ts"].dt.tz_localize(timezone)

    # delete overlap then insert
    start, end = df["ts"].min(), df["ts"].max()
    db.query(WeatherPoint).filter(WeatherPoint.ts >= start, WeatherPoint.ts <= end).delete(synchronize_session=False)

    db.bulk_save_objects([
        WeatherPoint(
            ts=row.ts,
            temperature_2m=None if pd.isna(row.temperature_2m) else float(row.temperature_2m),
            windspeed_10m=None if pd.isna(row.windspeed_10m) else float(row.windspeed_10m),
            precipitation=None if pd.isna(row.precipitation) else float(row.precipitation),
        )
        for row in df.itertuples(index=False)
    ])
    db.commit()

def run_ingestion(db: Session):
    regions = ["DE", "DE-LU"]   # keep only DE if you want
    resolutions = ["quarterhour", "hour", "day"]

    metric_filters = {
        "load": os.getenv("SMARD_FILTER_LOAD", ""),
        "wind": os.getenv("SMARD_FILTER_WIND", ""),
        "solar": os.getenv("SMARD_FILTER_SOLAR", ""),
    }

    for region in regions:  # ✅ loop one-by-one
        for resolution in resolutions:
            for metric, fid in metric_filters.items():
                if fid:
                    ingest_smard_metric(
                        db,
                        region=region,      # ✅ string, not list
                        metric=metric,
                        filter_id=fid,
                        resolution=resolution,
                    )

    # weather ingestion once (Berlin coords)
    lat = float(os.getenv("OPENMETEO_LAT", "52.52"))
    lon = float(os.getenv("OPENMETEO_LON", "13.405"))
    ingest_weather(db, lat=lat, lon=lon, timezone=os.getenv("TZ", "Europe/Berlin"))



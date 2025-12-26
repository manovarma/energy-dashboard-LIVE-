import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("energy_api")

import os
import pandas as pd
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

from .db import Base, engine, get_db, SessionLocal
from .models import TimeSeriesPoint, WeatherPoint
from .schemas import TSPoint, ForecastPoint
from .ingest import run_ingestion
from .forecast import train_and_forecast

app = FastAPI(title="Energy Dashboard API", version="1.0")

Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/timeseries", response_model=list[TSPoint])
def timeseries(
    region: str = Query("DE"),
    metric: str = Query(..., description="load | wind | solar"),
    resolution: str = Query("hour"),
    start: str = Query(...),
    end: str = Query(...),
    db: Session = Depends(get_db),
):
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)

    rows = (
        db.query(TimeSeriesPoint)
        .filter(TimeSeriesPoint.region == region)
        .filter(TimeSeriesPoint.metric == metric)
        .filter(TimeSeriesPoint.resolution == resolution)
        .filter(TimeSeriesPoint.ts >= start_dt)
        .filter(TimeSeriesPoint.ts <= end_dt)
        .order_by(TimeSeriesPoint.ts.asc())
        .all()
    )
    return [{"ts": r.ts, "value": r.value} for r in rows]

@app.get("/forecast", response_model=list[ForecastPoint])
def forecast(
    region: str = Query("DE"),
    horizon: int = Query(24, ge=1, le=72),
    db: Session = Depends(get_db),
):
    # Weather range (min/max) determines the usable training window
    w_range = pd.read_sql_query(
        "SELECT MIN(ts) AS min_ts, MAX(ts) AS max_ts FROM weather_hourly",
        db.bind,
    ).iloc[0]
    w_min = w_range["min_ts"]
    w_max = w_range["max_ts"]

    if pd.isna(w_min) or pd.isna(w_max):
        raise HTTPException(status_code=400, detail="No weather data available yet in weather_hourly.")

    # Load rows only within the weather window
    df_load = pd.read_sql_query(
        """
        SELECT ts, value
        FROM timeseries
        WHERE region = %(region)s
          AND metric = 'load'
          AND resolution = 'hour'
          AND ts >= %(w_min)s
          AND ts <= %(w_max)s
        ORDER BY ts ASC
        """,
        db.bind,
        params={"region": region, "w_min": w_min, "w_max": w_max},
    )

    # Weather rows (SQL direct)
    df_weather = pd.read_sql_query(
        """
        SELECT ts, temperature_2m, windspeed_10m, precipitation
        FROM weather_hourly
        WHERE ts >= %(w_min)s AND ts <= %(w_max)s
        ORDER BY ts ASC
        """,
        db.bind,
        params={"w_min": w_min, "w_max": w_max},
    )

    # Debug counts
    log.info("forecast debug: df_load=%d, df_weather=%d, window=[%s..%s]", len(df_load), len(df_weather), w_min, w_max)

    if len(df_load) < 24:
        raise HTTPException(status_code=400, detail=f"Not enough hourly load in overlap window (have {len(df_load)}, need >= 24).")
    if len(df_weather) < 24:
        raise HTTPException(status_code=400, detail=f"Not enough hourly weather in overlap window (have {len(df_weather)}, need >= 24).")

    # Join nearest hour (force same timezone dtype)
    df_load["ts"] = pd.to_datetime(df_load["ts"], utc=True)
    df_weather["ts"] = pd.to_datetime(df_weather["ts"], utc=True)

    df_joined = pd.merge_asof(
        df_load.sort_values("ts"),
        df_weather.sort_values("ts"),
        on="ts",
        direction="nearest",
        tolerance=pd.Timedelta("2h"),
    ).dropna(subset=["temperature_2m", "windspeed_10m", "precipitation"])

    log.info("forecast debug: df_joined=%d (after merge+dropna)", len(df_joined))

    if len(df_joined) < 24:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough merged load+weather rows after join (have {len(df_joined)}, need >= 48).",
        )

    df_pred = train_and_forecast(df_joined, horizon=horizon)
    if df_pred is None or len(df_pred) == 0:
        raise HTTPException(status_code=400, detail="Model produced empty forecast output.")

    return [{"ts": r.ts, "yhat": float(r.yhat)} for r in df_pred.itertuples(index=False)]

def _scheduled_ingest():
    log.info("Starting ingestion run...")
    db = SessionLocal()
    try:
        run_ingestion(db)
        log.info("Ingestion completed.")
    except Exception as e:
        log.exception("Ingestion failed: %s", e)
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler_started = False

@app.on_event("startup")
def start_scheduler():
    global scheduler_started
    if scheduler_started:
        return

    minutes = int(os.getenv("INGEST_INTERVAL_MINUTES", "15"))
    scheduler.add_job(
        _scheduled_ingest,
        "interval",
        minutes=minutes,
        id="ingest_job",
        replace_existing=True,
    )
    scheduler.start()
    scheduler_started = True

@app.post("/ingest-now")
def ingest_now():
    _scheduled_ingest()
    return {"status": "ingest triggered"}

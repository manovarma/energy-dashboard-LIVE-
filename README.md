# ⚡ Energy Demand & Renewables Dashboard (Live + Forecast)

An end-to-end data engineering + analytics project:
**SMARD (energy) + Open-Meteo (weather) → FastAPI → PostgreSQL → Streamlit**

## Features
- Live Monitoring (auto-refresh, KPIs, threshold alerts, drill-down)
- Compare Periods (A vs B analysis)
- Energy Mix (renewables comparison)
- Load Forecast (weather-enhanced predictive model)

## Tech Stack
- Python, FastAPI, Streamlit
- PostgreSQL (SQLAlchemy)
- Pandas, Plotly
- APScheduler

## Data Sources
- SMARD (Bundesnetzagentur) – electricity load, wind, solar
- Open-Meteo – weather features

## Run locally
### Backend
```bash
export INGEST_INTERVAL_MINUTES=15
uvicorn Backend.app.main:app --host 0.0.0.0 --port 8000 --reload

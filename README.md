# ⚡ Energy Demand & Renewables Dashboard (Live + Forecast)

An **end-to-end data engineering and analytics project** that integrates  
**live energy system data and weather data** to deliver interactive dashboards and short-term forecasting.

**Pipeline:**  
SMARD (energy) + Open-Meteo (weather) → FastAPI → PostgreSQL → Streamlit

---

## Features

- **Live Monitoring**
  - Auto-refreshing time series
  - KPI cards (latest, average, min, max)
  - Threshold alerts
  - Interactive drill-down

- **Compare Periods**
  - Period A vs Period B analysis
  - Shape comparison across time windows

- **Energy Mix**
  - Comparison of renewable generation sources
  - Wind vs Solar vs Load over time

- **Load Forecast**
  - Weather-enhanced predictive model
  - Short-term hourly demand forecasting
  - Model trained on live ingested data

---

## Tech Stack

- **Backend:** Python, FastAPI  
- **Database:** PostgreSQL (SQLAlchemy ORM)  
- **Frontend:** Streamlit  
- **Analytics & Visualization:** Pandas, Plotly  
- **Scheduling:** APScheduler  

---

##  Data Sources

- **SMARD (Bundesnetzagentur)**  
  Electricity load, wind, and solar generation data (Germany)

- **Open-Meteo API**  
  Weather features (temperature, wind speed, precipitation)

---

## Run Locally

### 1️ Backend (API + ingestion)
```bash
export INGEST_INTERVAL_MINUTES=15
uvicorn Backend.app.main:app --host 0.0.0.0 --port 8000 --reload

import os
import requests
import pandas as pd

DEFAULT_API_BASE = os.getenv("ENERGY_API_BASE", "http://127.0.0.1:8000")


# Regions available from SMARD-style data (market zones)
REGIONS = ["DE"]  # add "DE-LU" later if you ingest it

# Dashboard metric labels -> API metric keys
METRICS = {
    "Load (MW)": "load",
    "Wind (MW)": "wind",
    "Solar (MW)": "solar",
    "Renewables Share (%)": "renew_share",  # optional derived metric (not from API yet)
}

# SMARD resolutions
RESOLUTIONS = ["quarterhour", "hour", "day"]


def pretty_unit(metric_key: str) -> str:
    return "%" if metric_key == "renew_share" else "MW"


def api_get_timeseries(
    region: str,
    metric_key: str,
    resolution: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    api_base: str = DEFAULT_API_BASE,
    timeout: int = 30,
) -> pd.DataFrame:
    """
    Calls backend:
      GET /timeseries?region=DE&metric=load&resolution=hour&start=...&end=...

    Expects JSON list:
      [{"ts":"...","value":123.4}, ...]
    """
    url = f"{api_base.rstrip('/')}/timeseries"
    params = {
        "region": region,
        "metric": metric_key,
        "resolution": resolution,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }
    r = requests.get(url, params=params, timeout=timeout)

    if r.status_code != 200:
        raise RuntimeError(
            f"API error {r.status_code} from {r.url}\n"
            f"Body preview:\n{(r.text or '')[:500]}"
        )

    content_type = r.headers.get("content-type") or ""
    if "application/json" not in content_type:
        raise RuntimeError(
            f"Expected JSON but got Content-Type: {content_type}\n"
            f"URL: {r.url}\n"
            f"Body preview:\n{(r.text or '')[:500]}"
        )

    data = r.json()
    df = pd.DataFrame(data)
    if not df.empty:
        df["ts"] = pd.to_datetime(df["ts"])
    return df


def get_timeseries(
    region: str,
    metric_key: str,
    resolution: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    api_base: str = DEFAULT_API_BASE,
) -> pd.DataFrame:
    """API-only: no synthetic fallback."""
    return api_get_timeseries(region, metric_key, resolution, start, end, api_base=api_base)

import os
import requests

SMARD_BASE_URL = os.getenv("SMARD_BASE_URL", "https://www.smard.de/app")

def fetch_index(filter_id: str, region: str, resolution: str) -> dict:
    """
    SMARD endpoint (documented via OpenAPI):
    /chart_data/{filter}/{region}/index_{resolution}.json
    """
    url = f"{SMARD_BASE_URL}/chart_data/{filter_id}/{region}/index_{resolution}.json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_series(filter_id: str, region: str, resolution: str, timestamp: int) -> dict:
    url = f"{SMARD_BASE_URL}/chart_data/{filter_id}/{region}/{filter_id}_{region}_{resolution}_{timestamp}.json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


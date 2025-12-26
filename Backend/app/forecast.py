import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

def make_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("ts").copy()
    df["hour"] = df["ts"].dt.hour
    df["dow"] = df["ts"].dt.dayofweek
    df["lag_1"] = df["value"].shift(1)
    df["lag_2"] = df["value"].shift(2)
    df["roll_6"] = df["value"].rolling(6).mean()
    return df

def train_and_forecast(df_joined: pd.DataFrame, horizon: int = 24) -> pd.DataFrame:
    """
    df_joined columns: ts, value (load), temperature_2m, windspeed_10m, precipitation
    """
    df = make_features(df_joined).dropna().copy()
    feature_cols = ["hour","dow","lag_1","lag_2","roll_6","temperature_2m","windspeed_10m","precipitation"]

    X = df[feature_cols]
    y = df["value"]

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)

    # naive recursive forecast: use last rows and roll forward
    last = df_joined.sort_values("ts").copy()
    preds = []
    for i in range(horizon):
        next_ts = last["ts"].iloc[-1] + pd.Timedelta(hours=1)

        # take last known weather row if future not available in DB yet
        w = last.iloc[-1][["temperature_2m","windspeed_10m","precipitation"]].to_dict()

        temp = w.get("temperature_2m", np.nan)
        wind = w.get("windspeed_10m", np.nan)
        precip = w.get("precipitation", np.nan)

        # build feature row from last known values
        value_series = last["value"].astype(float)
        row = {
            "hour": next_ts.hour,
            "dow": next_ts.dayofweek,
            "lag_1": float(value_series.iloc[-1]),
            "lag_2": float(value_series.iloc[-2]) if len(value_series) > 1 else float(value_series.iloc[-1]),
            "roll_6": float(value_series.tail(6).mean()),
            "temperature_2m": temp,
            "windspeed_10m": wind,
            "precipitation": precip,
        }
        yhat = float(model.predict(pd.DataFrame([row]))[0])
        preds.append({"ts": next_ts, "yhat": yhat})

        # append predicted value to roll forward
        last = pd.concat([last, pd.DataFrame([{"ts": next_ts, "value": yhat, **w}])], ignore_index=True)

    return pd.DataFrame(preds)

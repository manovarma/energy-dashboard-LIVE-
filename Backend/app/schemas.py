from pydantic import BaseModel
from datetime import datetime

class TSPoint(BaseModel):
    ts: datetime
    value: float

class ForecastPoint(BaseModel):
    ts: datetime
    yhat: float

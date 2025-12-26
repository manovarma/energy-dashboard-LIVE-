from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from .db import Base

class TimeSeriesPoint(Base):
    __tablename__ = "timeseries"

    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(16), index=True)
    metric = Column(String(32), index=True)        # load, wind, solar
    resolution = Column(String(16), index=True)    # hour, day, 15min
    ts = Column(DateTime(timezone=True), index=True)
    value = Column(Float)

    __table_args__ = (
        Index("ix_timeseries_lookup", "region", "metric", "resolution", "ts"),
    )

class WeatherPoint(Base):
    __tablename__ = "weather_hourly"

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime(timezone=True), index=True)
    temperature_2m = Column(Float, nullable=True)
    windspeed_10m = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)

"""Defines the routes of the API."""

import datetime as dt

from fastapi import FastAPI, status

from fake_api.internal import DatabaseInterface, DBPredictedYield, inputs

server = FastAPI()


db: DatabaseInterface = inputs.DummyDatabase()


@server.get("/")
def read_root() -> dict:
    """Root endpoint for the API."""
    return {"Hello": "World"}


@server.get("/health")
def get_health_route() -> dict:
    """Health endpoint for the API."""
    return {"status": status.HTTP_200_OK}


@server.get("/historic_timeseries/{source}/{region}")
def get_historic_timeseries_route(source: str, region: str) -> dict:
    """Function for the historic timeseries route."""
    yields: list[DBPredictedYield] = []
    if source == "wind":
        yields = db.get_predicted_wind_yields_for_location(location=region)
    elif source == "solar":
        yields = db.get_predicted_solar_yields_for_location(location=region)
    else:
        raise ValueError(f"Unknown source {source}")
    return {
        "yields": [
            y.__dict__ for y in yields if y.TimeUnix < dt.datetime.now(tz=dt.UTC).timestamp()
        ],
    }


@server.get("/forecast_timeseries/{source}/{region}")
def get_forecast_timeseries_route(source: str, region: str) -> dict:
    """Function for the forecast timeseries route."""
    yields: list[DBPredictedYield] = []
    if source == "wind":
        yields = db.get_predicted_wind_yields_for_location(location=region)
    elif source == "solar":
        yields = db.get_predicted_solar_yields_for_location(location=region)
    else:
        raise ValueError(f"Unknown source {source}")
    return {
        "yields": [
            y.__dict__ for y in yields if y.TimeUnix >= dt.datetime.now(tz=dt.UTC).timestamp()
        ],
    }

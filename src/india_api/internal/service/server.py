"""Defines the routes of the API."""

import datetime as dt

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from india_api.internal import (
    DatabaseInterface,
    DBPredictedYield,
    PredictedYield,
    inputs,
)

server = FastAPI()


db: DatabaseInterface = inputs.DummyDatabase()


class GetHealthResponse(BaseModel):
    """Model for the health endpoint response."""

    status: int


@server.get(
    "/health",
    status_code=status.HTTP_200_OK,
)
def get_health_route() -> GetHealthResponse:
    """Health endpoint for the API."""
    return GetHealthResponse(status=status.HTTP_200_OK)


class GetHistoricTimeseriesResponse(BaseModel):
    """Model for the historic timeseries endpoint response."""

    yields: list[PredictedYield]


@server.get(
    "/historic_timeseries/{source}/{region}",
    status_code=status.HTTP_200_OK,
)
def get_historic_timeseries_route(source: str, region: str) -> GetHistoricTimeseriesResponse:
    """Function for the historic timeseries route."""
    yields: list[DBPredictedYield] = []
    if source == "wind":
        try:
            yields = db.get_predicted_wind_yields_for_location(location=region)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting wind yields: {e}",
            ) from e
    elif source == "solar":
        try:
            yields = db.get_predicted_solar_yields_for_location(location=region)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting solar yields: {e}",
            ) from e
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown source {source}",
        )
    return GetHistoricTimeseriesResponse(
        yields=[
            y.to_predicated_yield()
            for y in yields
            if y.TimeUnix < dt.datetime.now(tz=dt.UTC).timestamp()
        ],
    )


class GetForecastTimeseriesResponse(BaseModel):
    """Model for the forecast timeseries endpoint response."""

    yields: list[PredictedYield]


@server.get(
    "/forecast_timeseries/{source}/{region}",
    status_code=status.HTTP_200_OK,
)
def get_forecast_timeseries_route(source: str, region: str) -> GetForecastTimeseriesResponse:
    """Function for the forecast timeseries route."""
    yields: list[DBPredictedYield] = []
    if source == "wind":
        try:
            yields = db.get_predicted_wind_yields_for_location(location=region)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting wind yields: {e}",
            ) from e
    elif source == "solar":
        try:
            yields = db.get_predicted_solar_yields_for_location(location=region)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting solar yields: {e}",
            ) from e
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown source {source}",
        )
    return GetForecastTimeseriesResponse(
        yields=[
            y.to_predicted_yield()
            for y in yields
            if y.TimeUnix >= dt.datetime.now(tz=dt.UTC).timestamp()
        ],
    )

"""Defines the routes of the API."""

import datetime as dt
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

from india_api.internal import (
    DatabaseInterface,
    PredictedYield,
)

server = FastAPI()


def get_db_client() -> DatabaseInterface:
    """Dependency injection for the database client."""
    return DatabaseInterface()


DBClientDependency = Annotated[DatabaseInterface, Depends(get_db_client)]


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
def get_historic_timeseries_route(
    source: str,
    region: str,
    db: DBClientDependency,
) -> GetHistoricTimeseriesResponse:
    """Function for the historic timeseries route."""
    yields: list[PredictedYield] = []
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
            y for y in yields
            if y.Time < dt.datetime.now(tz=dt.UTC)
        ],
    )


class GetForecastTimeseriesResponse(BaseModel):
    """Model for the forecast timeseries endpoint response."""

    yields: list[PredictedYield]


@server.get(
    "/forecast_timeseries/{source}/{region}",
    status_code=status.HTTP_200_OK,
)
def get_forecast_timeseries_route(
    source: str,
    region: str,
    db: DBClientDependency,
) -> GetForecastTimeseriesResponse:
    """Function for the forecast timeseries route."""
    yields: list[PredictedYield] = []
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
            y for y in yields
            if y.Time >= dt.datetime.now(tz=dt.UTC)
        ],
    )

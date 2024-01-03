"""Defines the routes of the API."""

import datetime as dt
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status, Query
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

def validate_source(source: str) -> str:
    """Validate the source parameter."""
    if source not in ["wind", "solar"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown source {source}; valid sources are 'wind' and 'solar'.",
        )
    return source

ValidSourceDependency = Annotated[str, Depends(validate_source)]

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
    "/{source}/{region}/historic_timeseries",
    status_code=status.HTTP_200_OK,
)
def get_historic_timeseries_route(
    source: ValidSourceDependency,
    region: str,
    db: DBClientDependency,
) -> GetHistoricTimeseriesResponse:
    """Function for the historic timeseries route."""
    yields: list[PredictedYield] = []

    try:
        if source == "wind":
            yields = db.get_predicted_wind_yields_for_location(location=region)
        elif source == "solar":
            yields = db.get_predicted_solar_yields_for_location(location=region)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting solar yields: {e}",
        ) from e

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
    "/{source}/{region}/forecast_timeseries",
    status_code=status.HTTP_200_OK,
)
def get_forecast_timeseries_route(
    source: ValidSourceDependency,
    region: str,
    db: DBClientDependency,
) -> GetForecastTimeseriesResponse:
    """Function for the forecast timeseries route."""
    yields: list[PredictedYield] = []

    try:
        if source == "wind":
            yields = db.get_predicted_wind_yields_for_location(location=region)
        elif source == "solar":
            yields = db.get_predicted_solar_yields_for_location(location=region)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting yields: {e}",
        ) from e

    return GetForecastTimeseriesResponse(
        yields=[
            y for y in yields
            if y.Time >= dt.datetime.now(tz=dt.UTC)
        ],
    )

class GetSourcesResponse(BaseModel):
    """Model for the sources endpoint response."""

    sources: list[str]

@server.get(
    "/sources",
    status_code=status.HTTP_200_OK,
)
def get_sources_route() -> GetSourcesResponse:
    """Function for the sources route."""
    return GetSourcesResponse(sources=["wind", "solar"])


class GetRegionsResponse(BaseModel):
    """Model for the regions endpoint response."""

    regions: list[str]

@server.get(
    "/{source}/regions",
    status_code=status.HTTP_200_OK,
)
def get_regions_route(
    source: ValidSourceDependency,
    db: DBClientDependency,
) -> GetRegionsResponse:
    """Function for the regions route."""
    if source == "wind":
        regions = db.get_wind_regions()
    elif source == "solar":
        regions = db.get_solar_regions()
    return GetRegionsResponse(regions=regions)


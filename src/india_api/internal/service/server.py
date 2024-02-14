"""Defines the routes of the API."""

import os
import datetime as dt
import pytz
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from india_api.internal import (
    DatabaseInterface,
    PredictedPower,
)
from india_api.internal.models import ActualPower

log = logging.getLogger(__name__)
version = "0.1.7"


local_tz = pytz.timezone("Asia/Kolkata")

server = FastAPI(
    version=version,
    title="India API",
    description="API providing OCF Forecast for India",
)
origins = os.getenv("ORIGINS", "*").split(",")
server.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


route_tags = [
    {
        "name": "Forecast Routes",
        "description": "Routes for fetching forecast power values.",
    },
    {
        "name": "API Information",
        "description": "Routes pertaining to the usage and status of the API.",
    },
]


# === API ROUTES ==============================================================


class GetHealthResponse(BaseModel):
    """Model for the health endpoint response."""

    status: int


@server.get(
    "/health",
    tags=["API Information"],
    status_code=status.HTTP_200_OK,
)
def get_health_route() -> GetHealthResponse:
    """Health endpoint for the API."""
    return GetHealthResponse(status=status.HTTP_200_OK)


class GetHistoricGenerationResponse(BaseModel):
    """Model for the historic generation endpoint response."""

    values: list[ActualPower]


@server.get(
    "/{source}/{region}/generation",
    tags=["Forecast Routes"],
    status_code=status.HTTP_200_OK,
)
def get_historic_timeseries_route(
    source: ValidSourceDependency,
    region: str,
    db: DBClientDependency,
) -> GetHistoricGenerationResponse:
    """Function for the historic generation route."""
    values: list[ActualPower] = []

    try:
        if source == "wind":
            values = db.get_actual_wind_yields_for_location(location=region)
        elif source == "solar":
            values = db.get_actual_solar_yields_for_location(location=region)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting solar yields: {e}",
        ) from e

    return GetHistoricGenerationResponse(
        values=[y.to_timezone(tz=local_tz) for y in values if y.Time < dt.datetime.now(tz=dt.UTC)],
    )


class GetForecastGenerationResponse(BaseModel):
    """Model for the forecast generation endpoint response."""

    values: list[PredictedPower]


@server.get(
    "/{source}/{region}/forecast",
    tags=["Forecast Routes"],
    status_code=status.HTTP_200_OK,
)
def get_forecast_timeseries_route(
    source: ValidSourceDependency,
    region: str,
    db: DBClientDependency,
) -> GetForecastGenerationResponse:
    """Function for the forecast generation route."""
    values: list[PredictedPower] = []

    try:
        if source == "wind":
            values = db.get_predicted_wind_yields_for_location(location=region)
        elif source == "solar":
            values = db.get_predicted_solar_yields_for_location(location=region)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting yields: {e}",
        ) from e

    return GetForecastGenerationResponse(
        values=[y.to_timezone(tz=local_tz) for y in values if y.Time >= dt.datetime.now(tz=dt.UTC)],
    )


class GetSourcesResponse(BaseModel):
    """Model for the sources endpoint response."""

    sources: list[str]


@server.get(
    "/sources",
    tags=["API Information"],
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
    tags=["API Information"],
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

"""Defines the routes of the API."""

import os
import datetime as dt
import sys

import pytz
import logging
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from india_api.internal import (
    DatabaseInterface,
    PredictedPower,
)
from india_api.internal.models import ActualPower, ForecastHorizon
from india_api.internal.service.auth import Auth, DummyAuth
from india_api.internal.service.resample import resample_generation

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)
version = "0.1.26"

local_tz = pytz.timezone("Asia/Kolkata")

if (os.getenv("AUTH0_DOMAIN") is not None) and (os.getenv("AUTH0_API_AUDIENCE") is not None):
    auth = Auth(
        domain=os.getenv("AUTH0_DOMAIN"),
        api_audience=os.getenv("AUTH0_API_AUDIENCE"),
        algorithm="RS256",
    )
else:
    auth = DummyAuth(domain="dummy", api_audience="dummy", algorithm="dummy")
# TODO: add scopes for granular access across APIs
# auth = Auth(domain=os.getenv('AUTH0_DOMAIN'), api_audience=os.getenv('AUTH0_API_AUDIENCE'), scopes={'read:india': ''})

title = "India API"
description = "API providing OCF Forecast for India"
server = FastAPI(
    version=version,
    title=title,
    description=description,
)
origins = os.getenv("ORIGINS", "*").split(",")
server.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@server.middleware('http')
async def save_api_request_to_db(request: Request,  call_next):
    """Middleware to save the API request to the database."""
    response = await call_next(request)

    # Skip any OPTIONS requests
    if request.method == "OPTIONS":
        return response

    email = None
    # Check if the request has an auth object to avoid error
    if hasattr(request.state, 'auth'):
        auth = getattr(request.state, 'auth')
        email = auth.get("https://openclimatefix.org/email")

    # TODO: store the referer in the DB
    log.info("Referer: %s", request.headers.get("referer"))
    db = server.dependency_overrides[get_db_client]()
    db.save_api_call_to_db(url=request.url.path, email=email)

    return response

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
        request: Request,
        region: str,
        db: DBClientDependency,
        auth: dict = Depends(auth),
        # TODO: add auth scopes
        resample_minutes: Optional[int] = None,
) -> GetHistoricGenerationResponse:
    """Function for the historic generation route."""
    values: list[ActualPower] = []

    try:
        if source == "wind":
            values = db.get_actual_wind_power_production_for_location(location=region)
        elif source == "solar":
            values = db.get_actual_solar_power_production_for_location(location=region)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting {source} power production: {e}",
        ) from e

    if resample_minutes is not None:
        values = resample_generation(values=values, internal_minutes=resample_minutes)

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
        auth: dict = Depends(auth),
        # TODO: add auth scopes
        forecast_horizon: ForecastHorizon = ForecastHorizon.day_ahead,
) -> GetForecastGenerationResponse:
    """Function for the forecast generation route."""
    values: list[PredictedPower] = []

    try:
        if source == "wind":
            values = db.get_predicted_wind_power_production_for_location(location=region, forecast_horizon=forecast_horizon)
        elif source == "solar":
            values = db.get_predicted_solar_power_production_for_location(location=region, forecast_horizon=forecast_horizon)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting {source} power production: {e}",
        ) from e

    return GetForecastGenerationResponse(
        values=[y.to_timezone(tz=local_tz) for y in values],
    )


class GetSourcesResponse(BaseModel):
    """Model for the sources endpoint response."""

    sources: list[str]


@server.get(
    "/sources",
    tags=["API Information"],
    status_code=status.HTTP_200_OK,
)
def get_sources_route(auth: dict = Depends(auth)) -> GetSourcesResponse:
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
        auth: dict = Depends(auth),
        # TODO: add auth scopes
) -> GetRegionsResponse:
    """Function for the regions route."""

    if source == "wind":
        regions = db.get_wind_regions()
    elif source == "solar":
        regions = db.get_solar_regions()
    return GetRegionsResponse(regions=regions)

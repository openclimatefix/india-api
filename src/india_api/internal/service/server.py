"""Defines the routes of the API."""

import os
import datetime as dt
import sys
import time
import jwt

import pytz
import logging
from typing import Annotated, Optional, Callable

from fastapi import Depends, FastAPI, HTTPException, status, Security, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute, APIRouter
from fastapi_auth0 import Auth0User, Auth0
from pydantic import BaseModel

from india_api.internal import (
    DatabaseInterface,
    PredictedPower,
)
from india_api.internal.models import ActualPower
from india_api.internal.service.auth import get_auth_implicit_scheme, get_user
from india_api.internal.service.resample import resample_generation

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)
version = "0.1.21"

local_tz = pytz.timezone("Asia/Kolkata")

auth = Auth0(domain=os.getenv('AUTH0_DOMAIN'), api_audience=os.getenv('AUTH0_API_AUDIENCE'))
# TODO: scopes for granular access across APIs
# auth = Auth0(domain=os.getenv('AUTH0_DOMAIN'), api_audience=os.getenv('AUTH0_API_AUDIENCE'), scopes={'read:india': ''})

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


class User(BaseModel):
    id: str
    email: Optional[str] = None


class LoggedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            token = request.headers.get("Authorization")
            user = None
            log.info("token: %s", token)
            if token:
                token = token.split(" ")[1]
                try:
                    decoded_user = jwt.decode(token, options={"verify_signature": False})
                    user_id = decoded_user.get("sub")
                    user_email = decoded_user.get("https://openclimatefix.org/email")
                    user = User(id=user_id, email=user_email)
                finally:
                    log.info("Failed to decode token")
            # TODO: We could log referer instead of any UI flags etc.
            log.info("Referer: %s", request.headers.get("referer"))
            db = server.dependency_overrides[get_db_client]()
            db.save_api_call_to_db(url=request.url.path, user=user)
            # Similarly we could log the process time
            start_time = time.time()
            response = await original_route_handler(request)
            process_time = str(time.time() - start_time)
            log.info(f"Process Time {process_time} {request.url}s")
            response.headers["X-Process-Time"] = process_time
            return response

        return custom_route_handler


router = APIRouter(route_class=LoggedRoute)


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
        user: Auth0User = Security(get_user()),
        # TODO: user: Auth0User = Security(get_user(), scopes=["read:india"]),
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
        user: Auth0User = Security(get_user()),
        # user: Auth0User = Security(get_user(), scopes=["read:india"]),
) -> GetForecastGenerationResponse:
    """Function for the forecast generation route."""
    values: list[PredictedPower] = []

    try:
        if source == "wind":
            values = db.get_predicted_wind_power_production_for_location(location=region)
        elif source == "solar":
            values = db.get_predicted_solar_power_production_for_location(location=region)
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
def get_sources_route(user: Auth0User = Security(get_user())) -> GetSourcesResponse:
    """Function for the sources route."""

    return GetSourcesResponse(sources=["wind", "solar"])


class GetRegionsResponse(BaseModel):
    """Model for the regions endpoint response."""

    regions: list[str]


@router.get(
    "/{source}/regions",
    tags=["API Information"],
    status_code=status.HTTP_200_OK,
)
def get_regions_route(
        source: ValidSourceDependency,
        db: DBClientDependency,
        user: Auth0User = Security(get_user()),
        # user: Auth0User = Security(get_user(), scopes=["read:india"]),
) -> GetRegionsResponse:
    """Function for the regions route."""

    if source == "wind":
        regions = db.get_wind_regions()
    elif source == "solar":
        regions = db.get_solar_regions()
    return GetRegionsResponse(regions=regions)


# TODO: won't actually need this now if we go with the custom router logging approach with `Referer` stored in DB
# OpenAPI custom theme to allow for UI flag
def custom_openapi():
    """Make custom openapi schema."""
    if server.openapi_schema:
        return server.openapi_schema
    openapi_schema = get_openapi(
        title="Quartz Energy API",
        version=version,
        description=description,
        contact={
            "name": "Quartz Energy by Open Climate Fix",
            "url": "https://openclimatefix.org",
            "email": "info@openclimatefix.org",
        },
        license_info={
            "name": "MIT License",
            "url": "https://github.com/openclimatefix/india-api/blob/main/LICENSE",
        },
        routes=server.routes,
    )
    # Define the global query parameter for UI flag
    global_query_parameter = {
        "name": "ui",
        "in": "query",
        "required": False,
        "schema": {
            "type": "string",
            "show_in_schema": False,
        },
        "show_in_schema": False,  # Don't show this in the schema
        "description": 'A common, optional "ui" query parameter for all endpoints.',
    }
    # Add the query parameter to all paths
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "parameters" in method:
                method["parameters"].append(global_query_parameter)
            else:
                method["parameters"] = [global_query_parameter]

    # Create a new schema without the 'ui' parameter for Swagger UI
    swagger_schema = openapi_schema

    # Manually copy the parameters except 'ui' from openapi_schema to swagger_schema
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            if "parameters" in operation:
                swagger_schema["paths"][path][method]["parameters"] = [
                    param for param in operation["parameters"] if param["name"] != "ui"
                ]

    server.openapi_schema = swagger_schema
    return server.openapi_schema


server.openapi = custom_openapi
server.include_router(router)

"""Defines the routes of the API."""

import os
import datetime as dt
import pandas as pd
import sys

import pytz
import logging
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from india_api.internal import (
    DatabaseInterface,
    PredictedPower,
)
from india_api.internal.models import ActualPower, ForecastHorizon
from india_api.internal.service.auth import Auth, DummyAuth
from india_api.internal.service.csv import format_csv
from india_api.internal.service.resample import resample_generation
from india_api.internal.service.sites import router as sites_router
from india_api.internal.service.regions import router as regions_router
from india_api.internal.service.database_client import get_db_client, DBClientDependency

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)
version = "0.1.32"

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

tags_metadata = [
    {
        "name": "API Information",
        "description": "General API information,",
    },
    {
        "name": "Sites",
        "description": "A site is a specific point location, for example (52.15, 1.25) in latitude and longitude. "
        "Each site will have one source of energy "
        "and there is forecast and generation data for each site. ",
    },
    {
        "name": "Regions",
        "description": "A region is an area of land e.g. Alaska in the USA. "
        "There is forecast and generation data for each region "
        "and there may be different sources of energy in one region.",
    },
]

title = "India API"
description = """ API providing OCF Forecast for India.

## Regions

The regions routes are used to get solar and wind forecasts. 

## Sites

The sites routes are used to get site level forecasts. 
A user can
- **/sites**: Get information about your sites
- **/sites/{site_uuid}/forecast**: Get a forecast for a specific site
- **/sites/{site_uuid}/forecast**: Get and post generation for a specific site

### Authentication and Example
If you need an authentication route, please get your access token with the following code. 
You'll need a username and password. 
```
export AUTH=$(curl --request POST 
   --url https://nowcasting-pro.eu.auth0.com/oauth/token 
   --header 'content-type: application/json' 
   --data '{"client_id":"TODO", "audience":"https://api.nowcasting.io/", "grant_type":"password", "username":"username", "password":"password"}'
)

export TOKEN=$(echo "${AUTH}" | jq '.access_token' | tr -d '"')
```
You can then use
```
curl -X GET 'https://api.quartz.energy/sites' -H "Authorization: Bearer $TOKEN"
```

"""

server = FastAPI(
    version=version,
    title=title,
    description=description,
    openapi_tags=tags_metadata,
)
origins = os.getenv("ORIGINS", "*").split(",")
server.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@server.middleware("http")
async def save_api_request_to_db(request: Request, call_next):
    """Middleware to save the API request to the database."""
    response = await call_next(request)

    # Skip any OPTIONS requests
    if request.method == "OPTIONS":
        return response

    email = None
    # Check if the request has an auth object to avoid error
    if hasattr(request.state, "auth"):
        auth = getattr(request.state, "auth")
        email = auth.get("https://openclimatefix.org/email")

    # TODO: store the referer in the DB
    log.info("Referer: %s", request.headers.get("referer"))
    db = server.dependency_overrides[get_db_client]()

    url = request.url.path
    params = request.url.query
    url_and_query = f"{url}?{params}"

    db.save_api_call_to_db(url=url_and_query, email=email)

    return response


def validate_source(source: str) -> str:
    """Validate the source parameter."""
    if source not in ["wind", "solar"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown source {source}; valid sources are 'wind' and 'solar'.",
        )
    return source


ValidSourceDependency = Annotated[str, Depends(validate_source)]



# === API ROUTES ==============================================================
server.include_router(sites_router)
server.include_router(regions_router)


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
    forecast_horizon_minutes: Optional[int] = None,
) -> GetForecastGenerationResponse:
    """Function for the forecast generation route.

    Args:
        source: The source of the forecast, this is current wind or solar.
        region: The region to get the forecast for.
        forecast_horizon: The time horizon to get the data for. Can be 'latest', 'horizon' or 'day ahead'
        forecast_horizon_minutes: The number of minutes to get the forecast for. forecast_horizon must be 'horizon'
    """
    values: list[PredictedPower] = []

    try:
        if source == "wind":
            values = db.get_predicted_wind_power_production_for_location(
                location=region,
                forecast_horizon=forecast_horizon,
                forecast_horizon_minutes=forecast_horizon_minutes,
            )
        elif source == "solar":
            values = db.get_predicted_solar_power_production_for_location(
                location=region,
                forecast_horizon=forecast_horizon,
                forecast_horizon_minutes=forecast_horizon_minutes,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting {source} power production: {e}",
        ) from e

    return GetForecastGenerationResponse(
        values=[y.to_timezone(tz=local_tz) for y in values],
    )


@server.get(
    "/{source}/{region}/forecast/da-csv", tags=["Forecast Routes"], response_class=FileResponse
)
def get_forecast_da_csv(
    source: ValidSourceDependency,
    region: str,
    db: DBClientDependency,
    auth: dict = Depends(auth),
):
    """
    Route to get the day ahead forecast as a CSV file.
    """
    if source == "wind":
        values = db.get_predicted_wind_power_production_for_location(
            location=region,
            forecast_horizon=ForecastHorizon.day_ahead,
        )
    elif source == "solar":
        values = db.get_predicted_solar_power_production_for_location(
            location=region, forecast_horizon=ForecastHorizon.day_ahead
        )
    else:
        raise Exception(f"Source {source} needs to be wind or solar")

    # format to dataframe
    df = format_csv(values)

    # make file format
    now_ist = pd.Timestamp.now(tz="Asia/Kolkata")
    tomorrow_ist = df["Date [IST]"].iloc[0]
    csv_file_path = f"{region}_{source}_da_{tomorrow_ist}.csv"

    description = f"This file is made for {region} for {source} for {tomorrow_ist}, this was made at {now_ist}"

    output = df.to_csv(index=False)
    return StreamingResponse(
        iter([output] + [description]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment;filename={csv_file_path}"},
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


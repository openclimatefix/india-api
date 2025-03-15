"""Defines the routes of the API."""

import logging
import os
import sys
import datetime as dt

from fastapi import FastAPI, status, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from india_api.internal.service.database_client import get_db_client
from india_api.internal.service.regions import router as regions_router
from india_api.internal.service.sites import router as sites_router
from india_api.internal.service.utils import validate_forecast_timing
from india_api.internal.service.constants import local_tz, get_forecast_timing_message

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)
version = "0.1.52"


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
    # I want to keep this here, as we might add this back in the future
    # {
    #     "name": "Regions",
    #     "description": "A region is an area of land e.g. Alaska in the USA. "
    #     "There is forecast and generation data for each region "
    #     "and there may be different sources of energy in one region.",
    # },
]

title = "India API"
description = f""" API providing OCF Forecast for India.

## Regions

The regions routes are used to get solar and wind forecasts. 

## Sites

The sites routes are used to get site level forecasts. 
A user can
- **/sites**: Get information about your sites
- **/sites/{{site_uuid}}/forecast**: Get a forecast for a specific site
- **/sites/{{site_uuid}}/forecast**: Get and post generation for a specific site

## Forecast Timing

{get_forecast_timing_message()}

### Authentication and Example
If you need an authentication route, please get your access token with the following code. 
You'll need a username and password. 
export AUTH=$(curl --request POST
--url https://nowcasting-pro.eu.auth0.com/oauth/token
--header 'content-type: application/json'
--data '{{"client_id":"TODO", "audience":"https://api.nowcasting.io/", "grant_type":"password", "username":"username", "password":"password"}}'
)

export TOKEN=$(echo "${{AUTH}}" | jq '.access_token' | tr -d '"')

curl -X GET 'https://api.quartz.energy/sites' -H "Authorization: Bearer $TOKEN"


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


def validate_forecast_request(forecast_date: dt.datetime):
    """
    Validates a forecast request according to the day-ahead rule.
    
    Args:
        forecast_date: The date for which forecast is requested
        
    Raises:
        HTTPException: If the forecast request is invalid
    """
    if not validate_forecast_timing(forecast_date):
        from india_api.internal.service.constants import FORECAST_CUTOFF_HOUR
        cutoff_day = forecast_date.astimezone(local_tz) - dt.timedelta(days=1)
        cutoff_time = cutoff_day.replace(hour=FORECAST_CUTOFF_HOUR, minute=0, second=0, microsecond=0)
        
        raise HTTPException(
            status_code=400,
            detail=f"Forecast for {forecast_date.isoformat()} cannot be generated yet. "
                  f"Please wait until after {cutoff_time.isoformat()} IST."
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

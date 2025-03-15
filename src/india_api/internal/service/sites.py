from starlette import status
import datetime as dt

from fastapi import APIRouter, Depends, Query, HTTPException

from india_api.internal import ActualPower, PredictedPower, Site
from india_api.internal.service.database_client import DBClientDependency
from india_api.internal.service.auth import auth
from india_api.internal.service.server import validate_forecast_request

router = APIRouter(
    tags=["Sites"],
)


@router.get(
    "/sites",
    status_code=status.HTTP_200_OK,
)
def get_sites(db: DBClientDependency, auth: dict = Depends(auth)) -> list[Site]:
    """Get sites"""

    # get email from auth
    email = auth["https://openclimatefix.org/email"]

    sites = db.get_sites(email=email)

    return sites


@router.get(
    "/sites/{site_uuid}/forecast",
    status_code=status.HTTP_200_OK,
)
def get_forecast(
    site_uuid: str, 
    db: DBClientDependency, 
    auth: dict = Depends(auth),
    start_datetime: dt.datetime = Query(None, description="Start date and time for forecast in UTC"),
    end_datetime: dt.datetime = Query(None, description="End date and time for forecast in UTC")
) -> list[PredictedPower]:
    """
    Get forecast of a site.
    
    Forecasts follow the day-ahead rule:
    - Forecasts for a given date are generated before 9:00 IST on the day before
    - For example: Forecast for 2024-06-03 12:00 (IST) would be made before 2024-06-02 09:00 IST
    """
    # Validate forecast timing if start_datetime is provided
    if start_datetime:
        validate_forecast_request(start_datetime)

    # get email from auth
    email = auth["https://openclimatefix.org/email"]

    # Get forecast data
    forecast = db.get_site_forecast(site_uuid=site_uuid, email=email)

    return forecast


@router.get(
    "/sites/{site_uuid}/generation",
    status_code=status.HTTP_200_OK,
)
def get_generation(
    site_uuid: str, db: DBClientDependency, auth: dict = Depends(auth)
) -> list[ActualPower]:
    """Get get generation fo a site"""

    # get email from auth
    email = auth["https://openclimatefix.org/email"]

    generation = db.get_site_generation(site_uuid=site_uuid, email=email)

    return generation


@router.post(
    "/sites/{site_uuid}/generation",
    status_code=status.HTTP_200_OK,
)
def post_generation(
    site_uuid: str,
    generation: list[ActualPower],
    db: DBClientDependency,
    auth: dict = Depends(auth),
):
    """Get sites
    
    ### This route is used to input actual PV/Wind generation.

    Users will upload actual PV/Wind generation
    readings in kilowatts (kW) at intervals throughout a given day.
    For example: the average power in kW every 5,10,15 or 30 minutes.

    The PowerKW values should be non-negative floating point numbers
    (e.g., 0.0, 1.5, 10.753, etc).

    #### Parameters
    - **site_uuid**: The unique identifier for the site.
    - **generation**: The actual PV generation values for the site.
        You can add one at a time or many. For example:
        {
            "site_uuid": "0cafe3ed-0c5c-4ef0-9a53-e3789e8c8fc9",
            "generation": [
                {
                    "Time": "2024-02-09T17:19:35.986Z",
                    "PowerKW": 1.452
                }
            ]
        }

    All timestamps (Time) are in UTC.

    **Note**: Users should wait up to 1 day(s) to start experiencing the full
    effects from using live PV data.
    """

    # get email from auth
    email = auth["https://openclimatefix.org/email"]

    db.post_site_generation(site_uuid=site_uuid, generation=generation, email=email)

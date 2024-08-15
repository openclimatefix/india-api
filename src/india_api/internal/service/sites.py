from starlette import status

from fastapi import APIRouter, Depends

from india_api.internal import ActualPower, PredictedPower, Site
from india_api.internal.service.database_client import DBClientDependency
from india_api.internal.service.auth import auth

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
    site_uuid: str, db: DBClientDependency, auth: dict = Depends(auth)
) -> list[PredictedPower]:
    """Get forecast of a site"""

    # get email from auth
    email = auth["https://openclimatefix.org/email"]

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
    """Get sites"""

    # get email from auth
    email = auth["https://openclimatefix.org/email"]

    db.post_site_generation(site_uuid=site_uuid, generation=generation, email=email)

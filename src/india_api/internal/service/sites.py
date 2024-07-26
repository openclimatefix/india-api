from starlette import status

from fastapi import APIRouter

router = APIRouter(
    tags=["Sites"],
)



@router.get(
    "/sites",
    status_code=status.HTTP_200_OK,
)
def get_sites():
    """Get sites"""
    return None


@router.get(
    "/sites/{site_uuid}/forecast",
    status_code=status.HTTP_200_OK,
)
def get_forecast():
    """Get sites"""
    return None


@router.get(
    "/sites/{site_uuid}/generation",
    status_code=status.HTTP_200_OK,
)
def get_general():
    """Get sites"""
    return None


@router.post(
    "/sites/{site_uuid}/generation",
    status_code=status.HTTP_200_OK,
)
def post_generation():
    """Get sites"""
    return None

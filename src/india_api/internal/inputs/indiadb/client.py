"""India DB client that conforms to the DatabaseInterface."""
import datetime as dt
import logging

from pvsite_datamodel import DatabaseConnection
from pvsite_datamodel.read import (
    get_sites_by_country,
    get_latest_forecast_values_by_site,
    get_pv_generation_by_sites,
)
from pvsite_datamodel.sqlmodels import SiteAssetType, ForecastValueSQL
from sqlalchemy.orm import Session

from india_api import internal
from india_api.internal.inputs.utils import get_window

log = logging.getLogger(__name__)


class Client(internal.DatabaseInterface):
    """Defines India DB client that conforms to the DatabaseInterface."""

    session: Session = None

    def __init__(self, database_url: str) -> None:
        """Initialize the client with a SQLAlchemy database connection and session."""

        self.connection = DatabaseConnection(url=database_url, echo=False)

    def _get_session(self):
        """Allows for overriding the default session (useful for testing)"""
        if self.session is None:
            return self.connection.get_session()
        else:
            return self.session

    def get_predicted_yields_for_location(
        self,
        location: str,
        asset_type: SiteAssetType,
    ) -> list[internal.PredictedPower]:
        """Gets the predicted yields for a location."""

        # Get the window
        start, end = get_window()

        # get site uuid
        with self._get_session() as session:
            sites = get_sites_by_country(session, country="india")

            # just select wind site
            sites = [s for s in sites if s.asset_type == asset_type]
            site = sites[0]

            # read actual generations
            values = get_latest_forecast_values_by_site(
                session, site_uuids=[site.site_uuid], start_utc=start
            )
            forecast_values: [ForecastValueSQL] = values[site.site_uuid]

        # convert ForecastValueSQL to PredictedPower
        values = [
            internal.PredictedPower(
                PowerKW=value.forecast_power_kw, Time=value.start_utc.astimezone(dt.UTC)
            )
            for value in forecast_values
        ]

        return values

    def get_generation_for_location(
        self,
        location: str,
        asset_type: SiteAssetType,
    ) -> [internal.PredictedPower]:
        """Gets the predicted yields for a location."""

        # Get the window
        start, end = get_window()

        # get site uuid
        with self._get_session() as session:
            sites = get_sites_by_country(session, country="india")

            # just select wind site
            sites = [site for site in sites if site.asset_type == asset_type]
            site = sites[0]

            # read actual generations
            values = get_pv_generation_by_sites(
                session=session, site_uuids=[site.site_uuid], start_utc=start, end_utc=end
            )

        # convert from GenerationSQL to PredictedPower
        values = [
            internal.ActualPower(
                PowerKW=int(value.generation_power_kw), Time=value.start_utc.astimezone(dt.UTC)
            )
            for value in values
        ]

        return values

    def get_predicted_solar_yields_for_location(
        self,
        location: str,
    ) -> [internal.PredictedPower]:
        """
        Gets the predicted solar yields for a location.

        Args:
            location: The location to get the predicted solar yields for.
        """

        return self.get_predicted_yields_for_location(
            location=location, asset_type=SiteAssetType.pv
        )

    def get_predicted_wind_yields_for_location(
        self,
        location: str,
    ) -> list[internal.PredictedPower]:
        """
        Gets the predicted wind yields for a location.

        Args:
            location: The location to get the predicted wind yields for.
        """

        return self.get_predicted_yields_for_location(
            location=location, asset_type=SiteAssetType.wind
        )

    def get_actual_solar_yields_for_location(self, location: str) -> list[internal.PredictedPower]:
        """Gets the actual solar yields for a location."""

        return self.get_generation_for_location(location=location, asset_type=SiteAssetType.pv)

    def get_actual_wind_yields_for_location(self, location: str) -> list[internal.PredictedPower]:
        """Gets the actual wind yields for a location."""

        return self.get_generation_for_location(location=location, asset_type=SiteAssetType.wind)

    def get_wind_regions(self) -> list[str]:
        """Gets the valid wind regions."""
        return ["ruvnl"]

    def get_solar_regions(self) -> list[str]:
        """Gets the valid solar regions."""
        return ["ruvnl"]

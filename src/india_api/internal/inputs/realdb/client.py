"""A dummy database that conforms to the DatabaseInterface."""
import datetime as dt
import os

from pvsite_datamodel.connection import DatabaseConnection
from pvsite_datamodel.read import (
    get_pv_generation_by_sites,
    get_sites_by_country,
    get_latest_forecast_values_by_site,
)
from pvsite_datamodel.sqlmodels import SiteAssetType, ForecastValueSQL

from india_api import internal


class Client(internal.DatabaseInterface):
    """Defines a real database that conforms to the DatabaseInterface."""

    def __init__(self):
        db_url = os.getenv("DB_URL")
        self.db_connection = DatabaseConnection(url=db_url)

    def get_predicted_yields_for_location(
        self,
        location: str,
        asset_type: SiteAssetType,
    ) -> list[internal.PredictedPower]:

        """Gets the predicted yields for a location."""

        # Get the window
        start, end = _getWindow()

        # get site uuid
        with self.db_connection.get_session() as db_session:
            sites = get_sites_by_country(db_session, country="india")

            # just select wind site
            sites = [site for site in sites if site.asset_type == asset_type]
            site = sites[0]

            # read actual generations
            values = get_latest_forecast_values_by_site(
                session=db_session, site_uuids=[site.site_uuid], start_utc=start
            )
            forecast_values: [ForecastValueSQL] = values[site.site_uuid]

        # convert ForecastValueSQL to PredictedPower
        values = [
            internal.PredictedPower(PowerKW=value.forecast_power_kw, Time=value.start_utc)
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
        start, end = _getWindow()

        # get site uuid
        with self.db_connection.get_session() as db_session:
            sites = get_sites_by_country(db_session, country="india")

            # just select wind site
            for s in sites:
                print(f"{s.asset_type=}")
            sites = [site for site in sites if site.asset_type == asset_type]
            site = sites[0]

            # read actual generations
            values = get_pv_generation_by_sites(
                session=db_session, site_uuids=[site.site_uuid], start_utc=start, end_utc=end
            )

        # convert from GenerationSQL to PredictedPower
        values = [
            internal.PredictedPower(PowerKW=value.generation_power_kw, Time=value.start_utc)
            for value in values
        ]

        return values

    def get_predicted_solar_yields_for_location(
        self,
        location: str,
    ) -> [internal.PredictedPower]:
        """Gets the predicted solar yields for a location.

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
        """Gets the predicted wind yields for a location.

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


def _getWindow() -> tuple[dt.datetime, dt.datetime]:
    """Returns the start and end of the window for timeseries data."""
    # Window start is the beginning of the day two days ago
    start = (dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=2)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    # Window end is the beginning of the day two days ahead
    end = (dt.datetime.now(tz=dt.UTC) + dt.timedelta(days=2)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return start, end

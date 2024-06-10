"""India DB client that conforms to the DatabaseInterface."""
import datetime as dt
import logging
from typing import Optional

from pvsite_datamodel import DatabaseConnection
from pvsite_datamodel.read import (
    get_sites_by_country,
    get_latest_forecast_values_by_site,
    get_pv_generation_by_sites,
    get_user_by_email,
)
from pvsite_datamodel.sqlmodels import SiteAssetType, ForecastValueSQL
from pvsite_datamodel.write.database import save_api_call_to_db
from sqlalchemy.orm import Session

from india_api import internal
from india_api.internal.inputs.utils import get_window
from india_api.internal.inputs.indiadb.smooth import smooth_forecast
from india_api.internal.models import ForecastHorizon

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

    def save_api_call_to_db(self, url: str, email=""):
        """Saves an API call to the database."""
        with self._get_session() as session:
            # save the API call
            log.info(f"Saving API call ({url=}) to database")
            user = get_user_by_email(session, email)
            save_api_call_to_db(url=url, session=session, user=user)

    def get_predicted_power_production_for_location(
        self,
        location: str,
        asset_type: SiteAssetType,
        forecast_horizon: ForecastHorizon = ForecastHorizon.latest,
        forecast_horizon_minutes: Optional[int] = None,
    ) -> list[internal.PredictedPower]:
        """Gets the predicted power production for a location.

        Args:
            location: not used
            asset_type: The type of asset to get the forecast for
            forecast_horizon: The time horizon to get the data for. Can be latest or day ahead
            forecast_horizon_minutes: The number of minutes to get the forecast for. forecast_horizon must be 'horizon'
        """

        # Get the window
        start, end = get_window()

        # get house ahead forecast
        if forecast_horizon == ForecastHorizon.day_ahead:
            day_ahead_hours = 9
            day_ahead_timezone_delta_hours = 5.5
            forecast_horizon_minutes = None
        elif forecast_horizon == ForecastHorizon.horizon:
            day_ahead_hours = 9
            day_ahead_timezone_delta_hours = 5.5
        else:
            day_ahead_hours = None
            day_ahead_timezone_delta_hours = None
            forecast_horizon_minutes = None

        # get site uuid
        with self._get_session() as session:
            sites = get_sites_by_country(session, country="india")

            # just select wind site
            sites = [s for s in sites if s.asset_type == asset_type]
            site = sites[0]

            # read actual generations
            values = get_latest_forecast_values_by_site(
                session,
                site_uuids=[site.site_uuid],
                start_utc=start,
                day_ahead_hours=day_ahead_hours,
                day_ahead_timezone_delta_hours=day_ahead_timezone_delta_hours,
                forecast_horizon_minutes=forecast_horizon_minutes,
            )
            forecast_values: [ForecastValueSQL] = values[site.site_uuid]

        # convert ForecastValueSQL to PredictedPower
        values = [
            internal.PredictedPower(
                PowerKW=int(value.forecast_power_kw)
                if value.forecast_power_kw >= 0
                else 0,  # Set negative values of PowerKW up to 0
                Time=value.start_utc.replace(tzinfo=dt.UTC),
            )
            for value in forecast_values
        ]

        # smooth the forecasts
        values = smooth_forecast(values)

        return values

    def get_generation_for_location(
        self,
        location: str,
        asset_type: SiteAssetType,
    ) -> [internal.PredictedPower]:
        """Gets the predicted power production for a location."""

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
                PowerKW=int(value.generation_power_kw)
                if value.generation_power_kw >= 0
                else 0,  # Set negative values of PowerKW up to 0
                Time=value.start_utc.replace(tzinfo=dt.UTC),
            )
            for value in values
        ]

        return values

    def get_predicted_solar_power_production_for_location(
        self,
        location: str,
        forecast_horizon: ForecastHorizon = ForecastHorizon.latest,
        forecast_horizon_minutes: Optional[int] = None,
    ) -> [internal.PredictedPower]:
        """
        Gets the predicted solar power production for a location.

        Args:
            location: The location to get the predicted solar power production for.
            forecast_horizon: The time horizon to get the data for. Can be latest or day ahead
            forecast_horizon_minutes: The number of minutes to get the forecast for. forecast_horizon must be 'horizon'
        """

        return self.get_predicted_power_production_for_location(
            location=location,
            asset_type=SiteAssetType.pv,
            forecast_horizon=forecast_horizon,
            forecast_horizon_minutes=forecast_horizon_minutes,
        )

    def get_predicted_wind_power_production_for_location(
        self,
        location: str,
        forecast_horizon: ForecastHorizon = ForecastHorizon.latest,
        forecast_horizon_minutes: Optional[int] = None,
    ) -> list[internal.PredictedPower]:
        """
        Gets the predicted wind power production for a location.

        Args:
            location: The location to get the predicted wind power production for.
            forecast_horizon: The time horizon to get the data for. Can be latest or day ahead
            forecast_horizon_minutes: The number of minutes to get the forecast for. forecast_horizon must be 'horizon'
        """

        return self.get_predicted_power_production_for_location(
            location=location,
            asset_type=SiteAssetType.wind,
            forecast_horizon=forecast_horizon,
            forecast_horizon_minutes=forecast_horizon_minutes,
        )

    def get_actual_solar_power_production_for_location(
        self, location: str
    ) -> list[internal.PredictedPower]:
        """Gets the actual solar power production for a location."""

        return self.get_generation_for_location(location=location, asset_type=SiteAssetType.pv)

    def get_actual_wind_power_production_for_location(
        self, location: str
    ) -> list[internal.PredictedPower]:
        """Gets the actual wind power production for a location."""

        return self.get_generation_for_location(location=location, asset_type=SiteAssetType.wind)

    def get_wind_regions(self) -> list[str]:
        """Gets the valid wind regions."""
        return ["ruvnl"]

    def get_solar_regions(self) -> list[str]:
        """Gets the valid solar regions."""
        return ["ruvnl"]

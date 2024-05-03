"""Defines the application models and interfaces."""

import abc
import datetime as dt

from pydantic import BaseModel


class PredictedPower(BaseModel):
    """Defines the data structure for a predicted power value returned by the API."""

    PowerKW: float
    Time: dt.datetime

    def to_timezone(self, tz: dt.timezone) -> "PredictedPower":
        """Converts the time of this predicted power value to the given timezone."""
        return PredictedPower(
            PowerKW=self.PowerKW,
            Time=self.Time.astimezone(tz=tz),
        )


class ActualPower(BaseModel):
    """Defines the data structure for an actual power value returned by the API."""

    PowerKW: float
    Time: dt.datetime

    def to_timezone(self, tz: dt.timezone) -> "ActualPower":
        """Converts the time of this predicted power value to the given timezone."""
        return ActualPower(
            PowerKW=self.PowerKW,
            Time=self.Time.astimezone(tz=tz),
        )


class DatabaseInterface(abc.ABC):
    """Defines the interface for a generic database connection."""

    @abc.abstractmethod
    def get_predicted_solar_power_production_for_location(self, location: str) -> list[PredictedPower]:
        """Returns a list of predicted solar power production for a given location."""
        pass

    @abc.abstractmethod
    def get_actual_solar_power_production_for_location(self, location: str) -> list[ActualPower]:
        """Returns a list of actual solar power production for a given location."""
        pass

    @abc.abstractmethod
    def get_predicted_wind_power_production_for_location(self, location: str) -> list[PredictedPower]:
        """Returns a list of predicted wind power production for a given location."""
        pass

    @abc.abstractmethod
    def get_actual_wind_power_production_for_location(self, location: str) -> list[ActualPower]:
        """Returns a list of actual wind power production for a given location."""
        pass

    @abc.abstractmethod
    def get_wind_regions(self) -> list[str]:
        """Returns a list of wind regions."""
        pass

    @abc.abstractmethod
    def get_solar_regions(self) -> list[str]:
        """Returns a list of solar regions."""
        pass

    @abc.abstractmethod
    def save_api_call_to_db(self, url: str, user=None):
        """Saves an API call to the database."""
        pass
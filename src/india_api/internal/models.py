"""Defines the application models and interfaces."""

import abc
import datetime as dt

from pydantic import BaseModel


class PredictedPower(BaseModel):
    """Defines the data structure for a predicted power value returned by the API."""

    PowerKW: int
    Time: dt.datetime

    def to_timezone(self, tz: dt.timezone) -> "PredictedPower":
        """Converts the time of this predicted power value to the given timezone."""
        return PredictedPower(
            PowerKW=self.PowerKW,
            Time=self.Time.astimezone(tz=tz),
        )


class ActualPower(BaseModel):
    """Defines the data structure for an actual power value returned by the API."""

    PowerKW: int
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
    def get_predicted_solar_yields_for_location(self, location: str) -> list[PredictedPower]:
        """Returns a list of predicted solar yields for a given location."""
        pass

    @abc.abstractmethod
    def get_actual_solar_yields_for_location(self, location: str) -> list[ActualPower]:
        """Returns a list of actual solar yields for a given location."""
        pass

    @abc.abstractmethod
    def get_predicted_wind_yields_for_location(self, location: str) -> list[PredictedPower]:
        """Returns a list of predicted wind yields for a given location."""
        pass

    @abc.abstractmethod
    def get_actual_wind_yields_for_location(self, location: str) -> list[ActualPower]:
        """Returns a list of actual wind yields for a given location."""
        pass

    @abc.abstractmethod
    def get_wind_regions(self) -> list[str]:
        """Returns a list of wind regions."""
        pass

    @abc.abstractmethod
    def get_solar_regions(self) -> list[str]:
        """Returns a list of solar regions."""
        pass

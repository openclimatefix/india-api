"""Defines the application models and interfaces."""

import abc
import datetime as dt

from pydantic import BaseModel


class PredictedYield(BaseModel):
    """Defines the model for a predicted yield returned by the API."""

    YieldKW: int
    Time: dt.datetime


class ActualYield(BaseModel):
    """Defines the model for an actual yield returned by the API."""

    YieldKW: int
    Time: dt.datetime


class DatabaseInterface(abc.ABC):
    """Defines the interface for a generic database connection."""

    @abc.abstractmethod
    def get_predicted_solar_yields_for_location(self, location: str) -> list[PredictedYield]:
        """Returns a list of predicted solar yields for a given location."""
        pass

    @abc.abstractmethod
    def get_actual_solar_yields_for_location(self, location: str) -> list[ActualYield]:
        """Returns a list of actual solar yields for a given location."""
        pass

    @abc.abstractmethod
    def get_predicted_wind_yields_for_location(self, location: str) -> list[PredictedYield]:
        """Returns a list of predicted wind yields for a given location."""
        pass

    @abc.abstractmethod
    def get_actual_wind_yields_for_location(self, location: str) -> list[ActualYield]:
        """Returns a list of actual wind yields for a given location."""
        pass

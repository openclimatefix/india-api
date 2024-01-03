"""Defines the application models and interfaces."""

import abc
import dataclasses as dc
import datetime as dt

from pydantic import BaseModel


class PredictedYield(BaseModel):
    """Defines the model for a predicted yield returned by the API."""

    YieldKW: int
    Time: dt.datetime


@dc.dataclass
class DBPredictedYield:
    """Defines the dataclass for predicted yield pulled from a source."""

    YieldKW: int
    TimeUnix: int
    UncertaintyLow: int
    UncertaintyHigh: int

    def to_predicted_yield(self) -> PredictedYield:
        """Converts the dataclass to a PredictedYield model."""
        return PredictedYield(
            YieldKW=self.YieldKW,
            Time=dt.datetime.fromtimestamp(self.TimeUnix, tz=dt.UTC),
        )


@dc.dataclass
class DBActualYield:
    """Defines the dataclass for actual yield pulled from a source."""

    YieldKW: int
    TimeUnix: int


class DatabaseInterface(abc.ABC):
    """Defines the interface for a generic database connection."""

    @abc.abstractmethod
    def get_predicted_solar_yields_for_location(self, location: str) -> list[DBPredictedYield]:
        """Returns a list of predicted solar yields for a given location."""
        pass

    @abc.abstractmethod
    def get_actual_solar_yields_for_location(self, location: str) -> list[DBActualYield]:
        """Returns a list of actual solar yields for a given location."""
        pass

    @abc.abstractmethod
    def get_predicted_wind_yields_for_location(self, location: str) -> list[DBPredictedYield]:
        """Returns a list of predicted wind yields for a given location."""
        pass

    @abc.abstractmethod
    def get_actual_wind_yields_for_location(self, location: str) -> list[DBActualYield]:
        """Returns a list of actual wind yields for a given location."""
        pass

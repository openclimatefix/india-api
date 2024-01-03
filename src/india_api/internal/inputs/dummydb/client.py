"""A dummy database that conforms to the DatabaseInterface."""
import datetime as dt
import math
import random

from india_api import internal

from ._models import DummyDBPredictedYield

# step defines the time interval between each data point
step: dt.timedelta = dt.timedelta(minutes=5)


class Client(internal.DatabaseInterface):
    """Defines a dummy database that conforms to the DatabaseInterface."""

    def get_predicted_solar_yields_for_location(
        self,
        location: str,
    ) -> list[internal.PredictedYield]:
        """Gets the predicted solar yields for a location.

        Args:
            location: The location to get the predicted solar yields for.
        """
        # Get the window
        start, end = _getWindow()
        numSteps = int((end - start) / step)
        yields: list[internal.PredictedYield] = []

        for i in range(numSteps):
            time = start + i * step
            _yield = _basicSolarYieldFunc(int(time.timestamp()))
            yields.append(
                internal.PredictedYield(
                    Time=time,
                    YieldKW=int(_yield.YieldKW),
                ),
            )

        return yields

    def get_predicted_wind_yields_for_location(
        self,
        location: str,
    ) -> list[internal.PredictedYield]:
        """Gets the predicted wind yields for a location.

        Args:
            location: The location to get the predicted wind yields for.
        """
        # Get the window
        start, end = _getWindow()
        numSteps = int((end - start) / step)
        yields: list[internal.PredictedYield] = []

        for i in range(numSteps):
            time = start + i * step
            _yield = _basicWindYieldFunc(int(time.timestamp()))
            yields.append(
                internal.PredictedYield(
                    Time=time,
                    YieldKW=int(_yield.YieldKW),
                ),
            )

        return yields

    def get_actual_solar_yields_for_location(self, location: str) -> list[internal.PredictedYield]:
        """Gets the actual solar yields for a location."""
        # Get the window
        start, end = _getWindow()
        numSteps = int((end - start) / step)
        yields: list[internal.PredictedYield] = []

        for i in range(numSteps):
            time = start + i * step
            _yield = _basicSolarYieldFunc(int(time.timestamp()))
            yields.append(
                internal.PredictedYield(
                    Time=time,
                    YieldKW=int(_yield.YieldKW),
                ),
            )

        return yields

    def get_actual_wind_yields_for_location(self, location: str) -> list[internal.PredictedYield]:
        """Gets the actual wind yields for a location."""
        # Get the window
        start, end = _getWindow()
        numSteps = int((end - start) / step)
        yields: list[internal.PredictedYield] = []

        for i in range(numSteps):
            time = start + i * step
            _yield = _basicWindYieldFunc(int(time.timestamp()))
            yields.append(
                internal.PredictedYield(
                    Time=time,
                    YieldKW=int(_yield.YieldKW),
                ),
            )

        return yields

    def get_wind_regions(self) -> list[str]:
        """Gets the valid wind regions."""
        return ["dummy_wind_region1", "dummy_wind_region2"]

    def get_solar_regions(self) -> list[str]:
        """Gets the valid solar regions."""
        return ["dummy_solar_region1", "dummy_solar_region2"]


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
    return (start, end)


def _basicSolarYieldFunc(timeUnix: int, scaleFactor: int = 10000) -> DummyDBPredictedYield:
    """Gets a fake solar yield for the input time.

    The basic yield function is built from a sine wave
    with a period of 24 hours, peaking at 12 hours.
    Further convolutions modify the value according to time of year.

    Args:
        timeUnix: The time in unix time.
        scaleFactor: The scale factor for the sine wave.
            A scale factor of 10000 will result in a peak yield of 10 kW.
    """
    # Create a datetime object from the unix time
    time = dt.datetime.fromtimestamp(timeUnix, tz=dt.UTC)
    # The functions x values are hours, so convert the time to hours
    hour = time.day * 24 + time.hour + time.minute / 60 + time.second / 3600

    # scaleX makes the period of the function 24 hours
    scaleX = math.pi / 12
    # translateX moves the minimum of the function to 0 hours
    translateX = -math.pi / 2
    # translateY modulates the base function based on the month.
    # * + 0.5 at the summer solstice
    # * - 0.5 at the winter solstice
    translateY = math.sin((math.pi / 6) * time.month + translateX) / 2.0

    # basefunc ranges between -1 and 1 with a period of 24 hours,
    # peaking at 12 hours.
    # translateY changes the min and max to range between 1.5 and -1.5
    # depending on the month.
    basefunc = math.sin(scaleX * hour + translateX) + translateY
    # Remove negative values
    basefunc = max(0, basefunc)
    # Steepen the curve. The divisor is based on the max value
    basefunc = basefunc**4 / 1.5**4

    # Instead of completely random noise, apply based on the following process:
    # * A base noise function which is the product of long and short sines
    # * The resultant function modulates with very small amplitude around 1
    noise = (math.sin(math.pi * time.hour) / 20) * (math.sin(math.pi * time.hour / 3)) + 1
    noise = noise * random.random() / 20 + 0.97

    # Create the output value from the base function, noise, and scale factor
    output = basefunc * noise * scaleFactor

    # Add some random Uncertaintyor
    UncertaintyLow: float = 0.0
    UncertaintyHigh: float = 0.0
    if output > 0:
        UncertaintyLow = output - (random.random() * output / 10)
        UncertaintyHigh = output + (random.random() * output / 10)

    return DummyDBPredictedYield(
        YieldKW=output,
        UncertaintyLow=UncertaintyLow,
        UncertaintyHigh=UncertaintyHigh,
    )


def _basicWindYieldFunc(timeUnix: int, scaleFactor: int = 10000) -> DummyDBPredictedYield:
    """Gets a fake wind yield for the input time."""
    output = min(scaleFactor, scaleFactor * 10 * random.random())

    UncertaintyLow: float = 0.0
    UncertaintyHigh: float = 0.0
    if output > 0:
        UncertaintyLow = output - (random.random() * output / 10)
        UncertaintyHigh = output + (random.random() * output / 10)

    return DummyDBPredictedYield(
        YieldKW=output,
        UncertaintyLow=UncertaintyLow,
        UncertaintyHigh=UncertaintyHigh,
    )

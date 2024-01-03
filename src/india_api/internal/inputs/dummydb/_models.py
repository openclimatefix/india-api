import dataclasses as dc


@dc.dataclass
class DummyDBPredictedYield:
    """Structure of the predicted yield data from the dummy database."""

    YieldKW: float
    UncertaintyLow: float
    UncertaintyHigh: float

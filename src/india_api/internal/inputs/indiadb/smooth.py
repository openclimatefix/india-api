import pandas as pd
from india_api.internal import PredictedPower


def smooth_forecast(values: list[PredictedPower]) -> list[PredictedPower]:
    """Smooths the forecast values."""
    # convert to dataframe
    df = pd.DataFrame(
        {
            "Time": [value.Time for value in values],
            "PowerKW": [value.PowerKW for value in values],
        }
    )

    # smooth and make sure it is symmetrical
    df = df.set_index("Time")
    df = df.rolling(4, min_periods=1, center=True, closed='both').mean()

    # convert to ints
    df["PowerKW"] = df["PowerKW"].astype(int)

    # convert to ints
    df["PowerKW"] = df["PowerKW"].astype(int)

    # convert back to list of PredictedPower
    return [
        PredictedPower(
            Time=index,
            PowerKW=row.PowerKW,
        )
        for index, row in df.iterrows()
    ]

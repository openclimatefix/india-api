import pandas as pd
from india_api.internal import (
    PredictedPower
)


def smooth_forecast(values: list[PredictedPower]) -> list[PredictedPower]:

    # convert to dataframe
    df = pd.DataFrame(
        {
            "Time": [value.Time for value in values],
            "PowerKW": [value.PowerKW for value in values],
        }
    )

    # smooth
    df = df.set_index("Time").rolling(4).mean()

    # convert back to list of PredictedPower
    return [
        PredictedPower(
            Time=index,
            PowerKW=row.PowerKW,
        )
        for index, row in df.iterrows()
    ]
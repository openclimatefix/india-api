import pandas as pd
from india_api.internal import (
    ActualPower
)


def resample_generation(values: list[ActualPower], internal_minutes: int) -> list[ActualPower]:

    # convert to dataframe
    df = pd.DataFrame(
        {
            "Time": [value.Time for value in values],
            "PowerKW": [value.PowerKW for value in values],
        }
    )

    # resample
    df = df.set_index("Time").resample(f"{internal_minutes}T").mean().dropna()

    # convert to PowerKW to integers
    df.PowerKW = df.PowerKW.astype(int)

    # convert back to list of ActualPower
    return [
        ActualPower(
            Time=index,
            PowerKW=row.PowerKW,
        )
        for index, row in df.iterrows()
    ]
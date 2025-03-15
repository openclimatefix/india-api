import datetime as dt
import pytz

# Keep the original local_tz definition
local_tz = pytz.timezone("Asia/Kolkata")

# Timezone constants
IST_TIMEZONE = pytz.timezone("Asia/Kolkata")
UTC_TIMEZONE = pytz.UTC

# Forecast timing constants
FORECAST_CUTOFF_HOUR = 9  # 9:00 AM IST
FORECAST_DAY_AHEAD = 1    # 1 day before

# Forecast timing message format
FORECAST_TIMING_MESSAGE = (
    "Forecasts are generated before {cutoff_time} IST on the day before the forecast date. "
    "For example, a forecast for {example_date} would be generated before {example_cutoff}."
)

def get_forecast_timing_message() -> str:
    """Returns a formatted message explaining forecast timing rules."""
    now = dt.datetime.now(UTC_TIMEZONE).astimezone(IST_TIMEZONE)
    example_date = (now + dt.timedelta(days=2)).strftime("%Y-%m-%d %H:%M")
    example_cutoff = (now + dt.timedelta(days=1)).replace(
        hour=FORECAST_CUTOFF_HOUR, minute=0, second=0
    ).strftime("%Y-%m-%d %H:%M")
    
    return FORECAST_TIMING_MESSAGE.format(
        cutoff_time=f"{FORECAST_CUTOFF_HOUR}:00",
        example_date=example_date,
        example_cutoff=example_cutoff
    )

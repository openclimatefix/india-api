import datetime as dt
from india_api.internal.service.constants import local_tz

def get_window() -> tuple[dt.datetime, dt.datetime]:
    """
    Returns the start and end of the window for timeseries data,
    following the day-ahead rule (before 9:00 IST the day before).
    """
    # Current time in IST
    now_ist = dt.datetime.now(tz=dt.UTC).astimezone(local_tz)
    
    # Window start is the beginning of the day two days ago
    start = (now_ist - dt.timedelta(days=2)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    
    # Window end depends on the current time
    # If before 9:00 IST, end is the beginning of tomorrow
    # If after 9:00 IST, end is the beginning of the day after tomorrow
    if now_ist.hour < 9:
        end = (now_ist + dt.timedelta(days=1)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    else:
        end = (now_ist + dt.timedelta(days=2)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    
    return (start.astimezone(dt.UTC), end.astimezone(dt.UTC))

def validate_forecast_timing(forecast_date: dt.datetime) -> bool:
    """
    Validates that a forecast follows the day-ahead rule.
    Forecasts must be generated before 9:00 IST on the day before.
    
    Args:
        forecast_date: The date for which forecast is requested
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Convert times to IST
    forecast_ist = forecast_date.astimezone(local_tz)
    current_time = dt.datetime.now(dt.UTC).astimezone(local_tz)
    
    # Calculate cutoff time (9:00 IST on the day before forecast_date)
    cutoff_day = forecast_ist - dt.timedelta(days=1)
    cutoff_time = cutoff_day.replace(hour=9, minute=0, second=0, microsecond=0)
    
    return current_time > cutoff_time

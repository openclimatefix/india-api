import datetime as dt
from zoneinfo import ZoneInfo  # Available in Python 3.9 and later


def get_window() -> tuple[dt.datetime, dt.datetime]:
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

def get_forecast_deadline(forecast_date_str: str) -> str:
    """
    Calculate the submission deadline for a given forecast date.

    Args:
        forecast_date_str (str): The forecast date in 'YYYY-MM-DD' format.

    Returns:
        str: The submission deadline in 'YYYY-MM-DD HH:MM IST' format.
    """
    # Define the IST timezone
    ist = ZoneInfo('Asia/Kolkata')

    # Parse the input forecast date string into a datetime object
    forecast_date = dt.datetime.strptime(forecast_date_str, '%Y-%m-%d')

    # Calculate the deadline: 9:00 AM IST on the day before the forecast date
    deadline = dt.datetime.combine(forecast_date - dt.timedelta(days=1), dt.time(9, 0), tzinfo=ist)

    # Format the deadline as a string
    deadline_str = deadline.strftime('%Y-%m-%d %H:%M %Z')

    return deadline_str

import time
from datetime import datetime, timedelta

def get_timestamps(duration: int, unit: str) -> dict:
    """
    Get the start and end Unix timestamps in milliseconds based on the given duration.

    Parameters:
    duration (int): The duration for the time period.
    unit (str): The unit of time ('hours' or 'days').

    Returns:
    dict: A dictionary with 'start_ts' and 'end_ts' Unix timestamps in milliseconds.
    """
    if unit not in ['hours', 'days']:
        raise ValueError("Unit must be either 'hours' or 'days'")

    # Get the current time in Unix timestamp format (milliseconds)
    end_ts = int(time.time() * 1000)

    # Calculate the start timestamp based on the duration and unit
    if unit == 'hours':
        start_time = datetime.now() - timedelta(hours=duration)
    elif unit == 'days':
        start_time = datetime.now() - timedelta(days=duration)

    start_ts = int(start_time.timestamp() * 1000)

    return {'start_ts': start_ts, 'end_ts': end_ts}


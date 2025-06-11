"""
Timezone utilities for GranolaMCP.

Provides functions for converting UTC timestamps to CST using Python's
standard library zoneinfo module (Python 3.9+).
"""

import datetime
from zoneinfo import ZoneInfo
from typing import Union


def get_cst_timezone() -> ZoneInfo:
    """
    Get the CST timezone object.

    Returns:
        ZoneInfo: CST timezone object
    """
    return ZoneInfo("America/Chicago")


def convert_utc_to_cst(utc_timestamp: Union[datetime.datetime, str, int, float]) -> datetime.datetime:
    """
    Convert a UTC timestamp to CST.

    Args:
        utc_timestamp: UTC timestamp as datetime object, ISO string, or Unix timestamp

    Returns:
        datetime.datetime: Timestamp converted to CST

    Raises:
        ValueError: If timestamp format is invalid
        TypeError: If timestamp type is not supported
    """
    cst_tz = get_cst_timezone()
    utc_tz = ZoneInfo("UTC")

    # Handle different input types
    if isinstance(utc_timestamp, datetime.datetime):
        # If datetime has no timezone info, assume UTC
        if utc_timestamp.tzinfo is None:
            utc_dt = utc_timestamp.replace(tzinfo=utc_tz)
        else:
            utc_dt = utc_timestamp.astimezone(utc_tz)
    elif isinstance(utc_timestamp, str):
        # Parse ISO format string
        try:
            # Handle various ISO formats
            if utc_timestamp.endswith('Z'):
                utc_timestamp = utc_timestamp[:-1] + '+00:00'
            utc_dt = datetime.datetime.fromisoformat(utc_timestamp)
            if utc_dt.tzinfo is None:
                utc_dt = utc_dt.replace(tzinfo=utc_tz)
            else:
                utc_dt = utc_dt.astimezone(utc_tz)
        except ValueError as e:
            raise ValueError(f"Invalid ISO timestamp format: {utc_timestamp}") from e
    elif isinstance(utc_timestamp, (int, float)):
        # Unix timestamp
        try:
            utc_dt = datetime.datetime.fromtimestamp(utc_timestamp, tz=utc_tz)
        except (ValueError, OSError) as e:
            raise ValueError(f"Invalid Unix timestamp: {utc_timestamp}") from e
    else:
        raise TypeError(f"Unsupported timestamp type: {type(utc_timestamp)}")

    # Convert to CST
    return utc_dt.astimezone(cst_tz)


def format_cst_timestamp(cst_datetime: datetime.datetime, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Format a CST datetime object as a string.

    Args:
        cst_datetime: CST datetime object
        format_str: Format string (default includes timezone)

    Returns:
        str: Formatted timestamp string
    """
    return cst_datetime.strftime(format_str)


def get_current_cst_time() -> datetime.datetime:
    """
    Get the current time in CST.

    Returns:
        datetime.datetime: Current CST time
    """
    return datetime.datetime.now(get_cst_timezone())
"""
Date parsing utilities for GranolaMCP.

Provides functions for parsing relative dates (3d, 24h, 1w) and absolute dates
(YYYY-MM-DD) using Python's standard library datetime module.
"""

import datetime
import re
from typing import Union, Tuple, Optional
from ..core.timezone_utils import get_cst_timezone


def parse_relative_date(relative_str: str, reference_time: Optional[datetime.datetime] = None) -> datetime.datetime:
    """
    Parse a relative date string like '3d', '24h', '1w' into a datetime.

    Args:
        relative_str: Relative date string (e.g., '3d', '24h', '1w', '2m')
        reference_time: Reference time to calculate from (default: current CST time)

    Returns:
        datetime.datetime: Calculated datetime in CST

    Raises:
        ValueError: If the relative date format is invalid
    """
    if reference_time is None:
        reference_time = datetime.datetime.now(get_cst_timezone())

    # Normalize the input
    relative_str = relative_str.strip().lower()

    # Parse the relative date pattern
    pattern = r'^(\d+)([hdwmy])$'
    match = re.match(pattern, relative_str)

    if not match:
        raise ValueError(f"Invalid relative date format: {relative_str}. Expected format like '3d', '24h', '1w'")

    amount = int(match.group(1))
    unit = match.group(2)

    # Calculate the timedelta
    if unit == 'h':  # hours
        delta = datetime.timedelta(hours=amount)
    elif unit == 'd':  # days
        delta = datetime.timedelta(days=amount)
    elif unit == 'w':  # weeks
        delta = datetime.timedelta(weeks=amount)
    elif unit == 'm':  # months (approximate as 30 days)
        delta = datetime.timedelta(days=amount * 30)
    elif unit == 'y':  # years (approximate as 365 days)
        delta = datetime.timedelta(days=amount * 365)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")

    # Subtract the delta to get the past time
    return reference_time - delta


def parse_absolute_date(date_str: str, time_str: str = "00:00:00") -> datetime.datetime:
    """
    Parse an absolute date string like 'YYYY-MM-DD' into a datetime.

    Args:
        date_str: Date string in YYYY-MM-DD format
        time_str: Time string in HH:MM:SS format (default: "00:00:00")

    Returns:
        datetime.datetime: Parsed datetime in CST

    Raises:
        ValueError: If the date format is invalid
    """
    try:
        # Parse the date
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

        # Parse the time
        time_obj = datetime.datetime.strptime(time_str, "%H:%M:%S").time()

        # Combine date and time with CST timezone
        cst_tz = get_cst_timezone()
        return datetime.datetime.combine(date_obj, time_obj, tzinfo=cst_tz)

    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD") from e


def parse_date(date_input: str, reference_time: Optional[datetime.datetime] = None) -> datetime.datetime:
    """
    Parse either a relative or absolute date string.

    Args:
        date_input: Date string (relative like '3d' or absolute like '2025-01-01')
        reference_time: Reference time for relative dates (default: current CST time)

    Returns:
        datetime.datetime: Parsed datetime in CST

    Raises:
        ValueError: If the date format is invalid
    """
    date_input = date_input.strip()

    # Check if it's a relative date (contains letters)
    if re.search(r'[a-zA-Z]', date_input):
        return parse_relative_date(date_input, reference_time)

    # Check if it's an absolute date (YYYY-MM-DD format)
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_input):
        return parse_absolute_date(date_input)

    # Check if it's an absolute datetime (YYYY-MM-DD HH:MM:SS format)
    datetime_match = re.match(r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})$', date_input)
    if datetime_match:
        date_part, time_part = datetime_match.groups()
        return parse_absolute_date(date_part, time_part)

    raise ValueError(f"Invalid date format: {date_input}. Expected relative (3d, 24h, 1w) or absolute (YYYY-MM-DD)")


def get_date_range(start_date: str, end_date: Optional[str] = None, reference_time: Optional[datetime.datetime] = None) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Parse a date range from start and optional end date strings.

    Args:
        start_date: Start date string (relative or absolute)
        end_date: End date string (relative or absolute). If None, uses current time
        reference_time: Reference time for relative dates (default: current CST time)

    Returns:
        Tuple[datetime.datetime, datetime.datetime]: Start and end datetimes in CST
    """
    if reference_time is None:
        reference_time = datetime.datetime.now(get_cst_timezone())

    start_dt = parse_date(start_date, reference_time)

    if end_date is None:
        end_dt = reference_time
    else:
        end_dt = parse_date(end_date, reference_time)

    # Ensure start is before end
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt

    return start_dt, end_dt


def format_date_for_display(dt: datetime.datetime, include_timezone: bool = True) -> str:
    """
    Format a datetime for display purposes.

    Args:
        dt: Datetime to format
        include_timezone: Whether to include timezone in output

    Returns:
        str: Formatted date string
    """
    if include_timezone:
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
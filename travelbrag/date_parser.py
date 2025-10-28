"""Simple date parser for ISO dates and duration calculation."""

from datetime import date, timedelta
from typing import Optional, Tuple


def validate_iso_date(date_str: str) -> Optional[str]:
    """Validate an ISO format date string (YYYY-MM-DD or YYYY-MM).

    Args:
        date_str: Date string in ISO format (YYYY-MM-DD or YYYY-MM)

    Returns:
        Normalized date string or None if invalid
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    try:
        # Try YYYY-MM-DD format first
        date.fromisoformat(date_str)
        return date_str
    except ValueError:
        # Try YYYY-MM format
        try:
            date.fromisoformat(f"{date_str}-01")
            return date_str
        except ValueError:
            return None


def parse_iso_date(date_str: str) -> Optional[date]:
    """Parse an ISO format date string (YYYY-MM-DD or YYYY-MM) to a date object.

    For YYYY-MM format, converts to the first day of the month for calculations.

    Args:
        date_str: Date string in ISO format (YYYY-MM-DD or YYYY-MM)

    Returns:
        Parsed date object or None if invalid
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    try:
        # Try YYYY-MM-DD format first
        return date.fromisoformat(date_str)
    except ValueError:
        # Try YYYY-MM format (add -01 for first day of month)
        try:
            return date.fromisoformat(f"{date_str}-01")
        except ValueError:
            return None


def calculate_duration(start_date_str: str, end_date_str: str) -> int:
    """Calculate trip duration in days.

    Args:
        start_date_str: Trip start date (YYYY-MM-DD or YYYY-MM)
        end_date_str: Trip end date (YYYY-MM-DD or YYYY-MM)

    Returns:
        Number of days (inclusive of both start and end)
    """
    start_date = parse_iso_date(start_date_str)
    end_date = parse_iso_date(end_date_str)

    if not start_date or not end_date:
        raise ValueError("Invalid date format")

    if end_date < start_date:
        raise ValueError("End date cannot be before start date")
    return (end_date - start_date).days + 1


def validate_dates(start_str: str, end_str: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Validate and parse date inputs.

    Preserves the original format of the input dates (YYYY-MM-DD or YYYY-MM).

    Args:
        start_str: Start date string in ISO format
        end_str: End date string in ISO format

    Returns:
        Tuple of (start_date_str, end_date_str, error_message)
        Returns (None, None, error) if validation fails
    """
    # Validate start date
    start_date_validated = validate_iso_date(start_str)
    if not start_date_validated:
        return None, None, "Start date must be in YYYY-MM-DD or YYYY-MM format"

    # Validate end date
    if not end_str:
        return None, None, "End date is required"

    end_date_validated = validate_iso_date(end_str)
    if not end_date_validated:
        return None, None, "End date must be in YYYY-MM-DD or YYYY-MM format"

    # Compare dates (ISO format strings compare correctly)
    if end_date_validated < start_date_validated:
        return None, None, "End date cannot be before start date"

    return start_date_validated, end_date_validated, None
"""Tests for the date parser module."""

import pytest
from datetime import date, timedelta
from travelbrag.date_parser import (
    parse_iso_date,
    calculate_duration,
    validate_dates
)


class TestParseIsoDate:
    """Tests for parse_iso_date function."""

    def test_valid_iso_date(self):
        """Test parsing valid ISO date (YYYY-MM-DD)."""
        assert parse_iso_date("2025-01-15") == date(2025, 1, 15)
        assert parse_iso_date("2025-12-31") == date(2025, 12, 31)
        assert parse_iso_date("  2025-06-01  ") == date(2025, 6, 1)

    def test_valid_year_month_date(self):
        """Test parsing valid year-month date (YYYY-MM)."""
        assert parse_iso_date("2025-01") == date(2025, 1, 1)
        assert parse_iso_date("2025-12") == date(2025, 12, 1)
        assert parse_iso_date("  2025-06  ") == date(2025, 6, 1)
        assert parse_iso_date("2024-02") == date(2024, 2, 1)

    def test_invalid_date_format(self):
        """Test invalid date formats."""
        assert parse_iso_date("01/15/2025") is None
        assert parse_iso_date("25-01-15") is None
        assert parse_iso_date("invalid") is None
        # fromisoformat is strict about format - requires zero-padded month/day
        assert parse_iso_date("2025-1-15") is None
        assert parse_iso_date("2025-01-5") is None
        assert parse_iso_date("2025-1-5") is None

    def test_empty_or_none(self):
        """Test empty or None input."""
        assert parse_iso_date("") is None
        assert parse_iso_date(None) is None
        assert parse_iso_date("   ") is None


class TestCalculateDuration:
    """Tests for calculate_duration function."""

    def test_single_day_trip(self):
        """Test duration of 1-day trip."""
        assert calculate_duration("2025-01-15", "2025-01-15") == 1

    def test_multi_day_trip(self):
        """Test duration of multi-day trips."""
        assert calculate_duration("2025-01-15", "2025-01-19") == 5
        assert calculate_duration("2025-01-01", "2025-01-07") == 7
        assert calculate_duration("2025-01-01", "2025-01-31") == 31

    def test_year_month_dates(self):
        """Test with YYYY-MM format dates."""
        assert calculate_duration("2025-01", "2025-02") == 32  # Jan 1 to Feb 1
        assert calculate_duration("2025-01", "2025-01-15") == 15  # Jan 1 to Jan 15

    def test_invalid_date_range(self):
        """Test invalid date ranges."""
        with pytest.raises(ValueError, match="End date cannot be before start date"):
            calculate_duration("2025-01-20", "2025-01-15")


class TestValidateDates:
    """Tests for validate_dates function."""

    def test_valid_with_end_date(self):
        """Test validation with valid end date."""
        start, end, error = validate_dates("2025-01-15", "2025-01-20")
        assert start == "2025-01-15"
        assert end == "2025-01-20"
        assert error is None

    def test_invalid_start_date(self):
        """Test invalid start date."""
        start, end, error = validate_dates("invalid", "2025-01-20")
        assert start is None
        assert end is None
        assert error == "Start date must be in YYYY-MM-DD or YYYY-MM format"

    def test_invalid_end_date(self):
        """Test invalid end date."""
        start, end, error = validate_dates("2025-01-15", "invalid")
        assert start is None
        assert end is None
        assert error == "End date must be in YYYY-MM-DD or YYYY-MM format"

    def test_end_before_start(self):
        """Test end date before start date."""
        start, end, error = validate_dates("2025-01-20", "2025-01-15")
        assert start is None
        assert end is None
        assert error == "End date cannot be before start date"

    def test_missing_end_date(self):
        """Test missing end date."""
        start, end, error = validate_dates("2025-01-15", "")
        assert start is None
        assert end is None
        assert error == "End date is required"

    def test_valid_year_month_dates(self):
        """Test validation with year-month format dates - preserves original format."""
        # Both dates in YYYY-MM format
        start, end, error = validate_dates("2025-01", "2025-03")
        assert start == "2025-01"
        assert end == "2025-03"
        assert error is None

        # Mixed format: YYYY-MM start, YYYY-MM-DD end
        start, end, error = validate_dates("2025-01", "2025-01-20")
        assert start == "2025-01"
        assert end == "2025-01-20"
        assert error is None

        # Mixed format: YYYY-MM-DD start, YYYY-MM end
        start, end, error = validate_dates("2025-01-15", "2025-02")
        assert start == "2025-01-15"
        assert end == "2025-02"
        assert error is None
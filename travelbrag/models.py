"""Data models for Travelbrag application."""

from dataclasses import dataclass
from typing import Optional
import pycountry


@dataclass
class City:
    """Represents a city with geographic information."""

    id: Optional[int]
    geonameid: int
    name: str
    admin_division: Optional[str]
    country: str
    latitude: str
    longitude: str

    @property
    def country_name(self) -> str:
        """Get the full country name from the ISO code."""
        try:
            country = pycountry.countries.get(alpha_2=self.country)
            return country.name if country else self.country
        except (AttributeError, KeyError):
            # Fallback to the stored value if conversion fails
            return self.country

    @property
    def display_name(self) -> str:
        """Get formatted display name for the city."""
        parts = [self.name]
        if self.admin_division:
            parts.append(self.admin_division)
        parts.append(self.country_name)
        return ", ".join(parts)

    @property
    def coordinates(self) -> tuple[float, float]:
        """Get latitude and longitude as floats."""
        return (float(self.latitude), float(self.longitude))


@dataclass
class Person:
    """Represents a family member who takes trips."""

    id: Optional[int]
    name: str


@dataclass
class Trip:
    """Represents a trip with metadata.

    Dates are stored as ISO format strings (YYYY-MM-DD or YYYY-MM).
    """

    id: Optional[int]
    name: str
    notes: Optional[str]
    start_date: str  # ISO format: YYYY-MM-DD or YYYY-MM
    end_date: str    # ISO format: YYYY-MM-DD or YYYY-MM

    def __post_init__(self):
        """Validate trip dates."""
        # Text comparison works for ISO format dates
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")


@dataclass
class TripCity:
    """Represents a city visited on a trip with optional notes."""

    trip_id: int
    city_id: int
    notes: Optional[str] = None

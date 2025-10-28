"""Statistics calculations for Travelbrag application."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
import pycountry

from .config import Config
from .repository import Repository
from .models import Trip, City, Person
from .date_parser import parse_iso_date, calculate_duration


# Canadian provinces and territories for tracking
# Provinces (west to east), then territories (west to east)
CANADIAN_PROVINCES = [
    # Provinces (west to east)
    "British Columbia",
    "Alberta",
    "Saskatchewan",
    "Manitoba",
    "Ontario",
    "Quebec",
    "New Brunswick",
    "Nova Scotia",
    "Prince Edward Island",
    "Newfoundland and Labrador",
    # Territories (west to east)
    "Yukon",
    "Northwest Territories",
    "Nunavut",
]


@dataclass
class TripInfo:
    """Information about a trip for statistics display."""
    trip: Trip
    days_ago: int


@dataclass
class GapInfo:
    """Information about a gap between trips."""
    days: int
    from_trip: Optional[Trip]
    to_trip: Optional[Trip]
    is_ongoing: bool


@dataclass
class CityVisitCount:
    """City visit count information."""
    city: City
    count: int


@dataclass
class LongestTripInfo:
    """Information about the longest trip."""
    trip: Trip
    duration_days: int


@dataclass
class PersonLongestTrips:
    """Information about a person's longest trips."""
    person: Person
    longest_domestic: Optional[LongestTripInfo]
    longest_international: Optional[LongestTripInfo]


@dataclass
class PersonYearAway:
    """Information about a person's longest time away in a year."""
    person: Person
    year: int
    days_away: int


@dataclass
class ProvinceVisitStatus:
    """Status of visits to a Canadian province/territory."""
    province: str
    status: str  # "none", "some", "all"
    visitors: list[str]  # Names of people who visited


def has_full_date_precision(date_str: str) -> bool:
    """Check if a date string has full precision (YYYY-MM-DD).

    Args:
        date_str: Date string in ISO format

    Returns:
        True if date is YYYY-MM-DD, False if YYYY-MM
    """
    return len(date_str) == 10


def get_person_statistics_cutoff(repo: Repository, person_id: int) -> Optional[str]:
    """Find the earliest trip start_date with full precision for a person.

    Args:
        repo: Repository instance
        person_id: Person ID

    Returns:
        The start_date string to use as cutoff, or None if no full-precision trips
    """
    trips = repo.get_person_trips(person_id)

    # Filter to trips with full precision (both start and end dates)
    full_precision_trips = [
        t for t in trips
        if has_full_date_precision(t.start_date) and has_full_date_precision(t.end_date)
    ]

    if not full_precision_trips:
        return None

    # Return the earliest start_date
    return min(t.start_date for t in full_precision_trips)


def is_domestic_trip(repo: Repository, trip: Trip, home_country: str) -> bool:
    """Check if a trip is domestic (all cities in home country).

    Args:
        repo: Repository instance
        trip: Trip to check
        home_country: ISO 3166-1 alpha-2 country code

    Returns:
        True if all cities are in home country
    """
    cities = repo.get_trip_cities(trip.id)
    if not cities:
        return False

    return all(c.country.upper() == home_country.upper() for c in cities)


def is_international_trip(repo: Repository, trip: Trip, home_country: str) -> bool:
    """Check if a trip is international (any city outside home country).

    Args:
        repo: Repository instance
        trip: Trip to check
        home_country: ISO 3166-1 alpha-2 country code

    Returns:
        True if any city is outside home country
    """
    cities = repo.get_trip_cities(trip.id)
    if not cities:
        return False

    return any(c.country.upper() != home_country.upper() for c in cities)


def get_last_domestic_trip(repo: Repository, config: Config) -> Optional[TripInfo]:
    """Get the last domestic trip.

    Args:
        repo: Repository instance
        config: Config instance

    Returns:
        TripInfo or None if no domestic trips found
    """
    home_country = config.home
    if not home_country:
        return None

    all_trips = repo.get_all_trips()  # Already sorted by start_date DESC

    # Filter to full-precision domestic trips
    for trip in all_trips:
        if (has_full_date_precision(trip.start_date) and
            has_full_date_precision(trip.end_date) and
            is_domestic_trip(repo, trip, home_country)):

            end_date = parse_iso_date(trip.end_date)
            if end_date:
                days_ago = (date.today() - end_date).days
                return TripInfo(trip=trip, days_ago=days_ago)

    return None


def get_last_international_trip(repo: Repository, config: Config) -> Optional[TripInfo]:
    """Get the last international trip.

    Args:
        repo: Repository instance
        config: Config instance

    Returns:
        TripInfo or None if no international trips found
    """
    home_country = config.home
    if not home_country:
        return None

    all_trips = repo.get_all_trips()  # Already sorted by start_date DESC

    # Filter to full-precision international trips
    for trip in all_trips:
        if (has_full_date_precision(trip.start_date) and
            has_full_date_precision(trip.end_date) and
            is_international_trip(repo, trip, home_country)):

            end_date = parse_iso_date(trip.end_date)
            if end_date:
                days_ago = (date.today() - end_date).days
                return TripInfo(trip=trip, days_ago=days_ago)

    return None


def calculate_trip_gaps(repo: Repository, config: Config,
                       trip_filter: Optional[str] = None) -> Optional[GapInfo]:
    """Calculate the longest gap between trips.

    Args:
        repo: Repository instance
        config: Config instance
        trip_filter: "domestic", "international", or None for all trips

    Returns:
        GapInfo for the longest gap, or None if not enough trips
    """
    home_country = config.home
    all_trips = repo.get_all_trips()

    # Filter to full-precision trips
    trips = [
        t for t in all_trips
        if has_full_date_precision(t.start_date) and has_full_date_precision(t.end_date)
    ]

    # Apply trip type filter
    if trip_filter == "domestic" and home_country:
        trips = [t for t in trips if is_domestic_trip(repo, t, home_country)]
    elif trip_filter == "international" and home_country:
        trips = [t for t in trips if is_international_trip(repo, t, home_country)]

    if len(trips) < 1:
        return None

    # Sort chronologically (oldest first)
    trips_chrono = sorted(trips, key=lambda t: t.start_date)

    max_gap = None
    max_gap_days = 0

    # Check gaps between consecutive trips
    for i in range(len(trips_chrono) - 1):
        end_date = parse_iso_date(trips_chrono[i].end_date)
        start_date = parse_iso_date(trips_chrono[i + 1].start_date)

        if end_date and start_date:
            gap_days = (start_date - end_date).days
            if gap_days > max_gap_days:
                max_gap_days = gap_days
                max_gap = GapInfo(
                    days=gap_days,
                    from_trip=trips_chrono[i],
                    to_trip=trips_chrono[i + 1],
                    is_ongoing=False
                )

    # Check gap from last trip to today
    if trips_chrono:
        last_trip_end = parse_iso_date(trips_chrono[-1].end_date)
        if last_trip_end:
            gap_to_today = (date.today() - last_trip_end).days
            if gap_to_today > max_gap_days:
                max_gap = GapInfo(
                    days=gap_to_today,
                    from_trip=trips_chrono[-1],
                    to_trip=None,
                    is_ongoing=True
                )

    return max_gap


def get_most_visited_cities(repo: Repository, config: Config, limit: int = 10) -> list[CityVisitCount]:
    """Get the most visited cities.

    This is a count-based statistic that includes all trips (including month-only dates).

    Args:
        repo: Repository instance
        config: Config instance
        limit: Maximum number of cities to return

    Returns:
        List of CityVisitCount ordered by visit count descending
    """
    # Count city visits by trip (not by person-visits)
    # Simply count how many trips included each city
    city_counts = {}
    all_trips = repo.get_all_trips()

    for trip in all_trips:
        # Count each city in this trip once (not once per person)
        cities = repo.get_trip_cities(trip.id)
        for city in cities:
            city_counts[city.id] = city_counts.get(city.id, 0) + 1

    # Convert to CityVisitCount objects
    results = []
    for city_id, count in city_counts.items():
        city = repo.get_city_by_id(city_id)
        if city:
            results.append(CityVisitCount(city=city, count=count))

    # Sort by count descending, then by name
    results.sort(key=lambda x: (-x.count, x.city.name))

    return results[:limit]


def get_longest_trips_per_person(repo: Repository, config: Config) -> list[PersonLongestTrips]:
    """Get the longest domestic and international trips for each person.

    Args:
        repo: Repository instance
        config: Config instance

    Returns:
        List of PersonLongestTrips objects
    """
    home_country = config.home
    if not home_country:
        return []

    people = repo.get_all_people()
    results = []

    for person in people:
        cutoff = get_person_statistics_cutoff(repo, person.id)
        if not cutoff:
            continue

        trips = repo.get_person_trips(person.id)

        # Filter to full-precision trips after cutoff
        full_trips = [
            t for t in trips
            if (t.start_date >= cutoff and
                has_full_date_precision(t.start_date) and
                has_full_date_precision(t.end_date))
        ]

        longest_domestic = None
        longest_international = None
        max_domestic_duration = 0
        max_international_duration = 0

        for trip in full_trips:
            try:
                duration = calculate_duration(trip.start_date, trip.end_date)

                if is_domestic_trip(repo, trip, home_country):
                    if duration > max_domestic_duration:
                        max_domestic_duration = duration
                        longest_domestic = LongestTripInfo(trip=trip, duration_days=duration)
                elif is_international_trip(repo, trip, home_country):
                    if duration > max_international_duration:
                        max_international_duration = duration
                        longest_international = LongestTripInfo(trip=trip, duration_days=duration)
            except ValueError:
                continue

        results.append(PersonLongestTrips(
            person=person,
            longest_domestic=longest_domestic,
            longest_international=longest_international
        ))

    # Sort by person name
    results.sort(key=lambda x: x.person.name)

    return results


def get_longest_time_away_per_person(repo: Repository, config: Config) -> list[PersonYearAway]:
    """Get the longest time away from home in a single year for each traveller.

    Args:
        repo: Repository instance
        config: Config instance

    Returns:
        List of PersonYearAway objects
    """
    home_country = config.home
    if not home_country:
        return []

    people = repo.get_all_people()
    results = []

    for person in people:
        cutoff = get_person_statistics_cutoff(repo, person.id)
        if not cutoff:
            continue

        trips = repo.get_person_trips(person.id)

        # Filter to full-precision international trips after cutoff
        int_trips = [
            t for t in trips
            if (t.start_date >= cutoff and
                has_full_date_precision(t.start_date) and
                has_full_date_precision(t.end_date) and
                is_international_trip(repo, t, home_country))
        ]

        if not int_trips:
            continue

        # Group trips by year and calculate total days away per year
        year_days = {}

        for trip in int_trips:
            start = parse_iso_date(trip.start_date)
            end = parse_iso_date(trip.end_date)

            if not start or not end:
                continue

            # For simplicity, assign trip to year of start_date
            # (Could be improved to handle trips spanning multiple years)
            year = start.year

            try:
                duration = calculate_duration(trip.start_date, trip.end_date)
                year_days[year] = year_days.get(year, 0) + duration
            except ValueError:
                continue

        if year_days:
            max_year = max(year_days.items(), key=lambda x: x[1])
            results.append(PersonYearAway(
                person=person,
                year=max_year[0],
                days_away=max_year[1]
            ))

    # Sort by person name
    results.sort(key=lambda x: x.person.name)

    return results


def get_countries_last_5_years_per_person(repo: Repository, config: Config) -> dict[str, list[str]]:
    """Get countries visited in the last 5 years for each traveller.

    Includes all trips (including month-only dates) from the last 5 years.

    Args:
        repo: Repository instance
        config: Config instance

    Returns:
        Dictionary mapping person name to list of country names
    """
    # Calculate 5 years ago date
    five_years_ago = date.today().replace(year=date.today().year - 5)
    cutoff_date = five_years_ago.isoformat()

    people = repo.get_all_people()
    results = {}

    for person in people:
        trips = repo.get_person_trips(person.id)

        # Get all countries from trips in the last 5 years
        countries = set()
        for trip in trips:
            if trip.end_date >= cutoff_date:
                cities = repo.get_trip_cities(trip.id)
                for city in cities:
                    countries.add(city.country)

        # Convert country codes to names
        country_names = []
        for code in sorted(countries):
            try:
                country = pycountry.countries.get(alpha_2=code)
                country_names.append(country.name if country else code)
            except (AttributeError, KeyError):
                country_names.append(code)

        results[person.name] = country_names

    return results


def get_canadian_province_visits(repo: Repository, config: Config) -> list[ProvinceVisitStatus]:
    """Get visit status for Canadian provinces and territories.

    This is a count-based statistic that includes all trips.

    Args:
        repo: Repository instance
        config: Config instance

    Returns:
        List of ProvinceVisitStatus objects
    """
    people = repo.get_all_people()
    all_people_names = {p.name for p in people}

    results = []

    for province in CANADIAN_PROVINCES:
        visitors = set()

        # Check each person's trips
        for person in people:
            trips = repo.get_person_trips(person.id)

            # Check if person visited this province in any trip
            for trip in trips:
                cities = repo.get_trip_cities(trip.id)
                for city in cities:
                    if (city.country.upper() == "CA" and
                        city.admin_division == province):
                        visitors.add(person.name)
                        break

        # Determine status
        if not visitors:
            status = "none"
            status_symbol = "❌"
        elif visitors == all_people_names:
            status = "all"
            status_symbol = "✅"
        else:
            status = "some"
            status_symbol = "☑️"

        results.append(ProvinceVisitStatus(
            province=f"{status_symbol} {province}",
            status=status,
            visitors=sorted(visitors)
        ))

    return results

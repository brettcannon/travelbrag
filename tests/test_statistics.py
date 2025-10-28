"""Tests for statistics calculations."""

import pytest
import tempfile
from pathlib import Path
from datetime import date, timedelta
from unittest.mock import Mock

from travelbrag.database import Database
from travelbrag.repository import Repository
from travelbrag.config import Config
from travelbrag.models import Person, Trip, City
from travelbrag import statistics


@pytest.fixture
def repo():
    """Create a repository with initialized database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        schema_path = Path(__file__).parent.parent / "schema.sql"

        db = Database(db_path)
        db.initialize_schema(schema_path)

        repository = Repository(db)
        yield repository

        db.close()


@pytest.fixture
def config():
    """Create a mock config for testing."""
    config = Mock(spec=Config)
    config.home = "CA"
    return config


@pytest.fixture
def sample_data(repo):
    """Create sample test data."""
    # Add people
    person1 = repo.add_person(Person(id=None, name="Alice"))
    person2 = repo.add_person(Person(id=None, name="Bob"))

    # Add cities
    city_toronto = repo.add_city(City(
        id=None, geonameid=6167865, name="Toronto",
        admin_division="Ontario", country="CA",
        latitude="43.70011", longitude="-79.4163"
    ))
    city_vancouver = repo.add_city(City(
        id=None, geonameid=6173331, name="Vancouver",
        admin_division="British Columbia", country="CA",
        latitude="49.24966", longitude="-123.11934"
    ))
    city_paris = repo.add_city(City(
        id=None, geonameid=2988507, name="Paris",
        admin_division=None, country="FR",
        latitude="48.85341", longitude="2.3488"
    ))
    city_london = repo.add_city(City(
        id=None, geonameid=2643743, name="London",
        admin_division=None, country="GB",
        latitude="51.50853", longitude="-0.12574"
    ))

    # Add trips with full precision dates
    today = date.today()

    # Recent domestic trip (10 days ago)
    trip1 = repo.add_trip(Trip(
        id=None, name="Toronto Weekend",
        notes=None,
        start_date=(today - timedelta(days=12)).isoformat(),
        end_date=(today - timedelta(days=10)).isoformat()
    ))
    repo.add_trip_participant(trip1.id, person1.id)
    repo.add_trip_city(trip1.id, city_toronto.id)

    # Recent international trip (5 days ago)
    trip2 = repo.add_trip(Trip(
        id=None, name="Paris Trip",
        notes=None,
        start_date=(today - timedelta(days=7)).isoformat(),
        end_date=(today - timedelta(days=5)).isoformat()
    ))
    repo.add_trip_participant(trip2.id, person1.id)
    repo.add_trip_participant(trip2.id, person2.id)
    repo.add_trip_city(trip2.id, city_paris.id)

    # Older domestic trip (100 days ago, long duration)
    trip3 = repo.add_trip(Trip(
        id=None, name="Cross Canada Tour",
        notes=None,
        start_date=(today - timedelta(days=130)).isoformat(),
        end_date=(today - timedelta(days=100)).isoformat()
    ))
    repo.add_trip_participant(trip3.id, person1.id)
    repo.add_trip_city(trip3.id, city_toronto.id)
    repo.add_trip_city(trip3.id, city_vancouver.id)

    # Very old trip with only YYYY-MM dates (should be excluded from date-based stats)
    trip4 = repo.add_trip(Trip(
        id=None, name="Old Trip",
        notes=None,
        start_date="2020-05",
        end_date="2020-06"
    ))
    repo.add_trip_participant(trip4.id, person1.id)
    repo.add_trip_city(trip4.id, city_london.id)

    # International trip from last year
    trip5 = repo.add_trip(Trip(
        id=None, name="London Visit",
        notes=None,
        start_date=(today.replace(year=today.year - 1) + timedelta(days=10)).isoformat(),
        end_date=(today.replace(year=today.year - 1) + timedelta(days=20)).isoformat()
    ))
    repo.add_trip_participant(trip5.id, person2.id)
    repo.add_trip_city(trip5.id, city_london.id)

    return {
        "people": [person1, person2],
        "cities": [city_toronto, city_vancouver, city_paris, city_london],
        "trips": [trip1, trip2, trip3, trip4, trip5]
    }


def test_has_full_date_precision():
    """Test date precision detection."""
    assert statistics.has_full_date_precision("2024-07-15") is True
    assert statistics.has_full_date_precision("2024-07") is False
    assert statistics.has_full_date_precision("2024") is False


def test_get_person_statistics_cutoff(repo, sample_data):
    """Test finding the earliest full-precision trip for a person."""
    person1 = sample_data["people"][0]

    cutoff = statistics.get_person_statistics_cutoff(repo, person1.id)

    # Should return the earliest full-precision trip (Cross Canada Tour in this case)
    assert cutoff is not None
    # The cutoff should exclude the old YYYY-MM trip
    assert len(cutoff) == 10  # Full precision date


def test_get_person_statistics_cutoff_no_trips(repo):
    """Test cutoff when person has no full-precision trips."""
    person = repo.add_person(Person(id=None, name="NewPerson"))

    cutoff = statistics.get_person_statistics_cutoff(repo, person.id)

    assert cutoff is None


def test_is_domestic_trip(repo, config, sample_data):
    """Test domestic trip detection."""
    trips = sample_data["trips"]

    # Trip 0 is Toronto Weekend (domestic)
    assert statistics.is_domestic_trip(repo, trips[0], config.home) is True

    # Trip 1 is Paris Trip (international)
    assert statistics.is_domestic_trip(repo, trips[1], config.home) is False


def test_is_international_trip(repo, config, sample_data):
    """Test international trip detection."""
    trips = sample_data["trips"]

    # Trip 0 is Toronto Weekend (not international)
    assert statistics.is_international_trip(repo, trips[0], config.home) is False

    # Trip 1 is Paris Trip (international)
    assert statistics.is_international_trip(repo, trips[1], config.home) is True


def test_get_last_domestic_trip(repo, config, sample_data):
    """Test getting the last domestic trip."""
    result = statistics.get_last_domestic_trip(repo, config)

    assert result is not None
    assert result.trip.name == "Toronto Weekend"
    assert result.days_ago == 10


def test_get_last_international_trip(repo, config, sample_data):
    """Test getting the last international trip."""
    result = statistics.get_last_international_trip(repo, config)

    assert result is not None
    assert result.trip.name == "Paris Trip"
    assert result.days_ago == 5


def test_get_last_trips_no_home_country(repo, sample_data):
    """Test getting last trips when no home country is configured."""
    config_no_home = Mock(spec=Config)
    config_no_home.home = None

    result_domestic = statistics.get_last_domestic_trip(repo, config_no_home)
    result_international = statistics.get_last_international_trip(repo, config_no_home)

    assert result_domestic is None
    assert result_international is None


def test_calculate_trip_gaps_all(repo, config, sample_data):
    """Test calculating longest gap between all trips."""
    result = statistics.calculate_trip_gaps(repo, config)

    assert result is not None
    # Should find the longest gap between any trips
    assert result.days > 0
    assert result.from_trip is not None
    # May or may not be ongoing depending on gap calculation


def test_calculate_trip_gaps_domestic(repo, config, sample_data):
    """Test calculating longest gap between domestic trips."""
    result = statistics.calculate_trip_gaps(repo, config, trip_filter="domestic")

    assert result is not None
    # Should find a gap between domestic trips
    assert result.days > 0


def test_calculate_trip_gaps_international(repo, config, sample_data):
    """Test calculating longest gap between international trips."""
    result = statistics.calculate_trip_gaps(repo, config, trip_filter="international")

    assert result is not None
    # Should find a gap between international trips
    assert result.days > 0


def test_get_most_visited_cities(repo, config, sample_data):
    """Test getting most visited cities."""
    result = statistics.get_most_visited_cities(repo, config, limit=10)

    # Toronto: 2 trips (Toronto Weekend, Cross Canada Tour)
    # Vancouver: 1 trip (Cross Canada Tour)
    # Paris: 1 trip (Paris Trip - even though 2 people participated)
    # London: 2 trips (London Visit + Old Trip, both counted as this is count-based)
    assert len(result) > 0

    # Find Toronto in results
    toronto_result = next((r for r in result if r.city.name == "Toronto"), None)
    assert toronto_result is not None
    assert toronto_result.count == 2  # Visited on 2 trips

    # Find Paris in results - should count as 1 trip even though 2 people went
    paris_result = next((r for r in result if r.city.name == "Paris"), None)
    assert paris_result is not None
    assert paris_result.count == 1  # Only 1 trip, not 2 person-visits

    # Find London - should count both trips including the month-only one
    london_result = next((r for r in result if r.city.name == "London"), None)
    assert london_result is not None
    assert london_result.count == 2  # Old Trip (month-only) + London Visit


def test_get_longest_trips_per_person(repo, config, sample_data):
    """Test getting the longest trips per person."""
    result = statistics.get_longest_trips_per_person(repo, config)

    # Alice should have results (has both domestic and international trips)
    alice_result = next((r for r in result if r.person.name == "Alice"), None)
    assert alice_result is not None
    # Cross Canada Tour is 31 days (domestic)
    assert alice_result.longest_domestic is not None
    assert alice_result.longest_domestic.trip.name == "Cross Canada Tour"
    assert alice_result.longest_domestic.duration_days == 31
    # Should have an international trip too
    assert alice_result.longest_international is not None

    # Bob should have results
    bob_result = next((r for r in result if r.person.name == "Bob"), None)
    assert bob_result is not None


def test_get_longest_trips_no_trips(repo, config):
    """Test getting longest trips when no trips exist."""
    result = statistics.get_longest_trips_per_person(repo, config)

    assert result == []


def test_get_longest_time_away_per_person(repo, config, sample_data):
    """Test getting longest time away from home per person."""
    result = statistics.get_longest_time_away_per_person(repo, config)

    # Alice should have international trip (Paris Trip)
    alice_result = next((r for r in result if r.person.name == "Alice"), None)
    assert alice_result is not None
    assert alice_result.days_away > 0

    # Bob should have international trip (London Visit and Paris Trip)
    bob_result = next((r for r in result if r.person.name == "Bob"), None)
    assert bob_result is not None


def test_get_countries_last_5_years_per_person(repo, config, sample_data):
    """Test getting countries visited in last 5 years per person."""
    result = statistics.get_countries_last_5_years_per_person(repo, config)

    assert "Alice" in result
    assert "Bob" in result

    # Alice should have visited CA and FR (Toronto Weekend, Cross Canada, Paris Trip)
    assert "Canada" in result["Alice"]
    assert "France" in result["Alice"]

    # Bob should have visited FR and GB (Paris Trip, London Visit)
    assert "France" in result["Bob"]
    assert "United Kingdom" in result["Bob"]


def test_get_canadian_province_visits(repo, config, sample_data):
    """Test getting Canadian province visit status."""
    result = statistics.get_canadian_province_visits(repo, config)

    assert len(result) == 13  # All Canadian provinces and territories

    # Find Ontario
    ontario = next((r for r in result if "Ontario" in r.province), None)
    assert ontario is not None
    assert "Alice" in ontario.visitors

    # Find British Columbia
    bc = next((r for r in result if "British Columbia" in r.province), None)
    assert bc is not None
    assert "Alice" in bc.visitors

    # Find a province with no visits (e.g., Alberta)
    alberta = next((r for r in result if "Alberta" in r.province), None)
    assert alberta is not None
    assert len(alberta.visitors) == 0
    assert "❌" in alberta.province


def test_canadian_province_visits_all_travelers(repo, config):
    """Test Canadian province visits when all travelers visited."""
    # Add people
    person1 = repo.add_person(Person(id=None, name="Alice"))
    person2 = repo.add_person(Person(id=None, name="Bob"))

    # Add Quebec city
    city_quebec = repo.add_city(City(
        id=None, geonameid=6325494, name="Quebec City",
        admin_division="Quebec", country="CA",
        latitude="46.81228", longitude="-71.21454"
    ))

    # Add trip to Quebec for both people
    today = date.today()
    trip = repo.add_trip(Trip(
        id=None, name="Quebec Trip",
        notes=None,
        start_date=(today - timedelta(days=10)).isoformat(),
        end_date=(today - timedelta(days=5)).isoformat()
    ))
    repo.add_trip_participant(trip.id, person1.id)
    repo.add_trip_participant(trip.id, person2.id)
    repo.add_trip_city(trip.id, city_quebec.id)

    result = statistics.get_canadian_province_visits(repo, config)

    # Find Quebec
    quebec = next((r for r in result if "Quebec" in r.province), None)
    assert quebec is not None
    assert "Alice" in quebec.visitors
    assert "Bob" in quebec.visitors
    assert "✅" in quebec.province  # All travelers visited

"""Test repository methods for city operations."""

import tempfile
from pathlib import Path

import pytest

from travelbrag.database import Database
from travelbrag.models import City, Trip
from travelbrag.repository import Repository


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


def test_get_visited_cities_by_country_empty(repo):
    """Test getting visited cities when none exist."""
    cities = repo.get_visited_cities_by_country("US")
    assert cities == []


def test_get_visited_cities_by_country(repo):
    """Test getting visited cities for a specific country."""
    # Add some cities
    sf = City(
        id=None,
        geonameid=5391959,
        name="San Francisco",
        admin_division="California",
        country="US",
        latitude=37.7749,
        longitude=-122.4194
    )
    la = City(
        id=None,
        geonameid=5368361,
        name="Los Angeles",
        admin_division="California",
        country="US",
        latitude=34.0522,
        longitude=-118.2437
    )
    vancouver = City(
        id=None,
        geonameid=6173331,
        name="Vancouver",
        admin_division="British Columbia",
        country="CA",
        latitude=49.2827,
        longitude=-123.1207
    )
    paris = City(
        id=None,
        geonameid=2988507,
        name="Paris",
        admin_division="Île-de-France",
        country="FR",
        latitude=48.8566,
        longitude=2.3522
    )

    # Add cities to database
    sf = repo.add_city(sf)
    la = repo.add_city(la)
    vancouver = repo.add_city(vancouver)
    paris = repo.add_city(paris)

    # Create a trip and add cities
    trip = Trip(
        id=None,
        name="Test Trip",
        start_date="2024-01-01",
        end_date="2024-01-10",
        notes="Test trip"
    )
    trip = repo.add_trip(trip)

    # Add cities to trip
    repo.add_trip_city(trip.id, sf.id)
    repo.add_trip_city(trip.id, la.id)
    repo.add_trip_city(trip.id, vancouver.id)
    repo.add_trip_city(trip.id, paris.id)

    # Get US cities
    us_cities = repo.get_visited_cities_by_country("US")
    assert len(us_cities) == 2
    city_names = [c.name for c in us_cities]
    assert "Los Angeles" in city_names  # Alphabetical order
    assert "San Francisco" in city_names

    # Get Canadian cities
    ca_cities = repo.get_visited_cities_by_country("CA")
    assert len(ca_cities) == 1
    assert ca_cities[0].name == "Vancouver"

    # Get French cities
    fr_cities = repo.get_visited_cities_by_country("FR")
    assert len(fr_cities) == 1
    assert fr_cities[0].name == "Paris"

    # Get cities for country with no visits
    jp_cities = repo.get_visited_cities_by_country("JP")
    assert jp_cities == []


def test_get_visited_cities_by_country_case_insensitive(repo):
    """Test that country code comparison is case insensitive."""
    # Add a city
    city = City(
        id=None,
        geonameid=5391959,
        name="San Francisco",
        admin_division="California",
        country="US",  # Full name in database
        latitude=37.7749,
        longitude=-122.4194
    )
    city = repo.add_city(city)

    # Create a trip and add city
    trip = Trip(
        id=None,
        name="Test Trip",
        start_date="2024-01-01",
        end_date="2024-01-10",
        notes="Test trip"
    )
    trip = repo.add_trip(trip)
    repo.add_trip_city(trip.id, city.id)

    # Test with lowercase
    cities = repo.get_visited_cities_by_country("us")
    assert len(cities) == 1
    assert cities[0].name == "San Francisco"

    # Test with uppercase
    cities = repo.get_visited_cities_by_country("US")
    assert len(cities) == 1
    assert cities[0].name == "San Francisco"


def test_get_visited_cities_by_country_unique(repo):
    """Test that cities are unique even if visited on multiple trips."""
    # Add a city
    city = City(
        id=None,
        geonameid=5391959,
        name="San Francisco",
        admin_division="California",
        country="US",
        latitude=37.7749,
        longitude=-122.4194
    )
    city = repo.add_city(city)

    # Create two trips and add the same city to both
    trip1 = Trip(
        id=None,
        name="Trip 1",
        start_date="2024-01-01",
        end_date="2024-01-10",
        notes="First trip"
    )
    trip1 = repo.add_trip(trip1)
    repo.add_trip_city(trip1.id, city.id)

    trip2 = Trip(
        id=None,
        name="Trip 2",
        start_date="2024-02-01",
        end_date="2024-02-10",
        notes="Second trip"
    )
    trip2 = repo.add_trip(trip2)
    repo.add_trip_city(trip2.id, city.id)

    # Should only return the city once
    cities = repo.get_visited_cities_by_country("US")
    assert len(cities) == 1
    assert cities[0].name == "San Francisco"


def test_get_visited_cities_by_country_alphabetical(repo):
    """Test that cities are returned in alphabetical order."""
    # Add cities in non-alphabetical order
    cities_data = [
        ("Zurich", "CH"),
        ("Amsterdam", "NL"),
        ("Berlin", "DE"),
        ("Copenhagen", "DK"),
    ]

    trip = Trip(
        id=None,
        name="European Tour",
        start_date="2024-01-01",
        end_date="2024-01-20",
        notes="Tour of Europe"
    )
    trip = repo.add_trip(trip)

    # Add multiple cities to the same country to test ordering
    for i, (city_name, _) in enumerate(cities_data):
        city = City(
            id=None,
            geonameid=1000 + i,
            name=city_name,
            admin_division="State",
            country="US",  # Put them all in US for testing
            latitude=0.0,
            longitude=0.0
        )
        city = repo.add_city(city)
        repo.add_trip_city(trip.id, city.id)

    # Get cities - should be alphabetically ordered
    us_cities = repo.get_visited_cities_by_country("US")
    assert len(us_cities) == 4
    city_names = [c.name for c in us_cities]
    assert city_names == ["Amsterdam", "Berlin", "Copenhagen", "Zurich"]
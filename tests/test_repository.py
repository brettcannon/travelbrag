"""Tests for repository layer."""

import pytest
import tempfile
from pathlib import Path

from travelbrag.database import Database
from travelbrag.repository import Repository
from travelbrag.models import Person, Trip, City


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


def test_add_and_get_person(repo):
    """Test adding and retrieving a person."""
    person = Person(id=None, name="John Doe")
    added_person = repo.add_person(person)

    assert added_person.id is not None
    assert added_person.name == "John Doe"

    retrieved_person = repo.get_person_by_id(added_person.id)
    assert retrieved_person.name == "John Doe"


def test_get_person_by_name(repo):
    """Test retrieving person by name."""
    person = Person(id=None, name="Jane Smith")
    repo.add_person(person)

    retrieved_person = repo.get_person_by_name("Jane Smith")
    assert retrieved_person is not None
    assert retrieved_person.name == "Jane Smith"


def test_update_person(repo):
    """Test updating person name."""
    person = Person(id=None, name="Old Name")
    added_person = repo.add_person(person)

    added_person.name = "New Name"
    repo.update_person(added_person)

    retrieved_person = repo.get_person_by_id(added_person.id)
    assert retrieved_person.name == "New Name"


def test_delete_person(repo):
    """Test deleting a person."""
    person = Person(id=None, name="To Delete")
    added_person = repo.add_person(person)

    repo.delete_person(added_person.id)

    retrieved_person = repo.get_person_by_id(added_person.id)
    assert retrieved_person is None


def test_get_all_people(repo):
    """Test retrieving all people."""
    repo.add_person(Person(id=None, name="Person A"))
    repo.add_person(Person(id=None, name="Person B"))
    repo.add_person(Person(id=None, name="Person C"))

    people = repo.get_all_people()
    assert len(people) == 3
    names = {p.name for p in people}
    assert names == {"Person A", "Person B", "Person C"}


def test_add_and_get_trip(repo):
    """Test adding and retrieving a trip."""
    trip = Trip(
        id=None,
        name="Summer Vacation",
        notes="Great trip!",
        start_date="2024-07-01",
        end_date="2024-07-15"
    )
    added_trip = repo.add_trip(trip)

    assert added_trip.id is not None

    retrieved_trip = repo.get_trip_by_id(added_trip.id)
    assert retrieved_trip.name == "Summer Vacation"
    assert retrieved_trip.start_date == "2024-07-01"
    assert retrieved_trip.end_date == "2024-07-15"


def test_update_trip(repo):
    """Test updating trip details."""
    trip = Trip(
        id=None,
        name="Old Trip",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-05"
    )
    added_trip = repo.add_trip(trip)

    added_trip.name = "Updated Trip"
    added_trip.notes = "Updated notes"
    repo.update_trip(added_trip)

    retrieved_trip = repo.get_trip_by_id(added_trip.id)
    assert retrieved_trip.name == "Updated Trip"
    assert retrieved_trip.notes == "Updated notes"


def test_delete_trip(repo):
    """Test deleting a trip."""
    trip = Trip(
        id=None,
        name="To Delete",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-02"
    )
    added_trip = repo.add_trip(trip)

    repo.delete_trip(added_trip.id)

    retrieved_trip = repo.get_trip_by_id(added_trip.id)
    assert retrieved_trip is None


def test_add_and_get_city(repo):
    """Test adding and retrieving a city."""
    city = City(
        id=None,
        geonameid=5391959,
        name="San Francisco",
        admin_division="California",
        country="US",
        latitude="37.7749",
        longitude="-122.4194"
    )
    added_city = repo.add_city(city)

    assert added_city.id is not None

    retrieved_city = repo.get_city_by_id(added_city.id)
    assert retrieved_city.name == "San Francisco"
    assert retrieved_city.country == "US"


def test_get_city_by_geonameid(repo):
    """Test retrieving city by GeoNames ID."""
    city = City(
        id=None,
        geonameid=5391959,
        name="San Francisco",
        admin_division="California",
        country="US",
        latitude="37.7749",
        longitude="-122.4194"
    )
    repo.add_city(city)

    retrieved_city = repo.get_city_by_geonameid(5391959)
    assert retrieved_city is not None
    assert retrieved_city.name == "San Francisco"


def test_get_or_create_city(repo):
    """Test get or create city logic."""
    city = City(
        id=None,
        geonameid=5391959,
        name="San Francisco",
        admin_division="California",
        country="US",
        latitude="37.7749",
        longitude="-122.4194"
    )

    # First call should create
    city1 = repo.get_or_create_city(city)
    assert city1.id is not None

    # Second call should return existing
    city2 = repo.get_or_create_city(city)
    assert city2.id == city1.id


def test_trip_participants(repo):
    """Test adding and retrieving trip participants."""
    person1 = repo.add_person(Person(id=None, name="Alice"))
    person2 = repo.add_person(Person(id=None, name="Bob"))
    trip = repo.add_trip(Trip(
        id=None,
        name="Trip",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-02"
    ))

    repo.add_trip_participant(trip.id, person1.id)
    repo.add_trip_participant(trip.id, person2.id)

    participants = repo.get_trip_participants(trip.id)
    assert len(participants) == 2
    names = {p.name for p in participants}
    assert names == {"Alice", "Bob"}


def test_remove_trip_participant(repo):
    """Test removing trip participant."""
    person = repo.add_person(Person(id=None, name="Alice"))
    trip = repo.add_trip(Trip(
        id=None,
        name="Trip",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-02"
    ))

    repo.add_trip_participant(trip.id, person.id)
    repo.remove_trip_participant(trip.id, person.id)

    participants = repo.get_trip_participants(trip.id)
    assert len(participants) == 0


def test_person_trips(repo):
    """Test retrieving trips for a person."""
    person = repo.add_person(Person(id=None, name="Alice"))
    trip1 = repo.add_trip(Trip(
        id=None,
        name="Trip 1",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-02"
    ))
    trip2 = repo.add_trip(Trip(
        id=None,
        name="Trip 2",
        notes=None,
        start_date="2024-02-01",
        end_date="2024-02-02"
    ))

    repo.add_trip_participant(trip1.id, person.id)
    repo.add_trip_participant(trip2.id, person.id)

    trips = repo.get_person_trips(person.id)
    assert len(trips) == 2
    names = {t.name for t in trips}
    assert names == {"Trip 1", "Trip 2"}


def test_trip_cities(repo):
    """Test adding and retrieving cities for a trip."""
    trip = repo.add_trip(Trip(
        id=None,
        name="Trip",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-02"
    ))
    city1 = repo.add_city(City(
        id=None,
        geonameid=1,
        name="City A",
        admin_division=None,
        country="US",
        latitude="0",
        longitude="0"
    ))
    city2 = repo.add_city(City(
        id=None,
        geonameid=2,
        name="City B",
        admin_division=None,
        country="GB",
        latitude="1",
        longitude="1"
    ))

    repo.add_trip_city(trip.id, city1.id, "Great city!")
    repo.add_trip_city(trip.id, city2.id)

    cities = repo.get_trip_cities(trip.id)
    assert len(cities) == 2
    names = {c.name for c in cities}
    assert names == {"City A", "City B"}


def test_city_trips(repo):
    """Test retrieving all trips that include a specific city."""
    city = repo.add_city(City(
        id=None,
        geonameid=1,
        name="Paris",
        admin_division=None,
        country="FR",
        latitude="48.8566",
        longitude="2.3522"
    ))
    trip1 = repo.add_trip(Trip(
        id=None,
        name="Europe Trip",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-10"
    ))
    trip2 = repo.add_trip(Trip(
        id=None,
        name="France Visit",
        notes=None,
        start_date="2024-06-01",
        end_date="2024-06-05"
    ))
    trip3 = repo.add_trip(Trip(
        id=None,
        name="Spain Trip",
        notes=None,
        start_date="2024-08-01",
        end_date="2024-08-05"
    ))

    # Add Paris to trip1 and trip2, but not trip3
    repo.add_trip_city(trip1.id, city.id)
    repo.add_trip_city(trip2.id, city.id)

    # Get all trips for Paris
    trips = repo.get_city_trips(city.id)
    assert len(trips) == 2
    names = {t.name for t in trips}
    assert names == {"Europe Trip", "France Visit"}
    # Verify reverse chronological order
    assert trips[0].name == "France Visit"  # 2024-06-01 is more recent
    assert trips[1].name == "Europe Trip"    # 2024-01-01 is older


def test_person_cities(repo):
    """Test retrieving all cities visited by a person."""
    person = repo.add_person(Person(id=None, name="Alice"))
    trip1 = repo.add_trip(Trip(
        id=None,
        name="Trip 1",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-02"
    ))
    trip2 = repo.add_trip(Trip(
        id=None,
        name="Trip 2",
        notes=None,
        start_date="2024-02-01",
        end_date="2024-02-02"
    ))
    city1 = repo.add_city(City(
        id=None,
        geonameid=1,
        name="City A",
        admin_division=None,
        country="US",
        latitude="0",
        longitude="0"
    ))
    city2 = repo.add_city(City(
        id=None,
        geonameid=2,
        name="City B",
        admin_division=None,
        country="GB",
        latitude="1",
        longitude="1"
    ))

    repo.add_trip_participant(trip1.id, person.id)
    repo.add_trip_participant(trip2.id, person.id)
    repo.add_trip_city(trip1.id, city1.id)
    repo.add_trip_city(trip2.id, city2.id)

    cities = repo.get_person_cities(person.id)
    assert len(cities) == 2
    names = {c.name for c in cities}
    assert names == {"City A", "City B"}


def test_orphaned_city_cleanup_on_remove(repo):
    """Test that cities not attached to any trip are removed when city is removed from trip."""
    trip = repo.add_trip(Trip(
        id=None,
        name="Trip",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-02"
    ))
    city = repo.add_city(City(
        id=None,
        geonameid=1,
        name="Orphan City",
        admin_division=None,
        country="TC",
        latitude="0",
        longitude="0"
    ))

    # Add city to trip
    repo.add_trip_city(trip.id, city.id)

    # Verify city exists
    all_cities = repo.get_all_cities()
    assert len(all_cities) == 1
    assert all_cities[0].name == "Orphan City"

    # Remove city from trip - should trigger cleanup
    repo.remove_trip_city(trip.id, city.id)

    # Verify city was removed from database
    all_cities = repo.get_all_cities()
    assert len(all_cities) == 0


def test_orphaned_city_cleanup_on_trip_delete(repo):
    """Test that cities not attached to any trip are removed when trip is deleted."""
    trip = repo.add_trip(Trip(
        id=None,
        name="Trip",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-02"
    ))
    city = repo.add_city(City(
        id=None,
        geonameid=1,
        name="Orphan City",
        admin_division=None,
        country="TC",
        latitude="0",
        longitude="0"
    ))

    # Add city to trip
    repo.add_trip_city(trip.id, city.id)

    # Verify city exists
    all_cities = repo.get_all_cities()
    assert len(all_cities) == 1

    # Delete trip - should trigger cleanup via CASCADE and cleanup method
    repo.delete_trip(trip.id)

    # Verify city was removed from database
    all_cities = repo.get_all_cities()
    assert len(all_cities) == 0


def test_city_not_removed_when_still_attached(repo):
    """Test that cities are not removed when still attached to other trips."""
    trip1 = repo.add_trip(Trip(
        id=None,
        name="Trip 1",
        notes=None,
        start_date="2024-01-01",
        end_date="2024-01-02"
    ))
    trip2 = repo.add_trip(Trip(
        id=None,
        name="Trip 2",
        notes=None,
        start_date="2024-02-01",
        end_date="2024-02-02"
    ))
    city = repo.add_city(City(
        id=None,
        geonameid=1,
        name="Shared City",
        admin_division=None,
        country="TC",
        latitude="0",
        longitude="0"
    ))

    # Add city to both trips
    repo.add_trip_city(trip1.id, city.id)
    repo.add_trip_city(trip2.id, city.id)

    # Remove city from first trip
    repo.remove_trip_city(trip1.id, city.id)

    # Verify city still exists (attached to trip2)
    all_cities = repo.get_all_cities()
    assert len(all_cities) == 1
    assert all_cities[0].name == "Shared City"

    # Delete first trip
    repo.delete_trip(trip1.id)

    # Verify city still exists (still attached to trip2)
    all_cities = repo.get_all_cities()
    assert len(all_cities) == 1
    assert all_cities[0].name == "Shared City"

def test_trip_city_notes(repo):
    """Test adding and updating notes for cities in trips."""
    # Create a trip
    trip = Trip(
        id=None,
        name="European Adventure",
        start_date="2024-06-01",
        end_date="2024-06-15",
        notes="Summer vacation"
    )
    trip = repo.add_trip(trip)

    # Create a city
    city = City(
        id=None,
        name="Paris",
        latitude=48.8566,
        longitude=2.3522,
        country="FR",
        admin_division="Île-de-France",
        geonameid=2988507,
    )
    city = repo.get_or_create_city(city)
    
    # Add city to trip with notes
    repo.add_trip_city(trip.id, city.id, "Visit the Eiffel Tower")
    
    # Get cities with notes
    cities_with_notes = repo.get_trip_cities_with_notes(trip.id)
    
    assert len(cities_with_notes) == 1
    city_result, notes = cities_with_notes[0]
    assert city_result.name == "Paris"
    assert notes == "Visit the Eiffel Tower"
    
    # Update notes
    repo.update_trip_city_notes(trip.id, city.id, "Loved the Louvre!")
    cities_with_notes = repo.get_trip_cities_with_notes(trip.id)
    
    city_result, notes = cities_with_notes[0]
    assert notes == "Loved the Louvre!"
    
    # Add city without notes
    city2 = City(
        id=None,
        name="London",
        latitude=51.5074,
        longitude=-0.1278,
        country="GB",
        admin_division="England",
        geonameid=2643743,
    )
    city2 = repo.get_or_create_city(city2)
    repo.add_trip_city(trip.id, city2.id)
    
    # Check both cities
    cities_with_notes = repo.get_trip_cities_with_notes(trip.id)
    assert len(cities_with_notes) == 2
    
    # Find London (no notes)
    london_result = next((c for c, n in cities_with_notes if c.name == "London"), None)
    assert london_result is not None
    london_notes = next((n for c, n in cities_with_notes if c.name == "London"), None)
    assert london_notes is None

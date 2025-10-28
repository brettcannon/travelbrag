"""Tests for GeoJSON export functionality."""

import json
import pytest
import tempfile
from pathlib import Path

from travelbrag.database import Database
from travelbrag.repository import Repository
from travelbrag.models import City, Trip
from travelbrag.geojson_export import generate_geojson, export_geojson


@pytest.fixture
def db_with_data():
    """Create a database with sample data for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        schema_path = Path(__file__).parent.parent / "schema.sql"

        db = Database(db_path)
        db.initialize_schema(schema_path)
        repo = Repository(db)

        # Create some cities
        paris = City(
            id=None,
            geonameid=2988507,
            name="Paris",
            admin_division="Île-de-France",
            country="FR",
            latitude="48.8566",
            longitude="2.3522"
        )
        paris = repo.add_city(paris)

        london = City(
            id=None,
            geonameid=2643743,
            name="London",
            admin_division="England",
            country="GB",
            latitude="51.5074",
            longitude="-0.1278"
        )
        london = repo.add_city(london)

        tokyo = City(
            id=None,
            geonameid=1850144,
            name="Tokyo",
            admin_division="Tokyo",
            country="JP",
            latitude="35.6762",
            longitude="139.6503"
        )
        tokyo = repo.add_city(tokyo)

        # Create trips
        trip1 = Trip(
            id=None,
            name="Europe 2023",
            notes="Summer vacation",
            start_date="2023-06-01",
            end_date="2023-06-15"
        )
        trip1 = repo.add_trip(trip1)

        trip2 = Trip(
            id=None,
            name="Europe Again 2024",
            notes="Another trip",
            start_date="2024-07-01",
            end_date="2024-07-10"
        )
        trip2 = repo.add_trip(trip2)

        trip3 = Trip(
            id=None,
            name="Asia 2024",
            notes="Work trip",
            start_date="2024-09-01",
            end_date="2024-09-07"
        )
        trip3 = repo.add_trip(trip3)

        # Associate cities with trips
        # Paris visited twice (trip1 and trip2)
        repo.add_trip_city(trip1.id, paris.id)
        repo.add_trip_city(trip2.id, paris.id)
        # London visited once (trip1)
        repo.add_trip_city(trip1.id, london.id)
        # Tokyo visited once (trip3)
        repo.add_trip_city(trip3.id, tokyo.id)

        yield db

        db.close()


def test_generate_geojson_structure(db_with_data):
    """Test that generated GeoJSON has correct structure."""
    geojson = generate_geojson(db_with_data)

    # Check top-level structure
    assert geojson["type"] == "FeatureCollection"
    assert "features" in geojson
    assert isinstance(geojson["features"], list)


def test_generate_geojson_features(db_with_data):
    """Test that GeoJSON features have correct data."""
    geojson = generate_geojson(db_with_data)

    features = geojson["features"]
    assert len(features) == 3  # Paris, London, Tokyo

    # Find Paris feature
    paris_feature = next((f for f in features if f["properties"]["name"] == "Paris"), None)
    assert paris_feature is not None

    # Check geometry
    assert paris_feature["type"] == "Feature"
    assert paris_feature["geometry"]["type"] == "Point"
    assert len(paris_feature["geometry"]["coordinates"]) == 2
    # GeoJSON uses [longitude, latitude] order
    assert paris_feature["geometry"]["coordinates"][0] == pytest.approx(2.3522, abs=0.0001)
    assert paris_feature["geometry"]["coordinates"][1] == pytest.approx(48.8566, abs=0.0001)

    # Check properties
    assert paris_feature["properties"]["name"] == "Paris"
    assert paris_feature["properties"]["visit count"] == 2  # Visited on two trips
    assert paris_feature["properties"]["last visit"] == 2024  # From trip2


def test_generate_geojson_visit_counts(db_with_data):
    """Test that visit counts are calculated correctly."""
    geojson = generate_geojson(db_with_data)

    features = geojson["features"]

    # Check visit counts
    paris = next(f for f in features if f["properties"]["name"] == "Paris")
    assert paris["properties"]["visit count"] == 2

    london = next(f for f in features if f["properties"]["name"] == "London")
    assert london["properties"]["visit count"] == 1

    tokyo = next(f for f in features if f["properties"]["name"] == "Tokyo")
    assert tokyo["properties"]["visit count"] == 1


def test_generate_geojson_last_visit(db_with_data):
    """Test that last visit year is calculated correctly."""
    geojson = generate_geojson(db_with_data)

    features = geojson["features"]

    # Check last visit years
    paris = next(f for f in features if f["properties"]["name"] == "Paris")
    assert paris["properties"]["last visit"] == 2024  # trip2 ended in 2024

    london = next(f for f in features if f["properties"]["name"] == "London")
    assert london["properties"]["last visit"] == 2023  # trip1 ended in 2023

    tokyo = next(f for f in features if f["properties"]["name"] == "Tokyo")
    assert tokyo["properties"]["last visit"] == 2024  # trip3 ended in 2024


def test_export_geojson_creates_file(db_with_data):
    """Test that export_geojson creates a valid JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.geojson"

        export_geojson(db_with_data, output_path)

        # Check file was created
        assert output_path.exists()

        # Check file contains valid JSON
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Verify it's valid GeoJSON
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert len(data["features"]) == 3


def test_generate_geojson_empty_database():
    """Test that GeoJSON generation works with empty database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "empty.db"
        schema_path = Path(__file__).parent.parent / "schema.sql"

        db = Database(db_path)
        db.initialize_schema(schema_path)

        geojson = generate_geojson(db)

        assert geojson["type"] == "FeatureCollection"
        assert geojson["features"] == []

        db.close()


def test_geojson_with_yyyy_mm_dates():
    """Test GeoJSON generation with YYYY-MM format dates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        schema_path = Path(__file__).parent.parent / "schema.sql"

        db = Database(db_path)
        db.initialize_schema(schema_path)
        repo = Repository(db)

        # Create a city
        city = City(
            id=None,
            geonameid=12345,
            name="Test City",
            admin_division=None,
            country="US",
            latitude="40.7128",
            longitude="-74.0060"
        )
        city = repo.add_city(city)

        # Create a trip with YYYY-MM format dates
        trip = Trip(
            id=None,
            name="Test Trip",
            notes=None,
            start_date="2024-06",
            end_date="2024-06"
        )
        trip = repo.add_trip(trip)

        repo.add_trip_city(trip.id, city.id)

        geojson = generate_geojson(db)

        assert len(geojson["features"]) == 1
        feature = geojson["features"][0]
        assert feature["properties"]["last visit"] == 2024

        db.close()


def test_geojson_with_marker_colors():
    """Test GeoJSON generation with marker colors based on travelers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        schema_path = Path(__file__).parent.parent / "schema.sql"

        db = Database(db_path)
        db.initialize_schema(schema_path)
        repo = Repository(db)

        # Create people
        from travelbrag.models import Person
        alice = Person(id=None, name="Alice")
        alice = repo.add_person(alice)

        bob = Person(id=None, name="Bob")
        bob = repo.add_person(bob)

        charlie = Person(id=None, name="Charlie")
        charlie = repo.add_person(charlie)

        # Create cities
        city1 = City(
            id=None,
            geonameid=1,
            name="City A",
            admin_division=None,
            country="US",
            latitude="40.0",
            longitude="-74.0"
        )
        city1 = repo.add_city(city1)

        city2 = City(
            id=None,
            geonameid=2,
            name="City B",
            admin_division=None,
            country="US",
            latitude="41.0",
            longitude="-73.0"
        )
        city2 = repo.add_city(city2)

        city3 = City(
            id=None,
            geonameid=3,
            name="City C",
            admin_division=None,
            country="US",
            latitude="42.0",
            longitude="-72.0"
        )
        city3 = repo.add_city(city3)

        # Create trips
        # Trip 1: Alice only visits City A
        trip1 = Trip(
            id=None,
            name="Trip 1",
            notes=None,
            start_date="2024-01-01",
            end_date="2024-01-05"
        )
        trip1 = repo.add_trip(trip1)
        repo.add_trip_participant(trip1.id, alice.id)
        repo.add_trip_city(trip1.id, city1.id)

        # Trip 2: Alice and Bob visit City B
        trip2 = Trip(
            id=None,
            name="Trip 2",
            notes=None,
            start_date="2024-02-01",
            end_date="2024-02-05"
        )
        trip2 = repo.add_trip(trip2)
        repo.add_trip_participant(trip2.id, alice.id)
        repo.add_trip_participant(trip2.id, bob.id)
        repo.add_trip_city(trip2.id, city2.id)

        # Trip 3: All three visit City C
        trip3 = Trip(
            id=None,
            name="Trip 3",
            notes=None,
            start_date="2024-03-01",
            end_date="2024-03-05"
        )
        trip3 = repo.add_trip(trip3)
        repo.add_trip_participant(trip3.id, alice.id)
        repo.add_trip_participant(trip3.id, bob.id)
        repo.add_trip_participant(trip3.id, charlie.id)
        repo.add_trip_city(trip3.id, city3.id)

        # Define color mapping
        colours = {
            "FF0000": ["Alice"],  # Red for Alice only
            "00FF00": ["Alice", "Bob"],  # Green for Alice and Bob
            "0000FF": ["Alice", "Bob", "Charlie"],  # Blue for all three
        }

        geojson = generate_geojson(db, colours)

        assert len(geojson["features"]) == 3

        # Find features by name
        features_by_name = {f["properties"]["name"]: f for f in geojson["features"]}

        # City A should have red marker (Alice only)
        assert features_by_name["City A"]["properties"]["marker-color"] == "#FF0000"

        # City B should have green marker (Alice and Bob)
        assert features_by_name["City B"]["properties"]["marker-color"] == "#00FF00"

        # City C should have blue marker (All three)
        assert features_by_name["City C"]["properties"]["marker-color"] == "#0000FF"

        db.close()


def test_geojson_without_marker_colors():
    """Test GeoJSON generation without color mapping."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        schema_path = Path(__file__).parent.parent / "schema.sql"

        db = Database(db_path)
        db.initialize_schema(schema_path)
        repo = Repository(db)

        # Create a person and city
        from travelbrag.models import Person
        alice = Person(id=None, name="Alice")
        alice = repo.add_person(alice)

        city = City(
            id=None,
            geonameid=1,
            name="City A",
            admin_division=None,
            country="US",
            latitude="40.0",
            longitude="-74.0"
        )
        city = repo.add_city(city)

        # Create a trip
        trip = Trip(
            id=None,
            name="Trip",
            notes=None,
            start_date="2024-01-01",
            end_date="2024-01-05"
        )
        trip = repo.add_trip(trip)
        repo.add_trip_participant(trip.id, alice.id)
        repo.add_trip_city(trip.id, city.id)

        # Generate GeoJSON without colors
        geojson = generate_geojson(db)

        assert len(geojson["features"]) == 1
        feature = geojson["features"][0]

        # Should not have marker-color property
        assert "marker-color" not in feature["properties"]

        db.close()


def test_geojson_no_color_match():
    """Test GeoJSON generation when travelers don't match any color."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        schema_path = Path(__file__).parent.parent / "schema.sql"

        db = Database(db_path)
        db.initialize_schema(schema_path)
        repo = Repository(db)

        # Create people
        from travelbrag.models import Person
        alice = Person(id=None, name="Alice")
        alice = repo.add_person(alice)

        bob = Person(id=None, name="Bob")
        bob = repo.add_person(bob)

        # Create a city
        city = City(
            id=None,
            geonameid=1,
            name="City A",
            admin_division=None,
            country="US",
            latitude="40.0",
            longitude="-74.0"
        )
        city = repo.add_city(city)

        # Create a trip
        trip = Trip(
            id=None,
            name="Trip",
            notes=None,
            start_date="2024-01-01",
            end_date="2024-01-05"
        )
        trip = repo.add_trip(trip)
        repo.add_trip_participant(trip.id, alice.id)
        repo.add_trip_participant(trip.id, bob.id)
        repo.add_trip_city(trip.id, city.id)

        # Define color mapping that doesn't include Alice and Bob together
        colours = {
            "FF0000": ["Alice"],
            "00FF00": ["Bob"],
        }

        geojson = generate_geojson(db, colours)

        assert len(geojson["features"]) == 1
        feature = geojson["features"][0]

        # Should not have marker-color property when no match
        assert "marker-color" not in feature["properties"]

        db.close()

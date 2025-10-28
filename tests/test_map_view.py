"""Tests for map view component."""

import os
import pytest

from travelbrag.gui.map_view import CityMapView
from travelbrag.models import City


@pytest.fixture(autouse=True)
def set_toga_backend():
    """Set toga backend to dummy for all tests."""
    os.environ["TOGA_BACKEND"] = "toga_dummy"


@pytest.fixture
def sample_cities():
    """Create sample city data."""
    return [
        City(
            id=1,
            geonameid=5128581,
            name="New York",
            country="US",
            admin_division="New York",
            latitude="40.7128",
            longitude="-74.0060"
        ),
        City(
            id=2,
            geonameid=2643743,
            name="London",
            country="GB",
            admin_division="England",
            latitude="51.5074",
            longitude="-0.1278"
        ),
    ]


def test_map_view_creation():
    """Test that map view can be created."""
    map_view = CityMapView()
    assert map_view is not None
    assert hasattr(map_view, 'map_widget')


def test_update_cities_with_empty_map():
    """Test that updating cities on an empty map doesn't raise an error.

    This is a regression test for a bug where calling update_cities on a newly
    created map would fail because it tried to clear pins before the map's
    JavaScript was fully initialized.
    """
    map_view = CityMapView()

    # This should not raise an error even though the map has no pins
    map_view.update_cities([])


def test_update_cities_with_data(sample_cities):
    """Test updating map with city data."""
    map_view = CityMapView()

    # Update with cities
    map_view.update_cities(sample_cities)

    # Verify pins were added
    assert len(map_view.map_widget.pins) == 2


def test_update_cities_clears_previous_pins(sample_cities):
    """Test that updating cities clears previous pins."""
    map_view = CityMapView()

    # Add initial cities
    map_view.update_cities(sample_cities)
    assert len(map_view.map_widget.pins) == 2

    # Update with fewer cities
    map_view.update_cities([sample_cities[0]])
    assert len(map_view.map_widget.pins) == 1


def test_update_cities_empty_resets_view(sample_cities):
    """Test that updating with empty list resets the map view."""
    map_view = CityMapView()

    # Add cities first
    map_view.update_cities(sample_cities)
    assert len(map_view.map_widget.pins) == 2

    # Clear with empty list
    map_view.update_cities([])
    assert len(map_view.map_widget.pins) == 0

    # Verify map reset to world view
    assert map_view.map_widget.location == (20.0, 0.0)
    assert map_view.map_widget.zoom == 1


def test_map_widget_property():
    """Test that map widget property returns the widget."""
    map_view = CityMapView()
    widget = map_view.widget
    assert widget is map_view.map_widget

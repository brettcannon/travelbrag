"""Tests for the city search dialog."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
import toga
from travelbrag.gui.city_search import CitySearchDialog, validate_country_code
from travelbrag.models import City


@pytest.fixture
def mock_geonames_client():
    """Create a mock GeoNames client."""
    return Mock()


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = Mock()
    repo.get_visited_cities_by_country = Mock(return_value=[])
    return repo


@pytest.fixture
def sample_cities():
    """Create sample cities for testing."""
    return [
        City(
            id=1,
            geonameid=5391959,
            name="San Francisco",
            admin_division="California",
            country="United States",
            latitude=37.7749,
            longitude=-122.4194
        ),
        City(
            id=2,
            geonameid=5368361,
            name="Los Angeles",
            admin_division="California",
            country="United States",
            latitude=34.0522,
            longitude=-118.2437
        ),
        City(
            id=3,
            geonameid=5128581,
            name="New York",
            admin_division="New York",
            country="United States",
            latitude=40.7128,
            longitude=-74.0060
        ),
    ]


def test_validate_country_code():
    """Test country code validation."""
    # Valid codes
    assert validate_country_code("US") is None
    assert validate_country_code("us") is None  # Should accept lowercase
    assert validate_country_code("GB") is None
    assert validate_country_code("FR") is None
    assert validate_country_code("CA") is None
    assert validate_country_code("") is None  # Empty is allowed
    assert validate_country_code("  ") is None  # Whitespace-only is allowed

    # Invalid codes
    assert validate_country_code("USA") is not None  # Too long
    assert validate_country_code("U") is not None  # Too short
    assert validate_country_code("12") is not None  # Not alphabetic
    assert validate_country_code("ZZ") is not None  # Not a valid ISO code
    assert validate_country_code("U2") is not None  # Contains number


def test_city_search_dialog_init(mock_geonames_client, mock_repository):
    """Test CitySearchDialog initialization."""
    dialog = CitySearchDialog(mock_geonames_client, mock_repository)

    assert dialog.geonames_client == mock_geonames_client
    assert dialog.repository == mock_repository
    assert dialog.selected_city is None
    assert dialog.notes is None
    assert dialog.visited_cities == []
    assert dialog.filtered_cities == []


def test_on_country_changed_empty(mock_geonames_client, mock_repository):
    """Test handling empty country code."""
    dialog = CitySearchDialog(mock_geonames_client, mock_repository)
    mock_table = Mock()
    mock_status = Mock()

    dialog.on_country_changed("", "", mock_table, mock_status)

    assert dialog.visited_cities == []
    assert dialog.filtered_cities == []
    assert mock_table.data == []
    assert mock_status.text == ""
    mock_repository.get_visited_cities_by_country.assert_not_called()


def test_on_country_changed_invalid(mock_geonames_client, mock_repository):
    """Test handling invalid country code."""
    dialog = CitySearchDialog(mock_geonames_client, mock_repository)
    mock_table = Mock()
    mock_status = Mock()

    dialog.on_country_changed("ZZ", "", mock_table, mock_status)

    assert dialog.visited_cities == []
    assert dialog.filtered_cities == []
    assert mock_table.data == []
    assert mock_status.text == ""
    mock_repository.get_visited_cities_by_country.assert_not_called()


def test_on_country_changed_valid_with_cities(mock_geonames_client, mock_repository, sample_cities):
    """Test handling valid country code with visited cities."""
    mock_repository.get_visited_cities_by_country.return_value = sample_cities
    dialog = CitySearchDialog(mock_geonames_client, mock_repository)
    mock_table = Mock()
    mock_status = Mock()

    dialog.on_country_changed("US", "", mock_table, mock_status)

    assert dialog.visited_cities == sample_cities
    assert dialog.filtered_cities == sample_cities
    assert len(mock_table.data) == 3
    assert mock_table.data[0] == ("San Francisco", "California", "United States")
    assert mock_table.data[1] == ("Los Angeles", "California", "United States")
    assert mock_table.data[2] == ("New York", "New York", "United States")
    assert "3 previously visited cities" in mock_status.text
    mock_repository.get_visited_cities_by_country.assert_called_once_with("US")


def test_on_country_changed_with_filter(mock_geonames_client, mock_repository, sample_cities):
    """Test handling country change with existing city filter."""
    mock_repository.get_visited_cities_by_country.return_value = sample_cities
    dialog = CitySearchDialog(mock_geonames_client, mock_repository)
    mock_table = Mock()
    mock_status = Mock()

    dialog.on_country_changed("US", "San", mock_table, mock_status)

    assert dialog.visited_cities == sample_cities
    assert len(dialog.filtered_cities) == 1
    assert dialog.filtered_cities[0].name == "San Francisco"
    assert len(mock_table.data) == 1
    assert mock_table.data[0] == ("San Francisco", "California", "United States")
    assert "1 previously visited city" in mock_status.text


def test_filter_visited_cities(mock_geonames_client, mock_repository, sample_cities):
    """Test filtering visited cities by name."""
    dialog = CitySearchDialog(mock_geonames_client, mock_repository)
    dialog.visited_cities = sample_cities
    mock_table = Mock()
    mock_status = Mock()

    # Filter for "Los"
    dialog.filter_visited_cities("Los", mock_table, mock_status)
    assert len(dialog.filtered_cities) == 1
    assert dialog.filtered_cities[0].name == "Los Angeles"
    assert mock_table.data[0][0] == "Los Angeles"
    assert "1 previously visited city" in mock_status.text

    # Filter for "New"
    dialog.filter_visited_cities("New", mock_table, mock_status)
    assert len(dialog.filtered_cities) == 1
    assert dialog.filtered_cities[0].name == "New York"
    assert "1 previously visited city" in mock_status.text

    # Case insensitive filter
    dialog.filter_visited_cities("san", mock_table, mock_status)
    assert len(dialog.filtered_cities) == 1
    assert dialog.filtered_cities[0].name == "San Francisco"
    assert "1 previously visited city" in mock_status.text

    # Empty filter shows all
    dialog.filter_visited_cities("", mock_table, mock_status)
    assert len(dialog.filtered_cities) == 3
    assert "3 previously visited cities" in mock_status.text

    # No matches
    dialog.filter_visited_cities("Chicago", mock_table, mock_status)
    assert len(dialog.filtered_cities) == 0
    assert mock_table.data == []
    assert "No matching cities found" in mock_status.text


def test_on_city_typing_no_visited_cities(mock_geonames_client, mock_repository):
    """Test typing when no visited cities are loaded."""
    dialog = CitySearchDialog(mock_geonames_client, mock_repository)
    mock_table = Mock()
    mock_status = Mock()

    # Should do nothing if no visited cities
    dialog.on_city_typing("San", mock_table, mock_status)

    # Table should not be modified
    mock_table.data.assert_not_called()


def test_on_city_typing_with_visited_cities(mock_geonames_client, mock_repository, sample_cities):
    """Test typing when visited cities are loaded."""
    dialog = CitySearchDialog(mock_geonames_client, mock_repository)
    dialog.visited_cities = sample_cities
    mock_table = Mock()
    mock_status = Mock()

    dialog.on_city_typing("York", mock_table, mock_status)

    assert len(dialog.filtered_cities) == 1
    assert dialog.filtered_cities[0].name == "New York"
    assert mock_table.data[0][0] == "New York"
    assert "1 previously visited city" in mock_status.text


def test_select_city_from_filtered(mock_geonames_client, mock_repository, sample_cities):
    """Test selecting a city from filtered visited cities."""
    dialog = CitySearchDialog(mock_geonames_client, mock_repository)
    dialog.filtered_cities = [sample_cities[0]]  # San Francisco

    mock_table = Mock()
    mock_table.selection = ("San Francisco", "California", "United States")
    mock_table.data = [("San Francisco", "California", "United States")]

    mock_notes = Mock()
    mock_notes.value = "Great city for tech"

    mock_window = Mock()

    dialog.select_city(mock_table, mock_notes, mock_window)

    assert dialog.selected_city == sample_cities[0]
    assert dialog.notes == "Great city for tech"
    mock_window.close.assert_called_once()


def test_select_city_from_search_results(mock_geonames_client, mock_repository, sample_cities):
    """Test selecting a city from search results."""
    dialog = CitySearchDialog(mock_geonames_client, mock_repository)
    dialog.search_results = sample_cities
    dialog.filtered_cities = []  # No filtered cities

    mock_table = Mock()
    mock_table.selection = ("Los Angeles", "California", "United States")
    mock_table.data = [
        ("San Francisco", "California", "United States"),
        ("Los Angeles", "California", "United States"),
        ("New York", "New York", "United States")
    ]

    mock_notes = Mock()
    mock_notes.value = ""

    mock_window = Mock()

    dialog.select_city(mock_table, mock_notes, mock_window)

    assert dialog.selected_city == sample_cities[1]  # Los Angeles
    assert dialog.notes is None  # Empty notes
    mock_window.close.assert_called_once()
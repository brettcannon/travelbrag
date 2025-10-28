"""Tests for GeoNames API client."""

import pytest
from unittest.mock import AsyncMock, patch

from travelbrag.geonames import GeoNamesClient
from travelbrag.models import City


@pytest.fixture
def geonames_client():
    """Create a GeoNames client for testing."""
    return GeoNamesClient(username="test_user")


@pytest.mark.asyncio
async def test_search_cities(geonames_client):
    """Test searching for cities."""
    mock_response = {
        "geonames": [
            {
                "geonameId": 5391959,
                "name": "San Francisco",
                "adminName1": "California",
                "countryCode": "US",
                "countryCode": "US",
                "countryName": "United States",
                "lat": "37.7749",
                "lng": "-122.4194"
            },
            {
                "geonameId": 5391960,
                "name": "San Francisco Bay",
                "adminName1": "California",
                "countryCode": "US",
                "countryCode": "US",
                "countryName": "United States",
                "lat": "37.8",
                "lng": "-122.5"
            }
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        mock_get.return_value.raise_for_status = lambda: None

        cities = await geonames_client.search_cities(
            query="San Francisco",
            country="US",
            max_results=10
        )

        assert len(cities) == 2
        assert cities[0].name == "San Francisco"
        assert cities[0].geonameid == 5391959
        assert cities[0].admin_division == "California"
        assert cities[0].country == "US"


@pytest.mark.asyncio
async def test_search_cities_with_admin_division(geonames_client):
    """Test searching for cities with admin division filter."""
    mock_response = {
        "geonames": [
            {
                "geonameId": 12345,
                "name": "Springfield",
                "adminName1": "Illinois",
                "countryCode": "US",
                "countryName": "United States",
                "lat": "39.7817",
                "lng": "-89.6501"
            }
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        mock_get.return_value.raise_for_status = lambda: None

        cities = await geonames_client.search_cities(
            query="Springfield",
            country="US",
            admin_division="IL",
            max_results=10
        )

        assert len(cities) == 1
        assert cities[0].name == "Springfield"
        assert cities[0].admin_division == "Illinois"


@pytest.mark.asyncio
async def test_get_city_by_geonameid(geonames_client):
    """Test getting city by GeoNames ID."""
    mock_response = {
        "geonameId": 5391959,
        "name": "San Francisco",
        "adminName1": "California",
        "countryName": "United States",
        "lat": "37.7749",
        "lng": "-122.4194"
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        mock_get.return_value.raise_for_status = lambda: None

        city = await geonames_client.get_city_by_geonameid(5391959)

        assert city is not None
        assert city.name == "San Francisco"
        assert city.geonameid == 5391959
        assert city.latitude == "37.7749"
        assert city.longitude == "-122.4194"


@pytest.mark.asyncio
async def test_search_cities_with_spaces(geonames_client):
    """Test searching for cities with spaces in the name."""
    mock_response = {
        "geonames": [
            {
                "geonameId": 4164138,
                "name": "Miami Beach",
                "adminName1": "Florida",
                "countryCode": "US",
                "countryName": "United States",
                "lat": "25.7906",
                "lng": "-80.1303"
            },
            {
                "geonameId": 5128581,
                "name": "New York",
                "adminName1": "New York",
                "countryCode": "US",
                "countryName": "United States",
                "lat": "40.7128",
                "lng": "-74.0060"
            }
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        mock_get.return_value.raise_for_status = lambda: None

        # Test with "Miami Beach" - city with space
        cities = await geonames_client.search_cities(
            query="Miami Beach",
            country="US",
            max_results=10
        )

        # Verify the call was made with the correct params
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert params["q"] == "Miami Beach"  # Should contain the space

        assert len(cities) == 2
        assert cities[0].name == "Miami Beach"
        assert cities[1].name == "New York"


@pytest.mark.asyncio
async def test_search_cities_empty_result(geonames_client):
    """Test searching with no results."""
    mock_response = {"geonames": []}

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        mock_get.return_value.raise_for_status = lambda: None

        cities = await geonames_client.search_cities(
            query="NonexistentCity123",
            max_results=10
        )

        assert len(cities) == 0

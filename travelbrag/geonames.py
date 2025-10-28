"""GeoNames API client for fetching city data."""

import httpx
from typing import Optional
from .models import City


class GeoNamesClient:
    """Client for interacting with GeoNames web services."""

    BASE_URL = "http://api.geonames.org"

    def __init__(self, username: str):
        """Initialize GeoNames client.

        Args:
            username: GeoNames username for API access
        """
        self.username = username

    async def search_cities(
        self,
        query: str,
        country: Optional[str] = None,
        admin_division: Optional[str] = None,
        max_results: int = 10
    ) -> list[City]:
        """Search for cities using GeoNames API.

        Args:
            query: Search query (city name)
            country: ISO 2-letter country code to filter by
            admin_division: Admin division (state/province) to filter by
            max_results: Maximum number of results to return

        Returns:
            List of City objects matching the search
        """
        params = {
            "q": query,
            "maxRows": max_results,
            "username": self.username,
            "type": "json",
            "featureClass": "P",  # Populated places only
            "orderby": "relevance"
        }

        if country:
            params["country"] = country

        if admin_division:
            params["adminCode1"] = admin_division

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/searchJSON",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

        cities = []
        for item in data.get("geonames", []):
            city = City(
                id=None,  # Will be assigned by database
                geonameid=item["geonameId"],
                name=item["name"],
                admin_division=item.get("adminName1"),
                country=item.get("countryCode", ""),
                latitude=str(item["lat"]),
                longitude=str(item["lng"])
            )
            cities.append(city)

        return cities

    async def get_city_by_geonameid(self, geonameid: int) -> Optional[City]:
        """Get city details by GeoNames ID.

        Args:
            geonameid: GeoNames ID

        Returns:
            City object or None if not found
        """
        params = {
            "geonameId": geonameid,
            "username": self.username,
            "type": "json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/getJSON",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            item = response.json()

        if not item:
            return None

        return City(
            id=None,
            geonameid=item["geonameId"],
            name=item["name"],
            admin_division=item.get("adminName1"),
            country=item.get("countryCode", ""),
            latitude=str(item["lat"]),
            longitude=str(item["lng"])
        )

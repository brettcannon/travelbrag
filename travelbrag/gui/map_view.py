"""Map view component using Toga MapView widget."""

from typing import List

import toga
from toga.style import Pack

from ..models import City


class CityMapView:
    """Component for displaying cities on a map."""

    def __init__(self):
        """Initialize map view."""
        # Create map centered at world view initially
        self.map_widget = toga.MapView(style=Pack(flex=1, margin=5))

    def update_cities(self, cities: List[City]) -> None:
        """Update map with list of cities.

        Args:
            cities: List of City objects to display
        """
        # Clear existing pins (only if there are any)
        # This avoids errors when the map's JavaScript isn't fully initialized
        if len(self.map_widget.pins) > 0:
            self.map_widget.pins.clear()

        if not cities:
            # Reset to world view
            self.map_widget.location = (20.0, 0.0)
            self.map_widget.zoom = 1
            return

        # Add pins for each city
        for city in cities:
            lat, lon = city.coordinates
            pin = toga.MapPin(
                location=(lat, lon),
                title=city.name,
                subtitle=f"{city.admin_division}, {city.country_name}"
                if city.admin_division
                else city.country_name,
            )
            self.map_widget.pins.add(pin)

        # Calculate bounding box for all cities
        if cities:
            lats = [city.coordinates[0] for city in cities]
            lons = [city.coordinates[1] for city in cities]

            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)

            # Center on the midpoint
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            self.map_widget.location = (center_lat, center_lon)

            # Calculate zoom based on the span
            lat_span = max_lat - min_lat
            lon_span = max_lon - min_lon
            max_span = max(lat_span, lon_span)

            # Estimate zoom level (rough approximation)
            # Zoom levels: 1 = world, ~6 = country, ~10 = city, ~15 = streets
            if max_span < 0.01:  # Very small area (single city)
                self.map_widget.zoom = 12
            elif max_span < 0.1:  # Small region
                self.map_widget.zoom = 9
            elif max_span < 1:  # Regional
                self.map_widget.zoom = 7
            elif max_span < 10:  # Multiple countries
                self.map_widget.zoom = 5
            elif max_span < 50:  # Continental
                self.map_widget.zoom = 3
            else:  # Very large area
                self.map_widget.zoom = 1

    @property
    def widget(self) -> toga.MapView:
        """Get the map widget."""
        return self.map_widget

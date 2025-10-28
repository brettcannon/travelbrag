"""Statistics view for displaying travel statistics."""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Callable

from ..repository import Repository
from ..config import Config
from .. import statistics


class StatisticsView:
    """View for displaying travel statistics."""

    def __init__(self, app: toga.App, repo: Repository, config: Config, on_trip_selected: Callable[[int], None]):
        """Initialize statistics view.

        Args:
            app: Toga application instance
            repo: Repository instance
            config: Config instance
            on_trip_selected: Callback when a trip is selected (receives trip_id)
        """
        self.app = app
        self.repo = repo
        self.config = config
        self.on_trip_selected = on_trip_selected

        # Create main container with scroll support
        self.container = toga.ScrollContainer(style=Pack(flex=1))

        # Create content box
        self.content_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        self.container.content = self.content_box

        # Track most visited cities for selection
        self.most_visited_cities = []

    def refresh(self) -> None:
        """Refresh the statistics display."""
        # Clear existing content
        self.content_box.clear()

        # Title
        title = toga.Label(
            "STATISTICS",
            style=Pack(margin=(5, 5, 15, 5), font_size=18, font_weight="bold")
        )
        self.content_box.add(title)

        # Recent Trips Section
        self._add_section_header("Recent Trips")
        self._add_recent_trips()

        # City Statistics Section
        self._add_section_header("City Statistics")
        self._add_city_statistics()

        # Traveler Statistics Section
        self._add_section_header("Traveler Statistics")
        self._add_longest_trips()
        self._add_traveler_statistics()

        # Canadian Provinces Section
        if self.config.home and self.config.home.upper() == "CA":
            self._add_section_header("Canadian Provinces & Territories")
            self._add_canadian_provinces()

    def _add_section_header(self, text: str) -> None:
        """Add a section header.

        Args:
            text: Header text
        """
        separator = toga.Divider(style=Pack(margin=(10, 5, 5, 5)))
        header = toga.Label(
            text,
            style=Pack(margin=(5, 5, 10, 5), font_size=14, font_weight="bold")
        )
        self.content_box.add(separator)
        self.content_box.add(header)

    def _add_recent_trips(self) -> None:
        """Add recent trips information."""
        # Last domestic trip
        last_domestic = statistics.get_last_domestic_trip(self.repo, self.config)
        if last_domestic:
            label_box = toga.Box(style=Pack(direction=ROW, margin=(2, 5)))
            label = toga.Label(
                "Last Domestic Trip: ",
                style=Pack(font_weight="bold")
            )
            trip_name = toga.Label(
                last_domestic.trip.name,
                style=Pack()
            )
            label_box.add(label)
            label_box.add(trip_name)
            detail = toga.Label(
                f"  Ended: {last_domestic.trip.end_date} ({last_domestic.days_ago} days ago)",
                style=Pack(margin=(2, 5, 10, 15))
            )
            self.content_box.add(label_box)
            self.content_box.add(detail)
        else:
            label = toga.Label(
                "Last Domestic Trip: None found",
                style=Pack(margin=(2, 5, 10, 5), font_weight="bold")
            )
            self.content_box.add(label)

        # Last international trip
        last_international = statistics.get_last_international_trip(self.repo, self.config)
        if last_international:
            label_box = toga.Box(style=Pack(direction=ROW, margin=(2, 5)))
            label = toga.Label(
                "Last International Trip: ",
                style=Pack(font_weight="bold")
            )
            trip_name = toga.Label(
                last_international.trip.name,
                style=Pack()
            )
            label_box.add(label)
            label_box.add(trip_name)
            detail = toga.Label(
                f"  Ended: {last_international.trip.end_date} ({last_international.days_ago} days ago)",
                style=Pack(margin=(2, 5, 10, 15))
            )
            self.content_box.add(label_box)
            self.content_box.add(detail)
        else:
            label = toga.Label(
                "Last International Trip: None found",
                style=Pack(margin=(2, 5, 10, 5), font_weight="bold")
            )
            self.content_box.add(label)

    def _add_city_statistics(self) -> None:
        """Add city statistics."""
        # Most visited cities
        most_visited = statistics.get_most_visited_cities(self.repo, self.config, limit=20)

        # Store for selection tracking
        self.most_visited_cities = most_visited

        if most_visited:
            label = toga.Label(
                "Most Visited Cities:",
                style=Pack(margin=(2, 5, 5, 5), font_weight="bold")
            )
            self.content_box.add(label)

            # Create table
            city_table = toga.Table(
                headings=["City", "Visits"],
                data=[
                    (cv.city.display_name, cv.count)
                    for cv in most_visited
                ],
                on_activate=self.on_city_activate,
                style=Pack(height=200, margin=(0, 5, 10, 15))
            )
            self.content_box.add(city_table)
        else:
            label = toga.Label(
                "Most Visited Cities: None",
                style=Pack(margin=(2, 5, 10, 5))
            )
            self.content_box.add(label)

    def _add_longest_trips(self) -> None:
        """Add longest trips per person."""
        # Longest trips per person
        longest_trips = statistics.get_longest_trips_per_person(self.repo, self.config)
        if longest_trips:
            label = toga.Label(
                "Longest Trips:",
                style=Pack(margin=(2, 5, 5, 5), font_weight="bold")
            )
            self.content_box.add(label)

            for person_trips in longest_trips:
                # Person header
                person_label = toga.Label(
                    f"{person_trips.person.name}:",
                    style=Pack(margin=(5, 5, 2, 5))
                )
                self.content_box.add(person_label)

                # Domestic trip
                if person_trips.longest_domestic:
                    domestic_label = toga.Label(
                        f"Domestic: {person_trips.longest_domestic.trip.name} "
                        f"({person_trips.longest_domestic.duration_days} days)",
                        style=Pack(margin=(2, 5, 2, 25))
                    )
                    self.content_box.add(domestic_label)
                else:
                    domestic_label = toga.Label(
                        "Domestic: None",
                        style=Pack(margin=(2, 5, 2, 25))
                    )
                    self.content_box.add(domestic_label)

                # International trip
                if person_trips.longest_international:
                    intl_label = toga.Label(
                        f"International: {person_trips.longest_international.trip.name} "
                        f"({person_trips.longest_international.duration_days} days)",
                        style=Pack(margin=(2, 5, 5, 25))
                    )
                    self.content_box.add(intl_label)
                else:
                    intl_label = toga.Label(
                        "International: None",
                        style=Pack(margin=(2, 5, 5, 25))
                    )
                    self.content_box.add(intl_label)

            # Add bottom margin
            spacer = toga.Box(style=Pack(height=10))
            self.content_box.add(spacer)
        else:
            label = toga.Label(
                "Longest Trips: No data",
                style=Pack(margin=(2, 5, 10, 5))
            )
            self.content_box.add(label)

    def _add_traveler_statistics(self) -> None:
        """Add traveler statistics."""
        # Longest time away from home
        longest_away = statistics.get_longest_time_away_per_person(self.repo, self.config)

        if longest_away:
            label = toga.Label(
                "Longest Time Away from Home (in a single year):",
                style=Pack(margin=(2, 5, 5, 5), font_weight="bold")
            )
            self.content_box.add(label)

            for person_year in longest_away:
                detail = toga.Label(
                    f"  {person_year.person.name}: {person_year.days_away} days ({person_year.year})",
                    style=Pack(margin=(2, 5))
                )
                self.content_box.add(detail)

            # Add bottom margin
            spacer = toga.Box(style=Pack(height=10))
            self.content_box.add(spacer)
        else:
            label = toga.Label(
                "Longest Time Away from Home: No data",
                style=Pack(margin=(2, 5, 10, 5))
            )
            self.content_box.add(label)

        # Countries visited in last 5 years
        countries_by_person = statistics.get_countries_last_5_years_per_person(self.repo, self.config)

        if countries_by_person:
            label = toga.Label(
                "Countries Visited (last 5 years):",
                style=Pack(margin=(2, 5, 5, 5), font_weight="bold")
            )
            self.content_box.add(label)

            for person_name, countries in sorted(countries_by_person.items()):
                if countries:
                    countries_str = ", ".join(countries)
                    detail = toga.Label(
                        f"  {person_name}: {countries_str}",
                        style=Pack(margin=(2, 5))
                    )
                    self.content_box.add(detail)
                else:
                    detail = toga.Label(
                        f"  {person_name}: None",
                        style=Pack(margin=(2, 5))
                    )
                    self.content_box.add(detail)

            # Add bottom margin
            spacer = toga.Box(style=Pack(height=10))
            self.content_box.add(spacer)
        else:
            label = toga.Label(
                "Countries Visited (last 5 years): No data",
                style=Pack(margin=(2, 5, 10, 5))
            )
            self.content_box.add(label)

    def _add_canadian_provinces(self) -> None:
        """Add Canadian provinces and territories statistics."""
        provinces = statistics.get_canadian_province_visits(self.repo, self.config)

        if provinces:
            # Create list of provinces with emoji markers
            for pv in provinces:
                province_label = toga.Label(
                    pv.province,
                    style=Pack(margin=(2, 5))
                )
                self.content_box.add(province_label)
        else:
            label = toga.Label(
                "No Canadian province data available",
                style=Pack(margin=(2, 5, 10, 5))
            )
            self.content_box.add(label)

    async def on_city_activate(self, widget, row=None, **kwargs) -> None:
        """Handle city double-click to view trips for that city.

        Args:
            widget: Table widget
            row: Activated row
            **kwargs: Additional arguments
        """
        if widget.selection:
            # Get the selected city by row index
            row_index = widget.data.index(widget.selection)
            city_visit_count = self.most_visited_cities[row_index]
            city = city_visit_count.city

            # Show dialog with trips for this city
            from .city_trips_dialog import CityTripsDialog

            dialog = CityTripsDialog(self.repo, city, self.on_trip_selected)
            await dialog.show(self.app)

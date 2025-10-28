"""Individual person detail view showing their trips and cities with map."""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Callable

from ..repository import Repository
from .map_view import CityMapView


class PersonDetail:
    """View showing a person's trips and all cities they've visited."""

    def __init__(
        self,
        app: toga.App,
        repo: Repository,
        person_id: int,
        on_back: Callable
    ):
        """Initialize person detail view.

        Args:
            app: Toga application instance
            repo: Repository instance
            person_id: ID of person to display
            on_back: Callback to return to previous view
        """
        self.app = app
        self.repo = repo
        self.person_id = person_id
        self.on_back = on_back

        # Get person data
        self.person = self.repo.get_person_by_id(person_id)
        if not self.person:
            raise ValueError(f"Person with ID {person_id} not found")

        # Create main container
        self.container = toga.Box(style=Pack(direction=COLUMN, flex=1, margin=10))

        # Header with back button and title
        header_box = toga.Box(style=Pack(direction=ROW, margin=5))
        back_btn = toga.Button("← Back", on_press=lambda w: on_back(None), style=Pack(margin=5))
        title = toga.Label(
            f"Trips by {self.person.name}",
            style=Pack(margin=5, font_size=16, font_weight="bold", flex=1)
        )
        header_box.add(back_btn)
        header_box.add(title)

        # Split container for trips and map
        split_box = toga.Box(style=Pack(direction=ROW, flex=1))

        # Left side: Trips list
        left_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self.trips_label = toga.Label("Trips", style=Pack(margin=5, font_weight="bold"))
        self.trips_table = toga.Table(
            headings=["Trip Name", "Start Date", "End Date"],
            data=[],
            style=Pack(flex=1, margin=5)
        )
        left_box.add(self.trips_label)
        left_box.add(self.trips_table)

        # Right side: Map and cities
        right_box = toga.Box(style=Pack(direction=COLUMN, flex=1))

        self.cities_label = toga.Label("Cities Visited", style=Pack(margin=5, font_weight="bold"))
        self.map_view = CityMapView()

        # City list
        self.cities_table = toga.Table(
            headings=["City", "State/Province", "Country"],
            data=[],
            style=Pack(flex=1, margin=5)
        )

        right_box.add(self.cities_label)
        right_box.add(self.map_view.widget)
        right_box.add(self.cities_table)

        split_box.add(left_box)
        split_box.add(right_box)

        self.container.add(header_box)
        self.container.add(split_box)

        # Load data
        self.refresh()

    def refresh(self) -> None:
        """Refresh person's trips and cities."""
        # Load trips
        trips = self.repo.get_person_trips(self.person_id)

        # Update label with trip count and oldest date
        trip_count = len(trips)
        if trip_count > 0:
            oldest_date = min(t.start_date for t in trips)
            self.trips_label.text = f"{trip_count:,} {'trip' if trip_count == 1 else 'trips'} since {oldest_date}"
        else:
            self.trips_label.text = "0 trips"

        self.trips_table.data = [
            (t.name, t.start_date, t.end_date)
            for t in trips
        ]

        # Load cities
        cities = self.repo.get_person_cities(self.person_id)

        # Update label with city count
        city_count = len(cities)
        self.cities_label.text = f"{city_count:,} {'city' if city_count == 1 else 'cities'} visited"

        self.cities_table.data = [
            (c.name, c.admin_division or "", c.country_name)
            for c in cities
        ]

        # Update map
        self.map_view.update_cities(cities)

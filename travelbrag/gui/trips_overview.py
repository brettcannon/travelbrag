"""Overall trips view showing all trips with map of all visited cities."""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Callable, Optional

from ..repository import Repository
from ..models import Trip
from ..config import Config
from .map_view import CityMapView


class TripsOverview:
    """View showing all trips with map of all visited cities."""

    def __init__(self, app: toga.App, repo: Repository, config: Config, on_trip_selected: Callable[[int], None]):
        """Initialize trips overview.

        Args:
            app: Toga application instance
            repo: Repository instance
            config: Configuration instance
            on_trip_selected: Callback when trip is selected
        """
        self.app = app
        self.repo = repo
        self.config = config
        self.on_trip_selected = on_trip_selected

        # Create main container with split view
        self.container = toga.Box(style=Pack(direction=COLUMN, flex=1, margin=10))

        # Title
        self.title = toga.Label("All Trips", style=Pack(margin=5, font_size=16, font_weight="bold"))

        # Button row
        button_box = toga.Box(style=Pack(direction=ROW, margin=5))
        add_btn = toga.Button("Add Trip", on_press=self.add_trip, style=Pack(margin=5))
        view_btn = toga.Button("View Trip", on_press=self.view_trip, style=Pack(margin=5))
        delete_btn = toga.Button("Delete Trip", on_press=self.delete_trip, style=Pack(margin=5))

        button_box.add(add_btn)
        button_box.add(view_btn)
        button_box.add(delete_btn)

        # Split container for table and map
        split_box = toga.Box(style=Pack(direction=ROW, flex=1))

        # Left side: Trips table
        left_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self.trips_table = toga.Table(
            headings=["Trip Name", "Start Date", "End Date"],
            data=[],
            on_select=self.on_table_select,
            on_activate=self.on_trip_activate,
            style=Pack(flex=1, margin=5)
        )
        left_box.add(self.trips_table)

        # Right side: Map and city list
        right_box = toga.Box(style=Pack(direction=COLUMN, flex=1))

        self.map_title = toga.Label("All Visited Cities", style=Pack(margin=5, font_weight="bold"))
        self.map_view = CityMapView()

        # City list
        self.cities_table = toga.Table(
            headings=["City", "State/Province", "Country"],
            data=[],
            on_activate=self.on_city_activate,
            style=Pack(flex=1, margin=5)
        )

        right_box.add(self.map_title)
        right_box.add(self.map_view.widget)
        right_box.add(self.cities_table)

        split_box.add(left_box)
        split_box.add(right_box)

        self.container.add(self.title)
        self.container.add(button_box)
        self.container.add(split_box)

        self.selected_trip: Optional[Trip] = None
        self.trips_list = []
        self.cities_list = []

    def refresh(self) -> None:
        """Refresh trips list and map."""
        # Load trips and sort by start date (reverse chronological)
        trips = self.repo.get_all_trips()
        trips.sort(key=lambda t: t.start_date, reverse=True)

        # Store trips list for selection tracking
        self.trips_list = trips

        # Update title with trip count and oldest date
        trip_count = len(trips)
        if trip_count > 0:
            oldest_date = min(t.start_date for t in trips)
            self.title.text = f"{trip_count:,} {'trip' if trip_count == 1 else 'trips'} since {oldest_date}"
        else:
            self.title.text = "0 trips"

        self.trips_table.data = [
            (t.name, t.start_date, t.end_date)
            for t in trips
        ]

        # Load all visited cities
        cities = self.repo.get_all_visited_cities()

        # Store cities list for selection tracking
        self.cities_list = cities

        # Update title with city count
        city_count = len(cities)
        self.map_title.text = f"{city_count:,} {'city' if city_count == 1 else 'cities'} visited"

        self.cities_table.data = [
            (c.name, c.admin_division or "", c.country_name)
            for c in cities
        ]

        # Update map
        self.map_view.update_cities(cities)

    def on_table_select(self, widget) -> None:
        """Handle table row selection.

        Args:
            widget: Table widget
        """
        if widget.selection:
            # Get the selected trip by row index
            # The selection represents the row that was selected
            row_index = self.trips_table.data.index(widget.selection)
            self.selected_trip = self.trips_list[row_index]

    def on_trip_activate(self, widget, row=None, **kwargs) -> None:
        """Handle trip double-click to view trip details.

        Args:
            widget: Table widget
            row: Activated row
            **kwargs: Additional arguments
        """
        if self.selected_trip:
            self.on_trip_selected(self.selected_trip.id)

    async def on_city_activate(self, widget, row=None, **kwargs) -> None:
        """Handle city double-click to view trips for that city.

        Args:
            widget: Table widget
            row: Activated row
            **kwargs: Additional arguments
        """
        if widget.selection:
            # Get the selected city by row index
            row_index = self.cities_table.data.index(widget.selection)
            city = self.cities_list[row_index]

            # Show dialog with trips for this city
            from .city_trips_dialog import CityTripsDialog

            dialog = CityTripsDialog(self.repo, city, self.on_trip_selected)
            await dialog.show(self.app)

    async def add_trip(self, widget) -> None:
        """Show dialog to add a new trip."""
        from .trip_create_dialog import TripCreateDialog

        dialog = TripCreateDialog(self.repo, self.config)
        trip = await dialog.show(self.app)

        if trip:
            self.refresh()
            # Immediately view the newly created trip
            self.on_trip_selected(trip.id)

    def view_trip(self, widget) -> None:
        """View selected trip details."""
        if self.selected_trip:
            self.on_trip_selected(self.selected_trip.id)

    async def delete_trip(self, widget) -> None:
        """Delete selected trip with confirmation."""
        if not self.selected_trip:
            await self.app.main_window.info_dialog(
                "No Selection",
                "Please select a trip to delete."
            )
            return

        confirm_dialog = toga.ConfirmDialog(
            "Confirm Delete",
            f"Are you sure you want to delete the trip '{self.selected_trip.name}'? "
            f"This will remove all associated data."
        )
        confirmed = await self.app.main_window.dialog(confirm_dialog)

        if confirmed:
            self.repo.delete_trip(self.selected_trip.id)
            self.selected_trip = None
            self.refresh()

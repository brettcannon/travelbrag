"""Dialog to display all trips that include a specific city."""

import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Optional, Callable

from ..models import City, Trip
from ..repository import Repository


class CityTripsDialog:
    """A dialog that shows all trips for a specific city."""

    def __init__(self, repo: Repository, city: City, on_trip_selected: Optional[Callable[[int], None]] = None):
        """Initialize the city trips dialog.

        Args:
            repo: Repository instance
            city: City to show trips for
            on_trip_selected: Optional callback when a trip is double-clicked (receives trip_id)
        """
        self.repo = repo
        self.city = city
        self.on_trip_selected = on_trip_selected
        self.trips: list[Trip] = []
        self.dialog: Optional[toga.Window] = None

    async def show(self, app: toga.App) -> None:
        """Show the city trips dialog.

        Args:
            app: Toga application instance
        """
        # Get all trips for this city
        self.trips = self.repo.get_city_trips(self.city.id)

        # Create dialog window
        self.dialog = toga.Window(
            title=f"Trips to {self.city.display_name}",
            size=(600, 400)
        )

        # Create the UI
        main_box = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Info label
        trip_count = len(self.trips)
        label = toga.Label(
            f"Found {trip_count} trip{'s' if trip_count != 1 else ''} to {self.city.display_name}",
            style=Pack(margin=(0, 0, 10, 0))
        )

        # Trips table
        trips_table = toga.Table(
            headings=["Trip Name", "Start Date", "End Date"],
            data=[
                (trip.name, trip.start_date, trip.end_date)
                for trip in self.trips
            ],
            on_activate=self._on_trip_activate if self.on_trip_selected else None,
            style=Pack(flex=1, margin=5)
        )

        # Close button
        button_box = toga.Box(style=Pack(direction=ROW, margin=(10, 0, 0, 0)))
        close_button = toga.Button(
            "Close",
            on_press=lambda w: self.dialog.close(),
            style=Pack(margin=5, flex=1)
        )
        button_box.add(close_button)

        main_box.add(label)
        main_box.add(trips_table)
        main_box.add(button_box)

        self.dialog.content = main_box
        self.dialog.show()

        # Wait for dialog to close
        while not self.dialog.closed:
            await asyncio.sleep(0.1)

    def _on_trip_activate(self, widget, row=None, **kwargs) -> None:
        """Handle trip double-click.

        Args:
            widget: Table widget
            row: Activated row
            **kwargs: Additional arguments
        """
        if widget.selection:
            row_index = widget.data.index(widget.selection)
            trip = self.trips[row_index]
            # Close the dialog
            self.dialog.close()
            # Call the callback
            if self.on_trip_selected:
                self.on_trip_selected(trip.id)

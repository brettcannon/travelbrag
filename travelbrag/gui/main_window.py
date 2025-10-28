"""Main window for Travelbrag application."""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Optional

from ..config import Config
from ..database import Database
from ..repository import Repository


class MainWindow:
    """Main application window with navigation."""

    def __init__(self, app: toga.App, config: Config, db: Database, repo: Repository):
        """Initialize main window.

        Args:
            app: Toga application instance
            config: Configuration manager
            db: Database instance
            repo: Repository instance
        """
        self.app = app
        self.config = config
        self.db = db
        self.repo = repo

        # Import view classes here to avoid circular imports
        from .trips_overview import TripsOverview
        from .people_view import PeopleView
        from .statistics_view import StatisticsView

        # Create main container
        self.main_box = toga.Box(style=Pack(direction=COLUMN, flex=1))

        # Create navigation buttons
        nav_box = toga.Box(style=Pack(direction=ROW, margin=5))

        self.trips_btn = toga.Button(
            "All Trips",
            on_press=self.show_trips_view,
            style=Pack(margin=5, flex=1)
        )
        self.people_btn = toga.Button(
            "People",
            on_press=self.show_people_view,
            style=Pack(margin=5, flex=1)
        )
        self.statistics_btn = toga.Button(
            "Statistics",
            on_press=self.show_statistics_view,
            style=Pack(margin=5, flex=1)
        )

        nav_box.add(self.trips_btn)
        nav_box.add(self.people_btn)
        nav_box.add(self.statistics_btn)

        # Content area
        self.content_box = toga.Box(style=Pack(direction=COLUMN, flex=1))

        self.main_box.add(nav_box)
        self.main_box.add(self.content_box)

        # Initialize views
        self.trips_overview = TripsOverview(self.app, self.repo, self.config, self.on_trip_selected)
        self.people_view = PeopleView(self.app, self.repo, self.on_person_selected)
        self.statistics_view = StatisticsView(self.app, self.repo, self.config, self.on_trip_selected)

        # Show trips view by default
        self.show_trips_view(None)

    def show_trips_view(self, widget) -> None:
        """Show the trips overview."""
        self.content_box.clear()
        self.content_box.add(self.trips_overview.container)
        self.trips_overview.refresh()

    def show_people_view(self, widget) -> None:
        """Show the people management view."""
        self.content_box.clear()
        self.content_box.add(self.people_view.container)
        self.people_view.refresh()

    def show_statistics_view(self, widget) -> None:
        """Show the statistics view."""
        self.content_box.clear()
        self.content_box.add(self.statistics_view.container)
        self.statistics_view.refresh()

    def on_trip_selected(self, trip_id: int) -> None:
        """Handle trip selection to show trip details.

        Args:
            trip_id: Selected trip ID
        """
        from .trip_detail import TripDetail

        trip_detail = TripDetail(self.app, self.repo, self.config, trip_id, self.show_trips_view)
        self.content_box.clear()
        self.content_box.add(trip_detail.container)

    def on_person_selected(self, person_id: int) -> None:
        """Handle person selection to show person's trips.

        Args:
            person_id: Selected person ID
        """
        from .person_detail import PersonDetail

        person_detail = PersonDetail(self.app, self.repo, person_id, self.show_people_view)
        self.content_box.clear()
        self.content_box.add(person_detail.container)

    @property
    def container(self) -> toga.Box:
        """Get the main container widget."""
        return self.main_box

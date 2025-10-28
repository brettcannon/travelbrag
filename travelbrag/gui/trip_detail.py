"""Individual trip detail view with participants, cities, and map."""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Callable

from ..repository import Repository
from ..config import Config
from ..geonames import GeoNamesClient
from ..date_parser import calculate_duration
from .map_view import CityMapView
from .city_search import CitySearchDialog


class TripDetail:
    """View showing trip details including participants and cities visited."""

    def __init__(
        self,
        app: toga.App,
        repo: Repository,
        config: Config,
        trip_id: int,
        on_back: Callable
    ):
        """Initialize trip detail view.

        Args:
            app: Toga application instance
            repo: Repository instance
            config: Configuration manager
            trip_id: ID of trip to display
            on_back: Callback to return to previous view
        """
        self.app = app
        self.repo = repo
        self.config = config
        self.trip_id = trip_id
        self.on_back = on_back

        # Get trip data
        self.trip = self.repo.get_trip_by_id(trip_id)
        if not self.trip:
            raise ValueError(f"Trip with ID {trip_id} not found")

        # Create main container
        self.container = toga.Box(style=Pack(direction=COLUMN, flex=1, margin=10))

        # Header with back button and title
        header_box = toga.Box(style=Pack(direction=ROW, margin=5))
        back_btn = toga.Button("← Back", on_press=lambda w: on_back(None), style=Pack(margin=5))
        title = toga.Label(
            self.trip.name,
            style=Pack(margin=5, font_size=16, font_weight="bold", flex=1)
        )
        edit_trip_btn = toga.Button("Edit Trip", on_press=self.edit_trip, style=Pack(margin=5))
        header_box.add(back_btn)
        header_box.add(title)
        header_box.add(edit_trip_btn)

        # Trip info
        info_box = toga.Box(style=Pack(direction=ROW, margin=5))
        duration = calculate_duration(self.trip.start_date, self.trip.end_date)
        dates_label = toga.Label(
            f"{self.trip.start_date} to {self.trip.end_date} ({duration} day{'s' if duration != 1 else ''})",
            style=Pack(margin=5)
        )
        info_box.add(dates_label)
        if self.trip.notes:
            notes_label = toga.Label(
                f"Notes: {self.trip.notes}",
                style=Pack(margin=5, flex=1)
            )
            info_box.add(notes_label)

        # Main content split
        content_box = toga.Box(style=Pack(direction=ROW, flex=1))

        # Left side: Participants and cities management
        left_box = toga.Box(style=Pack(direction=COLUMN, flex=1))

        # Participants section
        participants_label = toga.Label("Participants (check to include)", style=Pack(margin=5, font_weight="bold"))

        # Create scrollable container for participant checkboxes
        self.participants_scroll = toga.ScrollContainer(style=Pack(flex=1, margin=5))
        self.participants_box = toga.Box(style=Pack(direction=COLUMN, margin=5))
        self.participants_scroll.content = self.participants_box

        # Dictionary to store checkboxes for each person
        self.participant_checkboxes = {}

        # Cities section
        cities_label = toga.Label("Cities Visited (double-click to view/edit notes)", style=Pack(margin=5, font_weight="bold"))
        cities_btn_box = toga.Box(style=Pack(direction=ROW, margin=5))
        add_city_btn = toga.Button(
            "Add City",
            on_press=self.add_city,
            style=Pack(margin=2)
        )
        view_notes_btn = toga.Button(
            "View/Edit Notes",
            on_press=self.view_city_notes,
            style=Pack(margin=2)
        )
        remove_city_btn = toga.Button(
            "Remove City",
            on_press=self.remove_city,
            style=Pack(margin=2)
        )
        cities_btn_box.add(add_city_btn)
        cities_btn_box.add(view_notes_btn)
        cities_btn_box.add(remove_city_btn)

        self.cities_table = toga.Table(
            headings=["City", "State/Province", "Country", "Notes"],
            data=[],
            on_activate=self.view_city_notes,
            style=Pack(flex=1, margin=5)
        )

        left_box.add(participants_label)
        left_box.add(self.participants_scroll)
        left_box.add(cities_label)
        left_box.add(cities_btn_box)
        left_box.add(self.cities_table)

        # Right side: Map
        right_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        map_label = toga.Label("Trip Map", style=Pack(margin=5, font_weight="bold"))
        self.map_view = CityMapView()

        right_box.add(map_label)
        right_box.add(self.map_view.widget)

        content_box.add(left_box)
        content_box.add(right_box)

        self.container.add(header_box)
        self.container.add(info_box)
        self.container.add(content_box)

        # Initialize data storage
        self.cities_with_notes = []

        # Load data
        self.refresh()

    def refresh(self) -> None:
        """Refresh trip data."""
        # Reload trip data to get any updates
        self.trip = self.repo.get_trip_by_id(self.trip_id)

        # Update the title label with new name if it changed
        header_box = self.container.children[0]
        for child in header_box.children:
            if isinstance(child, toga.Label) and child.style.font_weight == "bold":
                child.text = self.trip.name
                break

        # Update the info box with new dates and notes
        info_box = self.container.children[1]
        info_box.clear()
        duration = calculate_duration(self.trip.start_date, self.trip.end_date)
        dates_label = toga.Label(
            f"{self.trip.start_date} to {self.trip.end_date} ({duration} day{'s' if duration != 1 else ''})",
            style=Pack(margin=5)
        )
        info_box.add(dates_label)
        if self.trip.notes:
            notes_label = toga.Label(
                f"Notes: {self.trip.notes}",
                style=Pack(margin=5, flex=1)
            )
            info_box.add(notes_label)

        # Load all people and current participants
        all_people = self.repo.get_all_people()
        participants = self.repo.get_trip_participants(self.trip_id)
        participant_ids = {p.id for p in participants}

        # Clear and rebuild participant checkboxes
        self.participants_box.clear()
        self.participant_checkboxes.clear()

        for person in all_people:
            checkbox_row = toga.Box(style=Pack(direction=ROW, margin=2))
            checkbox = toga.Switch(
                text=person.name,
                value=person.id in participant_ids,
                on_change=lambda w, person_id=person.id: self.toggle_participant(person_id),
                style=Pack(margin_left=10, margin_top=5, margin_bottom=5, width=300)
            )
            self.participant_checkboxes[person.id] = checkbox
            checkbox_row.add(checkbox)
            self.participants_box.add(checkbox_row)

        # Load cities with notes
        self.cities_with_notes = self.repo.get_trip_cities_with_notes(self.trip_id)
        self.cities_table.data = [
            (c.name, c.admin_division or "", c.country_name, notes[:50] + "..." if notes and len(notes) > 50 else notes or "")
            for c, notes in self.cities_with_notes
        ]

        # Update map - extract just the cities for the map view
        cities = [c for c, _ in self.cities_with_notes]
        self.map_view.update_cities(cities)

    async def edit_trip(self, widget) -> None:
        """Edit the current trip's details."""
        from .trip_edit import TripEditDialog

        dialog = TripEditDialog(self.repo, self.trip)
        updated_trip = await dialog.show(self.app)

        if updated_trip:
            # Refresh the view to show updated trip details
            self.refresh()

    def toggle_participant(self, person_id: int) -> None:
        """Toggle a participant on or off for this trip.

        Args:
            person_id: ID of the person to toggle
        """
        # Check if the person is currently a participant
        participants = self.repo.get_trip_participants(self.trip_id)
        participant_ids = {p.id for p in participants}

        if person_id in participant_ids:
            # Remove from trip
            self.repo.remove_trip_participant(self.trip_id, person_id)
        else:
            # Add to trip
            self.repo.add_trip_participant(self.trip_id, person_id)

    async def view_city_notes(self, widget, row=None, **kwargs) -> None:
        """View and edit notes for the selected city."""
        if not self.cities_table.selection:
            await self.app.main_window.info_dialog(
                "No Selection",
                "Please select a city to view/edit its notes."
            )
            return

        # Get selected city information
        selected_row = self.cities_table.selection
        city_name = selected_row.city
        country = selected_row.country

        # Find the city and its notes from our stored data
        city_data = None
        current_notes = None
        for c, notes in self.cities_with_notes:
            if c.name == city_name and c.country_name == country:
                city_data = c
                current_notes = notes
                break

        if not city_data:
            return

        # Create dialog window for viewing/editing notes
        dialog = toga.Window(title=f"Notes for {city_data.display_name}", size=(500, 400))

        container = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Instructions
        instructions = toga.Label(
            f"View or edit notes for {city_data.display_name}:",
            style=Pack(margin=5, font_weight="bold")
        )

        # Notes input
        notes_input = toga.MultilineTextInput(
            value=current_notes or "",
            placeholder="Enter notes about this city visit...",
            style=Pack(flex=1, margin=5)
        )

        # Button row
        button_box = toga.Box(style=Pack(direction=ROW, margin=5))

        def save_notes(w):
            """Save the updated notes."""
            new_notes = notes_input.value.strip() if notes_input.value else None
            self.repo.update_trip_city_notes(self.trip_id, city_data.id, new_notes)
            self.refresh()
            dialog.close()

        save_btn = toga.Button(
            "Save",
            on_press=save_notes,
            style=Pack(margin=5, flex=1)
        )
        cancel_btn = toga.Button(
            "Cancel",
            on_press=lambda w: dialog.close(),
            style=Pack(margin=5, flex=1)
        )

        button_box.add(save_btn)
        button_box.add(cancel_btn)

        container.add(instructions)
        container.add(notes_input)
        container.add(button_box)

        dialog.content = container
        dialog.show()

    async def add_city(self, widget) -> None:
        """Add a city to the trip."""
        username = self.config.geonames_username
        if not username:
            await self.app.main_window.info_dialog(
                "GeoNames Username Required",
                f"Please add your GeoNames username to: {self.config.config_path}\n\n"
                f"Edit the file and set:\n"
                f'[geonames]\nusername = "your_username_here"'
            )
            return

        # Show city search dialog
        geonames_client = GeoNamesClient(username)
        search_dialog = CitySearchDialog(geonames_client, self.repo)

        result = await search_dialog.show(self.app)

        if result:
            selected_city, notes = result
            # Get or create city in database
            city = self.repo.get_or_create_city(selected_city)
            # Add to trip with notes
            self.repo.add_trip_city(self.trip_id, city.id, notes)
            self.refresh()

    async def remove_city(self, widget) -> None:
        """Remove selected city from trip."""
        if not self.cities_table.selection:
            await self.app.main_window.info_dialog(
                "No Selection",
                "Please select a city to remove."
            )
            return

        # Get selected row - it's a Row object with attributes matching the headings
        selected_row = self.cities_table.selection
        city_name = selected_row.city
        country = selected_row.country

        # Find the city
        city = next((c for c, _ in self.cities_with_notes if c.name == city_name and c.country_name == country), None)

        if city:
            confirm_dialog = toga.ConfirmDialog(
                "Confirm Remove",
                f"Remove {city.display_name} from this trip?"
            )
            if await self.app.main_window.dialog(confirm_dialog):
                self.repo.remove_trip_city(self.trip_id, city.id)
                self.refresh()

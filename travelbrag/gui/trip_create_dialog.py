"""Enhanced trip creation dialog with tabs for comprehensive trip setup."""

import asyncio
from datetime import date
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Optional, List, Tuple, Dict

from ..models import Trip, Person, City
from ..repository import Repository
from ..config import Config
from ..geonames import GeoNamesClient
from ..date_parser import validate_dates, parse_iso_date


class TripCreateDialog:
    """Enhanced dialog for creating a trip with travelers and cities."""

    def __init__(self, repo: Repository, config: Config):
        """Initialize enhanced trip creation dialog.

        Args:
            repo: Repository instance
            config: Configuration instance for GeoNames
        """
        self.repo = repo
        self.config = config
        self.result: Optional[Trip] = None

        # Track selected travelers and cities
        self.selected_travelers: List[Person] = []
        self.selected_cities: List[Tuple[City, Optional[str]]] = []  # (city, notes)

        # UI references
        self.name_input = None
        self.start_input = None
        self.start_validation_label = None
        self.end_input = None
        self.end_validation_label = None
        self.notes_input = None
        self.traveler_checkboxes: Dict[int, toga.Switch] = {}
        self.cities_table = None
        self.geonames_client = None
        self._updating_dates = False  # Prevent recursive updates

    async def show(self, app: toga.App) -> Optional[Trip]:
        """Show the enhanced trip creation dialog.

        Args:
            app: Toga application instance

        Returns:
            Created Trip object or None if cancelled
        """
        # Create dialog window
        dialog = toga.Window(title="Create New Trip", size=(700, 600))

        # Create tabs
        basic_info_tab = self.create_basic_info_tab()
        travelers_tab = self.create_travelers_tab()
        cities_tab = self.create_cities_tab(app)

        # Create tab container with all tabs
        tab_container = toga.OptionContainer(
            content=[
                ("Basic Info", basic_info_tab),
                ("Travelers", travelers_tab),
                ("Cities", cities_tab)
            ],
            style=Pack(flex=1)
        )

        # Main container with tabs and buttons
        main_container = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Instructions
        instructions = toga.Label(
            "Complete all tabs to create your trip. You can switch between tabs before saving.",
            style=Pack(margin=5, font_style="italic")
        )
        main_container.add(instructions)
        main_container.add(tab_container)

        # Button row
        button_box = toga.Box(style=Pack(direction=ROW, margin=10))
        save_btn = toga.Button(
            "Create Trip",
            on_press=lambda w: asyncio.create_task(
                self.save_complete_trip(app, dialog)
            ),
            style=Pack(margin=5, flex=1)
        )
        cancel_btn = toga.Button(
            "Cancel",
            on_press=lambda w: dialog.close(),
            style=Pack(margin=5, flex=1)
        )
        button_box.add(save_btn)
        button_box.add(cancel_btn)
        main_container.add(button_box)

        dialog.content = main_container
        dialog.show()

        # Wait for dialog to close
        while not dialog.closed:
            await asyncio.sleep(0.1)

        return self.result

    def create_basic_info_tab(self) -> toga.Box:
        """Create the basic info tab."""
        container = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Trip name
        name_box = toga.Box(style=Pack(direction=ROW, margin=5))
        name_label = toga.Label("Trip Name:", style=Pack(width=120, margin_right=5))
        self.name_input = toga.TextInput(
            placeholder="Enter trip name",
            style=Pack(flex=1)
        )
        name_box.add(name_label)
        name_box.add(self.name_input)

        # Start date with validation
        start_container = toga.Box(style=Pack(direction=COLUMN, margin=5))
        start_box = toga.Box(style=Pack(direction=ROW))
        start_label = toga.Label("Start Date:", style=Pack(width=120, margin_right=5))
        self.start_input = toga.TextInput(
            placeholder="YYYY-MM-DD or YYYY-MM",
            style=Pack(width=200),
            on_change=self.validate_and_update_dates
        )
        start_box.add(start_label)
        start_box.add(self.start_input)
        self.start_validation_label = toga.Label(
            "",
            style=Pack(margin_left=125, font_size=10, color="#FF0000")
        )
        start_container.add(start_box)
        start_container.add(self.start_validation_label)

        # End date with validation
        end_container = toga.Box(style=Pack(direction=COLUMN, margin=5))
        end_box = toga.Box(style=Pack(direction=ROW))
        end_label = toga.Label("End Date:", style=Pack(width=120, margin_right=5))
        self.end_input = toga.TextInput(
            placeholder="YYYY-MM-DD or YYYY-MM",
            style=Pack(width=200),
            on_change=self.validate_end_date
        )
        end_box.add(end_label)
        end_box.add(self.end_input)
        self.end_validation_label = toga.Label(
            "",
            style=Pack(margin_left=125, font_size=10, color="#FF0000")
        )
        end_container.add(end_box)
        end_container.add(self.end_validation_label)

        # Notes
        notes_label = toga.Label("Notes:", style=Pack(margin=5))
        self.notes_input = toga.MultilineTextInput(
            placeholder="Optional notes about the trip",
            style=Pack(flex=1, margin=5, height=200)
        )

        container.add(name_box)
        container.add(start_container)
        container.add(end_container)
        container.add(notes_label)
        container.add(self.notes_input)

        return container

    def validate_and_update_dates(self, widget):
        """Validate start date."""
        # Clear validation message
        self.start_validation_label.text = ""

        if not widget.value:
            return

        # Validate format
        parsed = parse_iso_date(widget.value.strip())
        if not parsed:
            self.start_validation_label.text = "Format: YYYY-MM-DD or YYYY-MM"
        else:
            # Re-validate end date if it exists
            if self.end_input.value:
                self.validate_end_date(None)

    def validate_end_date(self, widget):
        """Validate end date."""
        # Clear end date validation
        self.end_validation_label.text = ""

        end_str = self.end_input.value.strip() if self.end_input.value else ""
        if not end_str:
            return

        # Validate end date format
        if not parse_iso_date(end_str):
            self.end_validation_label.text = "Format: YYYY-MM-DD or YYYY-MM"
            return

        # If start date exists, check that end >= start
        start_str = self.start_input.value.strip() if self.start_input.value else ""
        if start_str and parse_iso_date(start_str):
            # ISO format strings compare correctly
            if end_str < start_str:
                self.end_validation_label.text = "Must be after start date"

    def create_travelers_tab(self) -> toga.Box:
        """Create the travelers selection tab."""
        container = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Instructions
        instructions = toga.Label(
            "Select people who will be on this trip:",
            style=Pack(margin=5, font_weight="bold")
        )
        container.add(instructions)

        # Get all people
        people = self.repo.get_all_people()

        if not people:
            no_people_label = toga.Label(
                "No people found. Add people from the People tab first.",
                style=Pack(margin=20, font_style="italic")
            )
            container.add(no_people_label)
        else:
            # Create scrollable container for checkboxes
            scroll_container = toga.ScrollContainer(style=Pack(flex=1))
            checkboxes_box = toga.Box(style=Pack(direction=COLUMN, margin=5))

            for person in people:
                checkbox_row = toga.Box(style=Pack(direction=ROW, margin=2))
                checkbox = toga.Switch(
                    text=person.name,
                    style=Pack(margin_left=10, margin_top=5, margin_bottom=5, width=300)
                )
                self.traveler_checkboxes[person.id] = checkbox
                checkbox_row.add(checkbox)
                checkboxes_box.add(checkbox_row)

            scroll_container.content = checkboxes_box
            container.add(scroll_container)

            # Quick actions
            actions_box = toga.Box(style=Pack(direction=ROW, margin=10))
            select_all_btn = toga.Button(
                "Select All",
                on_press=lambda w: self.select_all_travelers(True),
                style=Pack(margin=5)
            )
            clear_all_btn = toga.Button(
                "Clear All",
                on_press=lambda w: self.select_all_travelers(False),
                style=Pack(margin=5)
            )
            actions_box.add(select_all_btn)
            actions_box.add(clear_all_btn)
            container.add(actions_box)

        return container

    def create_cities_tab(self, app: toga.App) -> toga.Box:
        """Create the cities selection tab."""
        container = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Instructions
        instructions = toga.Label(
            "Add cities to visit on this trip:",
            style=Pack(margin=5, font_weight="bold")
        )
        container.add(instructions)

        # Add city button
        add_city_btn = toga.Button(
            "Add City",
            on_press=lambda w: asyncio.create_task(self.add_city(app)),
            style=Pack(margin=10)
        )
        container.add(add_city_btn)

        # Selected cities table
        cities_label = toga.Label(
            "Selected Cities (in order of visit):",
            style=Pack(margin=5, font_weight="bold")
        )
        container.add(cities_label)

        self.cities_table = toga.Table(
            headings=["City", "Country", "Notes"],
            data=[],
            style=Pack(flex=1, margin=5)
        )
        container.add(self.cities_table)

        # Remove button
        remove_btn = toga.Button(
            "Remove Selected City",
            on_press=self.remove_selected_city,
            style=Pack(margin=5)
        )
        container.add(remove_btn)

        return container

    def select_all_travelers(self, select: bool) -> None:
        """Select or deselect all travelers.

        Args:
            select: True to select all, False to deselect all
        """
        for checkbox in self.traveler_checkboxes.values():
            checkbox.value = select

    async def add_city(self, app: toga.App) -> None:
        """Add a city using the city search dialog."""
        # Check GeoNames configuration
        username = self.config.geonames_username
        if not username:
            await app.main_window.info_dialog(
                "GeoNames Username Required",
                f"Please add your GeoNames username to: {self.config.config_path}\n\n"
                f"Edit the file and set:\n"
                f'[geonames]\nusername = "your_username_here"'
            )
            return

        # Use the existing CitySearchDialog
        from .city_search import CitySearchDialog

        # Initialize GeoNames client if needed
        if not self.geonames_client:
            self.geonames_client = GeoNamesClient(username)

        search_dialog = CitySearchDialog(self.geonames_client, self.repo)
        result = await search_dialog.show(app)

        if result:
            selected_city, notes = result
            # Add to selected cities
            self.selected_cities.append((selected_city, notes))
            # Update table
            self.update_cities_table()

    def update_cities_table(self) -> None:
        """Update the cities table with selected cities."""
        self.cities_table.data = [
            (city.name, city.country_name, notes[:30] + "..." if notes and len(notes) > 30 else notes or "")
            for city, notes in self.selected_cities
        ]

    def remove_selected_city(self, widget) -> None:
        """Remove the selected city from the list."""
        if self.cities_table.selection:
            # Find the index of the selected row
            row_index = self.cities_table.data.index(self.cities_table.selection)
            # Remove from our list
            del self.selected_cities[row_index]
            # Update table
            self.update_cities_table()

    async def save_complete_trip(self, app: toga.App, dialog: toga.Window) -> None:
        """Save the complete trip with all travelers and cities.

        Args:
            app: Toga application instance
            dialog: Dialog window
        """
        # Validate basic info
        if not self.name_input.value or not self.name_input.value.strip():
            await app.main_window.info_dialog("Validation Error", "Trip name is required.")
            return

        # Validate dates
        start_str = self.start_input.value.strip()
        end_str = self.end_input.value.strip()

        start_date, end_date, error = validate_dates(start_str, end_str)

        if error:
            await app.main_window.info_dialog("Validation Error", error)
            return

        # Collect selected travelers
        people = self.repo.get_all_people()
        selected_travelers = [
            person for person in people
            if person.id in self.traveler_checkboxes and self.traveler_checkboxes[person.id].value
        ]

        # Confirm if no travelers or cities
        if not selected_travelers and not self.selected_cities:
            confirm_dialog = toga.ConfirmDialog(
                "No Travelers or Cities",
                "You haven't added any travelers or cities. Create the trip anyway?"
            )
            if not await app.main_window.dialog(confirm_dialog):
                return

        try:
            # Create the trip
            trip = Trip(
                id=None,
                name=self.name_input.value.strip(),
                notes=self.notes_input.value.strip() if self.notes_input.value.strip() else None,
                start_date=start_date,
                end_date=end_date
            )
            created_trip = self.repo.add_trip(trip)

            # Add travelers
            for person in selected_travelers:
                self.repo.add_trip_participant(created_trip.id, person.id)

            # Add cities with notes
            for city_data, notes in self.selected_cities:
                # Get or create city in database
                city = self.repo.get_or_create_city(city_data)
                self.repo.add_trip_city(created_trip.id, city.id, notes)

            self.result = created_trip
            dialog.close()

        except Exception as e:
            await app.main_window.info_dialog("Error", f"Failed to create trip: {e}")
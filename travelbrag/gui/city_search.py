"""City search dialog with country and admin division filters."""

import asyncio
from typing import Optional

import pycountry
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from ..geonames import GeoNamesClient
from ..models import City
from ..repository import Repository


def validate_country_code(value: str) -> Optional[str]:
    """Validate ISO 3166-1 alpha-2 country code.

    Args:
        value: The input value to validate

    Returns:
        None if valid, error message if invalid
    """
    if not value or not value.strip():
        # Empty is allowed (will search all countries)
        return None

    code = value.strip().upper()

    # Check length
    if len(code) != 2:
        return "Country code must be exactly 2 letters (e.g., US, GB, FR)"

    # Check if it's alphabetic
    if not code.isalpha():
        return "Country code must contain only letters"

    # Validate against pycountry database
    try:
        country = pycountry.countries.get(alpha_2=code)
        if not country:
            return f"'{code}' is not a valid ISO country code"
    except Exception:
        return f"'{code}' is not a valid ISO country code"

    return None  # Valid


class CitySearchDialog:
    """Dialog for searching and selecting cities using GeoNames."""

    def __init__(self, geonames_client: GeoNamesClient, repository: Repository):
        """Initialize city search dialog.

        Args:
            geonames_client: GeoNames API client
            repository: Repository for accessing visited cities
        """
        self.geonames_client = geonames_client
        self.repository = repository
        self.selected_city: Optional[City] = None
        self.notes: Optional[str] = None
        self.visited_cities: list[City] = []  # Cities visited in current country
        self.filtered_cities: list[City] = []  # Filtered visited cities based on typing
        self.search_results: list[City] = []  # Results from GeoNames search

    async def show(self, app: toga.App) -> Optional[tuple[City, Optional[str]]]:
        """Show the city search dialog.

        Args:
            app: Toga application instance

        Returns:
            Tuple of (Selected City object, notes) or None if cancelled
        """
        # Create dialog window
        dialog = toga.Window(title="Search for City", size=(600, 600))

        container = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Instructions
        instructions = toga.Label(
            "Search for a city by entering the ISO country code and city name.",
            style=Pack(margin=5),
        )

        # We need to pre-declare these to use in event handlers
        status_label = toga.Label(
            "",
            style=Pack(margin=5, font_size=12)
        )

        # Results table (created early so we can reference it in handlers)
        results_table = toga.Table(
            headings=["City", "State/Province", "Country"],
            data=[],
            style=Pack(flex=1, margin=5),
        )

        # Country input with change handler
        country_box = toga.Box(style=Pack(direction=ROW, margin=5))
        country_label = toga.Label(
            "Country Code:", style=Pack(width=100, margin_right=5)
        )

        # Store reference for city input (will be assigned later)
        self.city_input_ref = None

        def on_country_change(widget):
            """Handle country input changes."""
            city_value = self.city_input_ref.value if self.city_input_ref else ""
            self.on_country_changed(
                widget.value,
                city_value,
                results_table,
                status_label
            )

        country_input = toga.TextInput(
            placeholder="US",
            validators=[validate_country_code],
            on_change=on_country_change,
            style=Pack(width=60)  # Small width for 2 characters
        )
        country_hint = toga.Label(
            "(2-letter ISO code, e.g., US, GB, FR, CA)",
            style=Pack(margin_left=10, font_size=10)
        )
        country_box.add(country_label)
        country_box.add(country_input)
        country_box.add(country_hint)

        # City name input
        city_box = toga.Box(style=Pack(direction=ROW, margin=5))
        city_label = toga.Label("City Name:", style=Pack(width=100, margin_right=5))

        def on_city_change(widget):
            """Handle city input changes."""
            self.on_city_typing(widget.value, results_table, status_label)

        city_input = toga.TextInput(
            placeholder="e.g., Vancouver",
            on_change=on_city_change,
            style=Pack(flex=1)
        )
        self.city_input_ref = city_input  # Store reference for country change handler
        city_box.add(city_label)
        city_box.add(city_input)

        # Search button
        search_btn = toga.Button(
            "Search",
            on_press=lambda w: asyncio.create_task(
                self.perform_search(
                    app,
                    city_input.value,
                    country_input.value,
                    results_table,
                    search_btn,
                    status_label
                )
            ),
            style=Pack(margin=5),
        )

        # Notes input
        notes_box = toga.Box(style=Pack(direction=COLUMN, margin=5))
        notes_label = toga.Label("Notes (optional):", style=Pack(margin_bottom=5))
        notes_input = toga.MultilineTextInput(
            placeholder="e.g., Visit the waterfront, stayed 3 nights, great seafood restaurant near the harbor",
            style=Pack(flex=1, height=80)
        )
        notes_box.add(notes_label)
        notes_box.add(notes_input)

        # Button row
        button_box = toga.Box(style=Pack(direction=ROW, margin=5))
        select_btn = toga.Button(
            "Select",
            on_press=lambda w: self.select_city(results_table, notes_input, dialog),
            style=Pack(margin=5, flex=1),
        )
        cancel_btn = toga.Button(
            "Cancel", on_press=lambda w: dialog.close(), style=Pack(margin=5, flex=1)
        )
        button_box.add(select_btn)
        button_box.add(cancel_btn)

        container.add(instructions)
        container.add(country_box)
        container.add(city_box)
        container.add(search_btn)
        container.add(status_label)
        container.add(results_table)
        container.add(notes_box)
        container.add(button_box)

        dialog.content = container

        # Store results table reference
        self.results_table = results_table

        dialog.show()

        # Wait for dialog to close
        while not dialog.closed:
            await asyncio.sleep(0.1)

        if self.selected_city:
            return (self.selected_city, self.notes)
        return None

    async def perform_search(
        self, app: toga.App, city_name: str, country_code: str, results_table: toga.Table,
        search_btn: toga.Button, status_label: toga.Label
    ) -> None:
        """Perform city search using GeoNames API.

        Args:
            app: Toga application instance
            city_name: City name to search for
            country_code: ISO 3166-1 alpha-2 country code
            results_table: Table to display results
            search_btn: Search button to disable during search
            status_label: Label to show search status
        """
        if not city_name or not city_name.strip():
            await app.main_window.dialog(
                toga.InfoDialog(
                    "Validation Error",
                    "Please enter a city name."
                )
            )
            return

        # The country code has already been validated by the TextInput validator
        # Just normalize it to uppercase
        country_code = country_code.strip().upper() if country_code else ""

        # Disable search button and show loading status
        search_btn.enabled = False
        status_label.text = "🔍 Searching GeoNames..."

        try:
            cities = await self.geonames_client.search_cities(
                query=city_name.strip(), country=country_code, max_results=20
            )

            self.search_results = cities
            results_table.data = [
                (c.name, c.admin_division or "", c.country_name) for c in cities
            ]

            # Update status with result count
            if cities:
                status_label.text = f"✅ Found {len(cities)} result{'s' if len(cities) != 1 else ''}"
            else:
                status_label.text = "⚠️ No cities found"

        except Exception as e:
            await app.main_window.dialog(
                toga.InfoDialog(
                    "Search Error",
                    f"Failed to search for cities: {e}"
                )
            )
            self.search_results = []
            results_table.data = []
            status_label.text = "❌ Search failed"

        finally:
            # Re-enable search button
            search_btn.enabled = True

    def on_country_changed(self, country_code: str, city_filter: str,
                           results_table: toga.Table, status_label: toga.Label) -> None:
        """Handle country code change - populate with visited cities.

        Args:
            country_code: The entered country code
            city_filter: Current city name filter
            results_table: Table to populate
            status_label: Label to show status
        """
        # Clear any existing search results
        self.search_results = []

        if not country_code or not country_code.strip():
            # Clear the table if no country is selected
            self.visited_cities = []
            self.filtered_cities = []
            results_table.data = []
            status_label.text = ""
            return

        # Validate and normalize country code
        country_code = country_code.strip().upper()

        # Only proceed if we have a complete 2-letter code
        if len(country_code) != 2:
            self.visited_cities = []
            self.filtered_cities = []
            results_table.data = []
            status_label.text = ""
            return

        error = validate_country_code(country_code)
        if error:
            # Invalid country code, clear the table
            self.visited_cities = []
            self.filtered_cities = []
            results_table.data = []
            status_label.text = ""
            return

        # Get visited cities for this country
        try:
            self.visited_cities = self.repository.get_visited_cities_by_country(country_code)
        except Exception as e:
            # Silently handle errors to avoid crashing the dialog
            self.visited_cities = []

        # Apply city name filter if present
        if city_filter and city_filter.strip():
            self.filter_visited_cities(city_filter, results_table, status_label)
        else:
            # Show all visited cities for this country
            self.filtered_cities = self.visited_cities
            results_table.data = [
                (c.name, c.admin_division or "", c.country_name) for c in self.filtered_cities
            ]

            # Update status
            if self.filtered_cities:
                status_label.text = f"📍 Showing {len(self.filtered_cities)} previously visited cit{'y' if len(self.filtered_cities) == 1 else 'ies'}"
            else:
                status_label.text = "📍 No previously visited cities in this country"

    def on_city_typing(self, city_filter: str, results_table: toga.Table, status_label: toga.Label) -> None:
        """Handle typing in city input - filter visited cities.

        Args:
            city_filter: The typed city name filter
            results_table: Table to update
            status_label: Label to show status
        """
        # Only filter if we have visited cities loaded (country is selected)
        if not self.visited_cities:
            return

        self.filter_visited_cities(city_filter, results_table, status_label)

    def filter_visited_cities(self, city_filter: str, results_table: toga.Table, status_label: toga.Label) -> None:
        """Filter visited cities based on typed text.

        Args:
            city_filter: The filter text
            results_table: Table to update
            status_label: Label to show status
        """
        if not city_filter or not city_filter.strip():
            # No filter, show all visited cities
            self.filtered_cities = self.visited_cities
        else:
            # Filter cities by name (case-insensitive)
            filter_lower = city_filter.strip().lower()
            self.filtered_cities = [
                c for c in self.visited_cities
                if filter_lower in c.name.lower()
            ]

        # Update table
        results_table.data = [
            (c.name, c.admin_division or "", c.country_name) for c in self.filtered_cities
        ]

        # Update status with filtered count
        if self.filtered_cities:
            status_label.text = f"📍 Showing {len(self.filtered_cities)} previously visited cit{'y' if len(self.filtered_cities) == 1 else 'ies'}"
        else:
            status_label.text = "📍 No matching cities found"

    def select_city(self, results_table: toga.Table, notes_input: toga.MultilineTextInput, dialog: toga.Window) -> None:
        """Select a city from search results.

        Args:
            results_table: Table with search results
            notes_input: Text input for notes
            dialog: Dialog window to close
        """
        if results_table.selection:
            # Determine which list to use based on what's currently displayed
            if self.search_results:
                # User performed a search, use search results
                selected_index = results_table.data.index(results_table.selection)
                self.selected_city = self.search_results[selected_index]
            elif self.filtered_cities:
                # User is selecting from visited cities
                selected_index = results_table.data.index(results_table.selection)
                self.selected_city = self.filtered_cities[selected_index]

            self.notes = notes_input.value.strip() if notes_input.value else None

        dialog.close()

"""Trip add/edit dialog."""

import asyncio
from datetime import date
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Optional

from ..models import Trip
from ..repository import Repository
from ..date_parser import validate_dates, parse_iso_date


class TripEditDialog:
    """Dialog for creating or editing a trip."""

    def __init__(self, repo: Repository, trip: Optional[Trip] = None):
        """Initialize trip edit dialog.

        Args:
            repo: Repository instance
            trip: Trip to edit, or None to create new trip
        """
        self.repo = repo
        self.trip = trip
        self.result: Optional[Trip] = None
        self._updating_dates = False  # Prevent recursive updates

    async def show(self, app: toga.App) -> Optional[Trip]:
        """Show the trip edit dialog.

        Args:
            app: Toga application instance

        Returns:
            Created/updated Trip object or None if cancelled
        """
        # Create dialog window
        title = "Edit Trip" if self.trip else "Add Trip"
        dialog = toga.Window(title=title, size=(500, 400))

        container = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Trip name
        name_box = toga.Box(style=Pack(direction=ROW, margin=5))
        name_label = toga.Label("Trip Name:", style=Pack(width=120, margin_right=5))
        name_input = toga.TextInput(
            placeholder="Enter trip name",
            value=self.trip.name if self.trip else "",
            style=Pack(flex=1)
        )
        name_box.add(name_label)
        name_box.add(name_input)

        # Start date with validation
        start_container = toga.Box(style=Pack(direction=COLUMN, margin=5))
        start_box = toga.Box(style=Pack(direction=ROW))
        start_label = toga.Label("Start Date:", style=Pack(width=120, margin_right=5))
        start_input = toga.TextInput(
            placeholder="YYYY-MM-DD or YYYY-MM",
            value=self.trip.start_date if self.trip else "",
            style=Pack(width=200)
        )
        start_box.add(start_label)
        start_box.add(start_input)
        start_validation_label = toga.Label(
            "",
            style=Pack(margin_left=125, font_size=10, color="#FF0000")
        )
        start_container.add(start_box)
        start_container.add(start_validation_label)

        # End date with validation
        end_container = toga.Box(style=Pack(direction=COLUMN, margin=5))
        end_date_box = toga.Box(style=Pack(direction=ROW))
        end_label = toga.Label("End Date:", style=Pack(width=120, margin_right=5))
        end_input = toga.TextInput(
            placeholder="YYYY-MM-DD or YYYY-MM",
            value=self.trip.end_date if self.trip else "",
            style=Pack(width=200)
        )
        end_date_box.add(end_label)
        end_date_box.add(end_input)
        end_validation_label = toga.Label(
            "",
            style=Pack(margin_left=125, font_size=10, color="#FF0000")
        )
        end_container.add(end_date_box)
        end_container.add(end_validation_label)

        # Event handlers for date validation
        def validate_start_date(widget):
            """Validate start date."""
            start_validation_label.text = ""
            if not widget.value:
                return
            parsed = parse_iso_date(widget.value.strip())
            if not parsed:
                start_validation_label.text = "Format: YYYY-MM-DD or YYYY-MM"
            else:
                # Re-validate end date if it exists
                if end_input.value:
                    validate_end_date(None)

        def validate_end_date(widget):
            """Validate end date."""
            end_validation_label.text = ""
            end_str = end_input.value.strip() if end_input.value else ""
            if not end_str:
                return
            # Validate end date format
            if not parse_iso_date(end_str):
                end_validation_label.text = "Format: YYYY-MM-DD or YYYY-MM"
                return
            # If start date exists, check that end >= start
            start_str = start_input.value.strip() if start_input.value else ""
            if start_str and parse_iso_date(start_str):
                # ISO format strings compare correctly
                if end_str < start_str:
                    end_validation_label.text = "Must be after start date"

        # Connect event handlers
        start_input.on_change = validate_start_date
        end_input.on_change = validate_end_date

        # Notes
        notes_box = toga.Box(style=Pack(direction=COLUMN, margin=5))
        notes_label = toga.Label("Notes:", style=Pack(margin_bottom=5))
        notes_input = toga.MultilineTextInput(
            placeholder="Optional notes about the trip",
            value=self.trip.notes if self.trip and self.trip.notes else "",
            style=Pack(flex=1, height=150)
        )
        notes_box.add(notes_label)
        notes_box.add(notes_input)

        # Button row
        button_box = toga.Box(style=Pack(direction=ROW, margin=5))
        save_btn = toga.Button(
            "Save",
            on_press=lambda w: asyncio.create_task(
                self.save_trip(
                    app,
                    dialog,
                    name_input.value,
                    start_input.value,
                    end_input.value,
                    notes_input.value
                )
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

        container.add(name_box)
        container.add(start_container)
        container.add(end_container)
        container.add(notes_box)
        container.add(button_box)

        dialog.content = container
        dialog.show()

        # Wait for dialog to close
        while not dialog.closed:
            await asyncio.sleep(0.1)

        return self.result

    async def save_trip(
        self,
        app: toga.App,
        dialog: toga.Window,
        name: str,
        start_date_str: str,
        end_date_str: str,
        notes: str
    ) -> None:
        """Save the trip.

        Args:
            app: Toga application instance
            dialog: Dialog window
            name: Trip name
            start_date_str: Start date string
            end_date_str: End date string
            notes: Trip notes
        """
        # Validate inputs
        if not name or not name.strip():
            await app.main_window.info_dialog("Validation Error", "Trip name is required.")
            return

        # Validate dates
        start_date, end_date, error = validate_dates(
            start_date_str.strip(),
            end_date_str.strip()
        )

        if error:
            await app.main_window.info_dialog("Validation Error", error)
            return

        # Create or update trip
        try:
            if self.trip:
                # Update existing trip
                self.trip.name = name.strip()
                self.trip.start_date = start_date
                self.trip.end_date = end_date
                self.trip.notes = notes.strip() if notes.strip() else None
                self.repo.update_trip(self.trip)
                self.result = self.trip
            else:
                # Create new trip
                trip = Trip(
                    id=None,
                    name=name.strip(),
                    notes=notes.strip() if notes.strip() else None,
                    start_date=start_date,
                    end_date=end_date
                )
                self.result = self.repo.add_trip(trip)

            dialog.close()

        except Exception as e:
            await app.main_window.info_dialog("Error", f"Failed to save trip: {e}")

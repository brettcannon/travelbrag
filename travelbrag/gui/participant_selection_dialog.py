"""Participant selection dialog with checkboxes for consistent UI."""

import asyncio
from typing import List, Optional
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from ..models import Person
from ..repository import Repository


class ParticipantSelectionDialog:
    """Dialog for selecting participants using checkboxes."""

    def __init__(self, repo: Repository, trip_id: int):
        """Initialize participant selection dialog.

        Args:
            repo: Repository instance
            trip_id: ID of the trip to add participants to
        """
        self.repo = repo
        self.trip_id = trip_id
        self.selected_people: List[Person] = []

    async def show(self, app: toga.App) -> List[Person]:
        """Show the participant selection dialog.

        Args:
            app: Toga application instance

        Returns:
            List of selected Person objects
        """
        # Get all people and current participants
        all_people = self.repo.get_all_people()
        current_participants = self.repo.get_trip_participants(self.trip_id)
        current_ids = {p.id for p in current_participants}

        # Filter to people not already participating
        available_people = [p for p in all_people if p.id not in current_ids]

        if not available_people:
            await app.main_window.info_dialog(
                "No Available People",
                "All people are already participants, or no people exist. Add people from the People tab first."
            )
            return []

        # Create dialog window
        dialog = toga.Window(title="Select Participants", size=(400, 500))

        container = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Instructions
        instructions = toga.Label(
            "Select people to add to this trip:",
            style=Pack(margin=5, font_weight="bold")
        )
        container.add(instructions)

        # Create scrollable container for checkboxes
        scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        checkboxes_box = toga.Box(style=Pack(direction=COLUMN, margin=5))

        # Store checkboxes for later access
        checkboxes = {}

        for person in available_people:
            checkbox_row = toga.Box(style=Pack(direction=ROW, margin=2))
            checkbox = toga.Switch(
                text=person.name,
                style=Pack(margin_left=10, margin_top=5, margin_bottom=5, width=300)
            )
            checkboxes[person.id] = (checkbox, person)
            checkbox_row.add(checkbox)
            checkboxes_box.add(checkbox_row)

        scroll_container.content = checkboxes_box
        container.add(scroll_container)

        # Quick actions
        actions_box = toga.Box(style=Pack(direction=ROW, margin=10))

        def select_all(widget):
            for checkbox, _ in checkboxes.values():
                checkbox.value = True

        def clear_all(widget):
            for checkbox, _ in checkboxes.values():
                checkbox.value = False

        select_all_btn = toga.Button(
            "Select All",
            on_press=select_all,
            style=Pack(margin=5)
        )
        clear_all_btn = toga.Button(
            "Clear All",
            on_press=clear_all,
            style=Pack(margin=5)
        )
        actions_box.add(select_all_btn)
        actions_box.add(clear_all_btn)
        container.add(actions_box)

        # Button row
        button_box = toga.Box(style=Pack(direction=ROW, margin=5))

        def save_selection(widget):
            # Collect selected people
            self.selected_people = [
                person for checkbox, person in checkboxes.values()
                if checkbox.value
            ]
            dialog.close()

        save_btn = toga.Button(
            "Add Selected",
            on_press=save_selection,
            style=Pack(margin=5, flex=1)
        )
        cancel_btn = toga.Button(
            "Cancel",
            on_press=lambda w: dialog.close(),
            style=Pack(margin=5, flex=1)
        )
        button_box.add(save_btn)
        button_box.add(cancel_btn)
        container.add(button_box)

        dialog.content = container
        dialog.show()

        # Wait for dialog to close
        while not dialog.closed:
            await asyncio.sleep(0.1)

        return self.selected_people
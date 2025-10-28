"""People management view for adding/removing/editing family members."""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Callable, Optional

from ..repository import Repository
from ..models import Person
from .text_input_dialog import TextInputDialog


class PeopleView:
    """View for managing family members."""

    def __init__(self, app: toga.App, repo: Repository, on_person_selected: Callable[[int], None]):
        """Initialize people view.

        Args:
            app: Toga application instance
            repo: Repository instance
            on_person_selected: Callback when person is selected
        """
        self.app = app
        self.repo = repo
        self.on_person_selected = on_person_selected

        # Create main container
        self.container = toga.Box(style=Pack(direction=COLUMN, flex=1, margin=10))

        # Title
        title = toga.Label("Family Members", style=Pack(margin=5, font_size=16, font_weight="bold"))

        # Button row
        button_box = toga.Box(style=Pack(direction=ROW, margin=5))
        add_btn = toga.Button("Add Person", on_press=self.add_person, style=Pack(margin=5))
        edit_btn = toga.Button("Edit Person", on_press=self.edit_person, style=Pack(margin=5))
        delete_btn = toga.Button("Delete Person", on_press=self.delete_person, style=Pack(margin=5))

        button_box.add(add_btn)
        button_box.add(edit_btn)
        button_box.add(delete_btn)

        # People table
        self.people_table = toga.Table(
            headings=["ID", "Name"],
            data=[],
            on_select=self.on_table_select,
            style=Pack(flex=1, margin=5)
        )

        self.container.add(title)
        self.container.add(button_box)
        self.container.add(self.people_table)

        self.selected_person: Optional[Person] = None

    def refresh(self) -> None:
        """Refresh the people list."""
        people = self.repo.get_all_people()
        self.people_table.data = [(p.id, p.name) for p in people]

    def on_table_select(self, widget) -> None:
        """Handle table row selection.

        Args:
            widget: Table widget
        """
        if widget.selection:
            # Get selected row - it's a Row object, not a list
            person_id = widget.selection.id
            self.selected_person = self.repo.get_person_by_id(person_id)

    async def add_person(self, widget) -> None:
        """Show dialog to add a new person."""
        dialog = TextInputDialog(
            "Add Person",
            "Enter person's name:"
        )
        dialog.show()
        name = await dialog

        if name and name.strip():
            person = Person(id=None, name=name.strip())
            self.repo.add_person(person)
            self.refresh()

    async def edit_person(self, widget) -> None:
        """Show dialog to edit selected person."""
        if not self.selected_person:
            await self.app.main_window.info_dialog(
                "No Selection",
                "Please select a person to edit."
            )
            return

        dialog = TextInputDialog(
            "Edit Person",
            "Enter new name:",
            initial_value=self.selected_person.name
        )
        dialog.show()
        new_name = await dialog

        if new_name and new_name.strip():
            self.selected_person.name = new_name.strip()
            self.repo.update_person(self.selected_person)
            self.refresh()

    async def delete_person(self, widget) -> None:
        """Delete selected person with confirmation."""
        if not self.selected_person:
            await self.app.main_window.info_dialog(
                "No Selection",
                "Please select a person to delete."
            )
            return

        confirm_dialog = toga.ConfirmDialog(
            "Confirm Delete",
            f"Are you sure you want to delete {self.selected_person.name}? "
            f"This will also remove them from all trips."
        )
        confirmed = await self.app.main_window.dialog(confirm_dialog)

        if confirmed:
            self.repo.delete_person(self.selected_person.id)
            self.selected_person = None
            self.refresh()

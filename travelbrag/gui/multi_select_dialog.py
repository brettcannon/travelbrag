"""Custom multi-select dialog for Toga."""

import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Optional


class MultiSelectDialog:
    """A dialog that prompts the user to select multiple items from a list."""

    def __init__(self, title: str, message: str, items: list[str]):
        """Initialize the multi-select dialog.

        Args:
            title: Dialog title
            message: Prompt message to display
            items: List of items to choose from
        """
        self.title = title
        self.message = message
        self.items = items
        self.result: list[str] = []

    async def show(self, app: toga.App) -> list[str]:
        """Show the multi-select dialog.

        Args:
            app: Toga application instance

        Returns:
            List of selected items (empty list if cancelled)
        """
        # Create dialog window
        dialog = toga.Window(title=self.title, size=(500, 400))

        # Create the UI
        main_box = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Message label
        label = toga.Label(self.message, style=Pack(margin=(0, 0, 10, 0)))

        # Multi-select table
        # Convert items to table data format (single column)
        table_data = [(item,) for item in self.items]

        selection_table = toga.Table(
            headings=["Name"],
            data=table_data,
            multiple_select=True,
            style=Pack(margin=5, flex=1)
        )

        # Status label
        status_label = toga.Label(
            "Select one or more items (Ctrl/Cmd+Click for multiple)",
            style=Pack(margin=5)
        )

        # Button row
        button_box = toga.Box(style=Pack(direction=ROW, margin=(10, 0, 0, 0)))

        def update_status(widget):
            """Update status label when selection changes."""
            if selection_table.selection:
                count = len(selection_table.selection)
                status_label.text = f"{count} item{'s' if count != 1 else ''} selected"
            else:
                status_label.text = "No items selected"

        # Set handler for selection changes
        selection_table.on_select = update_status

        cancel_button = toga.Button(
            "Cancel",
            on_press=lambda w: dialog.close(),
            style=Pack(margin=5, flex=1)
        )

        ok_button = toga.Button(
            "Add Selected",
            on_press=lambda w: self._on_ok(dialog, selection_table.selection),
            style=Pack(margin=5, flex=1)
        )

        button_box.add(cancel_button)
        button_box.add(ok_button)

        main_box.add(label)
        main_box.add(selection_table)
        main_box.add(status_label)
        main_box.add(button_box)

        dialog.content = main_box
        dialog.show()

        # Wait for dialog to close
        while not dialog.closed:
            await asyncio.sleep(0.1)

        return self.result

    def _on_ok(self, dialog: toga.Window, selection) -> None:
        """Handle OK button press.

        Args:
            dialog: Dialog window
            selection: Selected rows (list of Row objects)
        """
        if selection:
            # Extract the name from each selected row
            self.result = [row.name for row in selection]
        else:
            self.result = []
        dialog.close()

"""Custom selection dialog for Toga."""

import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from typing import Optional


class SelectionDialog:
    """A dialog that prompts the user to select from a list."""

    def __init__(self, title: str, message: str, items: list[str]):
        """Initialize the selection dialog.

        Args:
            title: Dialog title
            message: Prompt message to display
            items: List of items to choose from
        """
        self.title = title
        self.message = message
        self.items = items
        self.result: Optional[str] = None

    async def show(self, app: toga.App) -> Optional[str]:
        """Show the selection dialog.

        Args:
            app: Toga application instance

        Returns:
            Selected item or None if cancelled
        """
        # Create dialog window
        dialog = toga.Window(title=self.title, size=(400, 200))

        # Create the UI
        main_box = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Message label
        label = toga.Label(self.message, style=Pack(margin=(0, 0, 10, 0)))

        # Selection widget
        selection = toga.Selection(
            items=self.items,
            style=Pack(margin=5, flex=1)
        )

        # Button row
        button_box = toga.Box(style=Pack(direction=ROW, margin=(10, 0, 0, 0)))

        cancel_button = toga.Button(
            "No",
            on_press=lambda w: dialog.close(),
            style=Pack(margin=5, flex=1)
        )

        ok_button = toga.Button(
            "Yes",
            on_press=lambda w: self._on_ok(dialog, selection.value),
            style=Pack(margin=5, flex=1)
        )

        button_box.add(cancel_button)
        button_box.add(ok_button)

        main_box.add(label)
        main_box.add(selection)
        main_box.add(button_box)

        dialog.content = main_box
        dialog.show()

        # Wait for dialog to close
        while not dialog.closed:
            await asyncio.sleep(0.1)

        return self.result

    def _on_ok(self, dialog: toga.Window, value: str) -> None:
        """Handle OK button press.

        Args:
            dialog: Dialog window
            value: Selected value
        """
        self.result = value
        dialog.close()

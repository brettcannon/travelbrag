"""Custom text input dialog for Toga."""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class TextInputDialog(toga.Window):
    """A dialog that prompts the user for text input."""

    def __init__(self, title: str, message: str, initial_value: str = ""):
        """Initialize the text input dialog.

        Args:
            title: Dialog title
            message: Prompt message to display
            initial_value: Initial value for the text input
        """
        super().__init__(title=title, resizable=False, closable=True)

        # Create the UI
        main_box = toga.Box(style=Pack(direction=COLUMN, margin=10))

        # Message label
        label = toga.Label(message, style=Pack(margin=(0, 0, 10, 0)))

        # Text input
        self.text_input = toga.TextInput(
            value=initial_value,
            style=Pack(margin=5, width=300)
        )

        # Button row
        button_box = toga.Box(style=Pack(direction=ROW, margin=(10, 0, 0, 0)))

        cancel_button = toga.Button(
            "Cancel",
            on_press=self.on_cancel,
            style=Pack(margin=5, flex=1)
        )

        ok_button = toga.Button(
            "OK",
            on_press=self.on_ok,
            style=Pack(margin=5, flex=1)
        )

        button_box.add(cancel_button)
        button_box.add(ok_button)

        main_box.add(label)
        main_box.add(self.text_input)
        main_box.add(button_box)

        self.content = main_box
        self.future = self.app.loop.create_future()

    def on_ok(self, widget) -> None:
        """Handle OK button press."""
        self.future.set_result(self.text_input.value)
        self.close()

    def on_cancel(self, widget) -> None:
        """Handle Cancel button press."""
        self.future.set_result(None)
        self.close()

    def __await__(self):
        """Make the dialog awaitable."""
        return self.future.__await__()

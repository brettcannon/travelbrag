"""Tests for main window GUI."""

import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock

import toga
from travelbrag.gui.main_window import MainWindow


@pytest.fixture
def mock_app():
    """Create a mock Toga app."""
    os.environ["TOGA_BACKEND"] = "toga_dummy"
    app = Mock(spec=toga.App)
    return app


@pytest.fixture
def mock_config():
    """Create a mock config."""
    config = Mock()
    with tempfile.TemporaryDirectory() as tmpdir:
        config.database_path = Path(tmpdir) / "test.db"
        yield config


@pytest.fixture
def mock_db():
    """Create a mock database."""
    return Mock()


@pytest.fixture
def mock_repo():
    """Create a mock repository."""
    repo = Mock()
    repo.get_all_trips.return_value = []
    repo.get_all_people.return_value = []
    repo.get_all_visited_cities.return_value = []
    return repo


@pytest.fixture
def main_window(mock_app, mock_config, mock_db, mock_repo):
    """Create a MainWindow instance for testing."""
    window = MainWindow(mock_app, mock_config, mock_db, mock_repo)
    return window


def test_main_window_creation(main_window):
    """Test that main window can be created."""
    assert main_window is not None
    assert hasattr(main_window, 'container')
    assert isinstance(main_window.container, toga.Box)


def test_main_window_has_navigation_buttons(main_window):
    """Test that main window has navigation buttons."""
    assert hasattr(main_window, 'trips_btn')
    assert hasattr(main_window, 'people_btn')
    assert isinstance(main_window.trips_btn, toga.Button)
    assert isinstance(main_window.people_btn, toga.Button)
    assert main_window.trips_btn.text == "All Trips"
    assert main_window.people_btn.text == "People"


def test_main_window_has_content_area(main_window):
    """Test that main window has a content area."""
    assert hasattr(main_window, 'content_box')
    assert isinstance(main_window.content_box, toga.Box)


def test_main_window_initializes_with_trips_view(main_window):
    """Test that main window initializes showing trips view."""
    # The trips overview should be in the content box
    assert len(main_window.content_box.children) > 0


def test_show_trips_view(main_window, mock_repo):
    """Test switching to trips view."""
    # Clear content first
    main_window.content_box.clear()
    assert len(main_window.content_box.children) == 0

    # Show trips view
    main_window.show_trips_view(None)

    # Content should now contain trips overview
    assert len(main_window.content_box.children) > 0


def test_show_people_view(main_window, mock_repo):
    """Test switching to people view."""
    # Start with trips view
    main_window.show_trips_view(None)
    initial_children = main_window.content_box.children[:]

    # Switch to people view
    main_window.show_people_view(None)

    # Content should have changed
    assert len(main_window.content_box.children) > 0


def test_on_trip_selected(main_window, mock_repo):
    """Test trip selection handler."""
    # Mock a trip in the repository
    trip_id = 1
    mock_trip = Mock()
    mock_trip.id = trip_id
    mock_trip.name = "Test Trip"
    mock_trip.start_date = "2024-01-01"
    mock_trip.end_date = "2024-01-07"
    mock_trip.notes = None
    mock_repo.get_trip_by_id.return_value = mock_trip
    mock_repo.get_trip_participants.return_value = []
    mock_repo.get_trip_cities.return_value = []
    mock_repo.get_trip_cities_with_notes.return_value = []

    # Select the trip
    main_window.on_trip_selected(trip_id)

    # Content should have changed to trip detail view
    assert len(main_window.content_box.children) > 0


def test_on_person_selected(main_window, mock_repo):
    """Test person selection handler."""
    # Mock a person in the repository
    person_id = 1
    mock_person = Mock()
    mock_person.id = person_id
    mock_person.name = "Test Person"
    mock_repo.get_person_by_id.return_value = mock_person
    mock_repo.get_trips_by_person.return_value = []
    mock_repo.get_person_trips.return_value = []
    mock_repo.get_person_cities.return_value = []

    # Select the person
    main_window.on_person_selected(person_id)

    # Content should have changed to person detail view
    assert len(main_window.content_box.children) > 0


def test_navigation_button_handlers_wired(main_window):
    """Test that navigation buttons have handlers wired correctly."""
    assert main_window.trips_btn.on_press is not None
    assert main_window.people_btn.on_press is not None


@pytest.mark.asyncio
async def test_people_view_add_person_dialog(main_window, mock_repo):
    """Test that add person dialog can be invoked without errors."""
    # Show people view
    main_window.show_people_view(None)

    # Get the people view
    people_view = main_window.people_view

    # Mock the TextInputDialog to avoid actually showing a dialog
    from unittest.mock import patch, Mock

    # Create a simple awaitable mock
    async def mock_await():
        return "Test Name"

    class MockDialog:
        def __init__(self, *args, **kwargs):
            pass

        def show(self):
            pass

        def __await__(self):
            return mock_await().__await__()

    with patch('travelbrag.gui.people_view.TextInputDialog', MockDialog):
        # This should not raise AttributeError
        await people_view.add_person(None)

        # Verify that add_person was called on the repository
        mock_repo.add_person.assert_called_once()

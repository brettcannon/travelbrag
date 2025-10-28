"""Tests for main Travelbrag application."""

import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

import toga
from travelbrag.app import TravelbragApp


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield db_path


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def app(temp_db_path, temp_config_dir, monkeypatch):
    """Create a TravelbragApp instance for testing (not started)."""
    # Set environment to use toga-dummy backend
    monkeypatch.setenv("TOGA_BACKEND", "toga_dummy")

    app = TravelbragApp("Travelbrag Test", "org.travelbrag.test")
    yield app

    # Cleanup
    if hasattr(app, 'db'):
        app.db.close()


def test_app_creation(app):
    """Test that the app can be created."""
    assert app is not None
    assert app.formal_name == "Travelbrag Test"
    assert app.app_id == "org.travelbrag.test"


def test_app_startup(app, temp_db_path, monkeypatch):
    """Test that app startup initializes all components."""
    # Mock config to use temporary paths
    with patch("travelbrag.app.Config") as mock_config_class:
        mock_config = Mock()
        mock_config.database_path = temp_db_path
        mock_config.data_dir = temp_db_path.parent  # Add data_dir for backup path
        mock_config.load.return_value = None
        mock_config_class.return_value = mock_config

        app.startup()

        # Verify config was loaded
        assert hasattr(app, 'config')
        app.config.load.assert_called_once()

        # Verify database was created
        assert hasattr(app, 'db')

        # Verify repository was created
        assert hasattr(app, 'repo')

        # Verify main window was created
        assert hasattr(app, 'main_window')
        assert hasattr(app, 'main_window_view')
        assert app.main_window.title == "Travelbrag Test"


def test_app_shutdown(app, temp_db_path, monkeypatch):
    """Test that app shutdown closes database properly."""
    # Mock config to use temporary paths
    with patch("travelbrag.app.Config") as mock_config_class:
        mock_config = Mock()
        mock_config.database_path = temp_db_path
        mock_config.data_dir = temp_db_path.parent  # Add data_dir for backup path
        mock_config.colours = {}  # Add colours for GeoJSON export
        mock_config.load.return_value = None
        mock_config_class.return_value = mock_config

        app.startup()

        # Mock the db.close method
        app.db.close = Mock()

        result = app.shutdown()

        assert result is True
        app.db.close.assert_called_once()

        # Verify GeoJSON file was created in site/ directory
        site_dir = Path(__file__).parent.parent / "site"
        geojson_path = site_dir / "travelogue.geojson"
        assert geojson_path.exists()


def test_app_shutdown_without_db():
    """Test that shutdown works even if db wasn't initialized."""
    os.environ["TOGA_BACKEND"] = "toga_dummy"
    app = TravelbragApp("Test", "org.test")

    # Don't call startup, so db is never created
    result = app.shutdown()

    assert result is True


def test_app_shutdown_shows_notification_when_modified(app, temp_db_path, monkeypatch, capsys):
    """Test that shutdown shows notification when database was modified."""
    # Mock config to use temporary paths
    with patch("travelbrag.app.Config") as mock_config_class:
        mock_config = Mock()
        mock_config.database_path = temp_db_path
        mock_config.data_dir = temp_db_path.parent
        mock_config.colours = {}
        mock_config.backup = None
        mock_config.load.return_value = None
        mock_config_class.return_value = mock_config

        app.startup()

        # Mark database as modified
        app.db.mark_modified()

        result = app.shutdown()

        assert result is True

        # Check that notification was printed
        captured = capsys.readouterr()
        assert "⚠️ Back up travelogue.sqlite3 at:" in captured.out


def test_app_shutdown_no_notification_when_not_modified(app, temp_db_path, monkeypatch, capsys):
    """Test that shutdown doesn't show notification when database wasn't modified."""
    # Mock config to use temporary paths
    with patch("travelbrag.app.Config") as mock_config_class:
        mock_config = Mock()
        mock_config.database_path = temp_db_path
        mock_config.data_dir = temp_db_path.parent
        mock_config.colours = {}
        mock_config.load.return_value = None
        mock_config_class.return_value = mock_config

        app.startup()

        # Don't mark database as modified

        result = app.shutdown()

        assert result is True

        # Check that notification was NOT printed
        captured = capsys.readouterr()
        assert "⚠️ Back up travelogue.sqlite3" not in captured.out


def test_app_notification_includes_backup_url(app, temp_db_path, monkeypatch, capsys):
    """Test that notification includes backup URL when configured."""
    # Mock config to use temporary paths
    with patch("travelbrag.app.Config") as mock_config_class:
        mock_config = Mock()
        mock_config.database_path = temp_db_path
        mock_config.data_dir = temp_db_path.parent
        mock_config.colours = {}
        mock_config.backup = "https://example.com/backup"
        mock_config.load.return_value = None
        mock_config_class.return_value = mock_config

        app.startup()

        # Mark database as modified
        app.db.mark_modified()

        result = app.shutdown()

        assert result is True

        # Check that notification includes backup URL
        captured = capsys.readouterr()
        assert "⚠️ Back up travelogue.sqlite3 at:" in captured.out
        assert "🔗 Backup URL: https://example.com/backup" in captured.out

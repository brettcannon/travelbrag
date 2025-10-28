"""Tests for configuration module."""

import pytest
import tempfile
import os
from pathlib import Path

from travelbrag.config import Config


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set XDG_CONFIG_HOME to temp directory
        old_config_home = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = tmpdir

        yield tmpdir

        # Restore original XDG_CONFIG_HOME
        if old_config_home:
            os.environ["XDG_CONFIG_HOME"] = old_config_home
        else:
            del os.environ["XDG_CONFIG_HOME"]


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set XDG_DATA_HOME to temp directory
        old_data_home = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = tmpdir

        yield tmpdir

        # Restore original XDG_DATA_HOME
        if old_data_home:
            os.environ["XDG_DATA_HOME"] = old_data_home
        else:
            del os.environ["XDG_DATA_HOME"]


def test_config_path_uses_xdg(temp_config_dir):
    """Test that config path uses XDG_CONFIG_HOME."""
    config = Config()
    config_path = config.config_path

    assert str(config_path).startswith(temp_config_dir)
    assert config_path.name == "travelbrag.toml"
    assert config_path.parent.name == "travelbrag"


def test_load_creates_default_config(temp_config_dir):
    """Test that load creates default config if it doesn't exist."""
    config = Config()
    data = config.load()

    assert "geonames" in data
    assert "username" in data["geonames"]
    assert data["geonames"]["username"] == ""

    # Check file was created
    assert config.config_path.exists()


def test_load_existing_config(temp_config_dir):
    """Test loading existing config file."""
    config = Config()

    # Create config with custom values
    config._data = {
        "geonames": {
            "username": "test_user"
        }
    }
    config.save()

    # Create new config instance and load
    config2 = Config()
    data = config2.load()

    assert data["geonames"]["username"] == "test_user"


def test_geonames_username_property(temp_config_dir):
    """Test geonames_username property."""
    config = Config()
    config.load()

    assert config.geonames_username == ""

    config.geonames_username = "my_username"
    assert config.geonames_username == "my_username"

    # Verify it was saved
    config2 = Config()
    config2.load()
    assert config2.geonames_username == "my_username"


def test_data_dir_uses_xdg(temp_data_dir):
    """Test that data dir uses XDG_DATA_HOME."""
    config = Config()
    data_dir = config.data_dir

    # Should use XDG_DATA_HOME
    assert str(data_dir).startswith(temp_data_dir)
    assert data_dir.name == "travelbrag"
    assert data_dir.exists()
    assert data_dir.is_dir()


def test_database_path(temp_data_dir):
    """Test database path uses XDG data directory."""
    config = Config()
    db_path = config.database_path

    # Database should be at XDG_DATA_HOME/travelbrag/travelogue.sqlite3
    assert db_path.name == "travelogue.sqlite3"
    assert db_path.parent == config.data_dir
    assert str(db_path.parent).startswith(temp_data_dir)


def test_config_directory_created(temp_config_dir):
    """Test that config directory is created."""
    config = Config()

    # Access property to trigger directory creation
    _ = config.config_path

    config_dir = Path(temp_config_dir) / "travelbrag"

    assert config_dir.exists()
    assert config_dir.is_dir()


def test_backup_url_property(temp_config_dir):
    """Test backup URL property."""
    config = Config()
    config.load()

    # Should return None when not set
    assert config.backup is None

    # Set backup URL
    config._data["backup"] = "https://example.com/backup"
    config.save()

    # Verify it was saved
    config2 = Config()
    config2.load()
    assert config2.backup == "https://example.com/backup"


def test_backup_url_not_set(temp_config_dir):
    """Test backup URL when not configured."""
    config = Config()
    config.load()

    assert config.backup is None

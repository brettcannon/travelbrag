"""Tests for database module."""

import pytest
import tempfile
import time
from pathlib import Path

from travelbrag.database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        yield db
        db.close()


@pytest.fixture
def schema_path():
    """Get path to schema.sql file."""
    return Path(__file__).parent.parent / "schema.sql"


def test_database_connection(temp_db):
    """Test database connection is created."""
    assert temp_db.connection is not None
    assert temp_db._conn is not None


def test_database_foreign_keys_enabled(temp_db):
    """Test that foreign keys are enabled."""
    cursor = temp_db.connection.execute("PRAGMA foreign_keys")
    result = cursor.fetchone()
    assert result[0] == 1


def test_initialize_schema(temp_db, schema_path):
    """Test schema initialization."""
    temp_db.initialize_schema(schema_path)

    # Check that tables were created
    cursor = temp_db.connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {"cities", "people", "trips", "trip_participants", "trip_cities"}
    assert expected_tables.issubset(tables)


def test_database_context_manager(schema_path):
    """Test database as context manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        with Database(db_path) as db:
            db.initialize_schema(schema_path)
            assert db.connection is not None

        # Connection should be closed after context
        assert db._conn is None


def test_database_close(temp_db):
    """Test database close."""
    # Access connection to create it
    _ = temp_db.connection
    assert temp_db._conn is not None

    temp_db.close()
    assert temp_db._conn is None


def test_wal_mode_enabled(temp_db):
    """Test that WAL mode is enabled."""
    cursor = temp_db.connection.execute("PRAGMA journal_mode")
    result = cursor.fetchone()
    assert result[0].lower() == "wal"


def test_synchronous_full(temp_db):
    """Test that synchronous mode is set to FULL."""
    cursor = temp_db.connection.execute("PRAGMA synchronous")
    result = cursor.fetchone()
    # FULL = 2 in SQLite
    assert result[0] == 2


def test_integrity_check_healthy(temp_db, schema_path):
    """Test integrity check on healthy database."""
    temp_db.initialize_schema(schema_path)
    is_ok, message = temp_db.check_integrity()
    assert is_ok is True
    assert "passed" in message.lower()


def test_backup_creation(temp_db, schema_path):
    """Test database backup creation."""
    # Initialize schema and add some data
    temp_db.initialize_schema(schema_path)
    temp_db.connection.execute("INSERT INTO people (name) VALUES ('Test Person')")
    temp_db.connection.commit()

    # Create backup
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_path = Path(tmpdir) / "backup.db"
        temp_db.backup(backup_path)

        # Verify backup exists and contains data
        assert backup_path.exists()
        backup_db = Database(backup_path)
        cursor = backup_db.connection.execute("SELECT name FROM people WHERE name = 'Test Person'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "Test Person"
        backup_db.close()


def test_backup_creates_directory(temp_db, schema_path):
    """Test that backup creates parent directory if needed."""
    temp_db.initialize_schema(schema_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_path = Path(tmpdir) / "backups" / "nested" / "backup.db"
        temp_db.backup(backup_path)

        assert backup_path.exists()
        assert backup_path.parent.exists()


def test_timestamped_backup_creation(temp_db, schema_path):
    """Test creating a timestamped backup."""
    temp_db.initialize_schema(schema_path)
    temp_db.connection.execute("INSERT INTO people (name) VALUES ('Test Person')")
    temp_db.connection.commit()

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = Path(tmpdir)
        backup_path = temp_db.create_timestamped_backup(backup_dir, max_backups=5)

        # Verify backup was created with correct naming pattern
        assert backup_path.exists()
        assert backup_path.name.startswith("travelogue_")
        assert backup_path.name.endswith(".sqlite3")

        # Verify backup contains data
        backup_db = Database(backup_path)
        cursor = backup_db.connection.execute("SELECT name FROM people WHERE name = 'Test Person'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "Test Person"
        backup_db.close()


def test_backup_rotation_keeps_max_backups(temp_db, schema_path):
    """Test that backup rotation keeps only max_backups files."""
    temp_db.initialize_schema(schema_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = Path(tmpdir)

        # Create 8 backups with max_backups=5
        for i in range(8):
            temp_db.create_timestamped_backup(backup_dir, max_backups=5)
            # Small delay to ensure different timestamps
            time.sleep(0.01)

        # Should only have 5 backups
        backups = list(backup_dir.glob("travelogue_*.sqlite3"))
        assert len(backups) == 5


def test_get_available_backups_sorted(temp_db, schema_path):
    """Test that get_available_backups returns backups sorted by time (newest first)."""
    temp_db.initialize_schema(schema_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = Path(tmpdir)

        # Create multiple backups
        created_backups = []
        for i in range(3):
            backup_path = temp_db.create_timestamped_backup(backup_dir, max_backups=5)
            created_backups.append(backup_path)
            time.sleep(0.01)

        # Get available backups
        available = temp_db.get_available_backups(backup_dir)

        # Should be sorted newest first (reverse of creation order)
        assert len(available) == 3
        assert available[0] == created_backups[2]  # Newest
        assert available[2] == created_backups[0]  # Oldest


def test_get_available_backups_empty_directory(temp_db):
    """Test get_available_backups with non-existent directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = Path(tmpdir) / "nonexistent"
        available = temp_db.get_available_backups(backup_dir)
        assert available == []


def test_backup_rotation_preserves_newest(temp_db, schema_path):
    """Test that backup rotation preserves the newest backups."""
    temp_db.initialize_schema(schema_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = Path(tmpdir)

        # Create backups with identifiable data
        created_backups = []
        for i in range(7):
            temp_db.connection.execute(f"INSERT INTO people (name) VALUES ('Person_{i}')")
            temp_db.connection.commit()
            backup_path = temp_db.create_timestamped_backup(backup_dir, max_backups=5)
            created_backups.append(backup_path)
            time.sleep(0.01)

        # Only the last 5 should exist
        for i, backup_path in enumerate(created_backups):
            if i < 2:  # First 2 should be deleted
                assert not backup_path.exists()
            else:  # Last 5 should exist
                assert backup_path.exists()


def test_modification_tracking(temp_db):
    """Test database modification tracking."""
    # Initially not modified
    assert temp_db.was_modified is False

    # Mark as modified
    temp_db.mark_modified()
    assert temp_db.was_modified is True


def test_modification_flag_persists_across_connection(temp_db):
    """Test that modification flag persists even if connection is accessed."""
    assert temp_db.was_modified is False

    # Access connection (shouldn't affect modification flag)
    _ = temp_db.connection
    assert temp_db.was_modified is False

    # Mark as modified
    temp_db.mark_modified()
    assert temp_db.was_modified is True

    # Still modified after more operations
    _ = temp_db.connection
    assert temp_db.was_modified is True

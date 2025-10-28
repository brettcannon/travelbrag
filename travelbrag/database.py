"""Database connection and initialization for Travelbrag."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class Database:
    """Manages SQLite database connection and schema initialization."""

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._modified = False

    @property
    def connection(self) -> sqlite3.Connection:
        """Get database connection, creating it if needed."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            # Enable foreign key constraints
            self._conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better crash resistance
            self._conn.execute("PRAGMA journal_mode = WAL")
            # Set full synchronous mode for maximum durability
            self._conn.execute("PRAGMA synchronous = FULL")
        return self._conn

    def initialize_schema(self, schema_path: Path) -> None:
        """Initialize database schema from SQL file.

        Args:
            schema_path: Path to schema.sql file
        """
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Split by statement and filter out comments and empty statements
        statements = []
        current_statement = []

        for line in schema_sql.split('\n'):
            # Skip pure comment lines
            if line.strip().startswith('--'):
                continue
            current_statement.append(line)
            # Execute when we hit a semicolon
            if ';' in line:
                stmt = '\n'.join(current_statement)
                if stmt.strip() and not stmt.strip().startswith('--'):
                    statements.append(stmt)
                current_statement = []

        # Execute all statements
        with self.connection:
            for stmt in statements:
                self.connection.execute(stmt)

    def check_integrity(self) -> tuple[bool, str]:
        """Check database integrity.

        Returns:
            Tuple of (is_ok, message) where is_ok is True if integrity check passed
        """
        try:
            cursor = self.connection.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            if result == "ok":
                return (True, "Database integrity check passed")
            else:
                return (False, f"Database integrity check failed: {result}")
        except Exception as e:
            return (False, f"Error running integrity check: {e}")

    def backup(self, backup_path: Path) -> None:
        """Create a backup of the database.

        Args:
            backup_path: Path where backup should be saved
        """
        # Create backup directory if needed
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Use SQLite's backup API
        backup_conn = sqlite3.connect(backup_path)
        try:
            with backup_conn:
                self.connection.backup(backup_conn)
        finally:
            backup_conn.close()

    def create_timestamped_backup(self, backup_dir: Path, max_backups: int = 5) -> Path:
        """Create a timestamped backup and manage rotation.

        Args:
            backup_dir: Directory where backups should be stored
            max_backups: Maximum number of backups to keep (default: 5)

        Returns:
            Path to the created backup file
        """
        # Create backup directory if needed
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped backup filename with microseconds for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_path = backup_dir / f"travelogue_{timestamp}.sqlite3"

        # Create the backup
        self.backup(backup_path)

        # Cleanup old backups
        self._rotate_backups(backup_dir, max_backups)

        return backup_path

    def _rotate_backups(self, backup_dir: Path, max_backups: int) -> None:
        """Remove old backups, keeping only the most recent ones.

        Args:
            backup_dir: Directory containing backups
            max_backups: Maximum number of backups to keep
        """
        # Get all backup files sorted by modification time (newest first)
        backups = sorted(
            backup_dir.glob("travelogue_*.sqlite3"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Remove backups beyond the limit
        for old_backup in backups[max_backups:]:
            old_backup.unlink()

    def get_available_backups(self, backup_dir: Path) -> list[Path]:
        """Get list of available backups sorted by timestamp (newest first).

        Args:
            backup_dir: Directory containing backups

        Returns:
            List of backup file paths
        """
        if not backup_dir.exists():
            return []

        return sorted(
            backup_dir.glob("travelogue_*.sqlite3"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

    def mark_modified(self) -> None:
        """Mark the database as having been modified during this session."""
        self._modified = True

    @property
    def was_modified(self) -> bool:
        """Check if the database was modified during this session."""
        return self._modified

    def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            # Checkpoint WAL to ensure all changes are written to main database
            self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

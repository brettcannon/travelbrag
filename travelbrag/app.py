"""Main Travelbrag application entry point."""

import atexit
import shutil
import toga
from toga.style import Pack
from pathlib import Path

from .config import Config
from .database import Database
from .repository import Repository
from .gui.main_window import MainWindow
from .geojson_export import export_geojson


class TravelbragApp(toga.App):
    """Main Travelbrag application."""

    def startup(self):
        """Initialize and start the application."""
        # Load configuration
        self.config = Config()
        self.config.load()
        print(f"Configuration loaded from: {self.config.config_path}")

        # Initialize database
        schema_path = Path(__file__).parent.parent / "schema.sql"
        self.db = Database(self.config.database_path)

        # Initialize schema if database is new
        if not self.config.database_path.exists() or self.config.database_path.stat().st_size == 0:
            self.db.initialize_schema(schema_path)

        # Check database integrity on startup
        backup_dir = self.config.data_dir / "backups"
        is_ok, message = self.db.check_integrity()
        if not is_ok:
            print(f"🚨 {message}")
            # If integrity check fails, attempt to restore from backups (newest first)
            available_backups = self.db.get_available_backups(backup_dir)
            restored = False

            for backup_path in available_backups:
                print(f"Attempting to restore from backup: {backup_path}")
                try:
                    # Close current connection before overwriting
                    self.db.close()
                    shutil.copy(backup_path, self.config.database_path)

                    # Re-check integrity
                    is_ok, message = self.db.check_integrity()
                    if not is_ok:
                        print(f"🚨 After restore: {message}")

                    if is_ok:
                        restored = True
                        print(f"Successfully restored from {backup_path.name}")
                        break
                except Exception as e:
                    print(f"Failed to restore from {backup_path.name}: {e}")

            if not restored and available_backups:
                print("🚨 Could not restore from any available backup")
            elif not available_backups:
                print("🚨 No backups available to restore from")

        # Create backup on startup only if database is healthy
        if is_ok:
            try:
                backup_path = self.db.create_timestamped_backup(backup_dir, max_backups=5)
                print(f"Database backup created: {backup_path.name}")
            except Exception as e:
                print(f"Warning: Could not create backup: {e}")
        else:
            print("🚨 Skipping backup creation due to database integrity issues")

        # Create repository
        self.repo = Repository(self.db)

        # Register cleanup functions (atexit runs in LIFO order)
        # Database close must be first (executed last) so other handlers can still use it
        atexit.register(self._close_database_on_exit)
        atexit.register(self._show_database_modified_notification_on_exit)
        atexit.register(self._export_geojson_on_exit)

        # Create main window
        self.main_window_view = MainWindow(self, self.config, self.db, self.repo)

        # Set main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_window_view.container
        self.main_window.size = (1200, 800)
        self.main_window.show()

    def _export_geojson_on_exit(self):
        """Export GeoJSON data. Called on exit via atexit."""
        try:
            if hasattr(self, 'db') and hasattr(self, 'config'):
                # Export to site/ directory (repository root / site / travelogue.geojson)
                site_dir = Path(__file__).parent.parent / "site"
                if site_dir.exists():
                    geojson_path = site_dir / "travelogue.geojson"
                    colours = self.config.colours if hasattr(self.config, 'colours') else {}
                    export_geojson(self.db, geojson_path, colours)
                    print(f"GeoJSON file updated: {geojson_path}")
        except (OSError, TypeError, AttributeError):
            # Silently ignore errors during shutdown/cleanup
            # (e.g., temp directories already deleted, mocked objects in tests)
            pass
        except Exception as e:
            # Print unexpected errors but don't prevent shutdown
            print(f"Error exporting GeoJSON on exit: {e}")

    def shutdown(self):
        """Clean up resources on shutdown."""
        try:
            # Export GeoJSON before closing database
            self._export_geojson_on_exit()
        except Exception as e:
            print(f"Error in shutdown: {e}")

        # Show database modification notification
        self._show_database_modified_notification_on_exit()

        if hasattr(self, 'db'):
            self.db.close()
        return True

    def _close_database_on_exit(self):
        """Close database connection. Called on exit via atexit."""
        try:
            if hasattr(self, 'db'):
                self.db.close()
        except Exception as e:
            # Print unexpected errors but don't prevent shutdown
            print(f"Error closing database on exit: {e}")

    def _show_database_modified_notification_on_exit(self):
        """Show notification when database was modified. Called on exit via atexit."""
        try:
            if hasattr(self, 'db') and hasattr(self, 'config') and self.db.was_modified:
                # Build message with clickable path
                message = f"⚠️ Back up travelogue.sqlite3 at: {self.config.data_dir}"

                # Add backup URL if configured
                backup_url = self.config.backup
                if backup_url:
                    message += f"\n🔗 Backup URL: {backup_url}"

                print(message)
        except (OSError, AttributeError):
            # Silently ignore errors during shutdown/cleanup
            pass
        except Exception as e:
            # Print unexpected errors but don't prevent shutdown
            print(f"Error showing database notification on exit: {e}")


def main():
    """Main entry point for the application."""
    app = TravelbragApp(
        "Travelbrag",
        "org.travelbrag.app"
    )
    app.main_loop()


if __name__ == "__main__":
    app = main()
    app.main_loop()

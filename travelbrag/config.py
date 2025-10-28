"""Configuration management for Travelbrag using XDG Base Directory Specification."""

import os
import sys
from pathlib import Path
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w


class Config:
    """Manages application configuration stored in TOML format."""

    CONFIG_FILENAME = "travelbrag.toml"
    DEFAULT_CONFIG = {
        "geonames": {
            "username": ""
        }
    }

    def __init__(self):
        """Initialize configuration manager."""
        self._config_path: Optional[Path] = None
        self._data: dict = {}

    @property
    def config_path(self) -> Path:
        """Get configuration file path using XDG Base Directory Specification."""
        if self._config_path is None:
            # Get XDG_CONFIG_HOME or default to ~/.config
            config_home = os.environ.get("XDG_CONFIG_HOME")
            if config_home:
                base_path = Path(config_home)
            else:
                base_path = Path.home() / ".config"

            # Create travelbrag config directory if needed
            config_dir = base_path / "travelbrag"
            config_dir.mkdir(parents=True, exist_ok=True)

            self._config_path = config_dir / self.CONFIG_FILENAME

        return self._config_path

    def load(self) -> dict:
        """Load configuration from file.

        Returns:
            Configuration dictionary
        """
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                self._data = tomllib.load(f)
        else:
            # Create default config file
            self._data = self.DEFAULT_CONFIG.copy()
            self.save()

        return self._data

    def save(self) -> None:
        """Save current configuration to file."""
        with open(self.config_path, "wb") as f:
            tomli_w.dump(self._data, f)

    @property
    def geonames_username(self) -> str:
        """Get GeoNames username from config."""
        if not self._data:
            self.load()
        return self._data.get("geonames", {}).get("username", "")

    @geonames_username.setter
    def geonames_username(self, username: str) -> None:
        """Set GeoNames username in config.

        Args:
            username: GeoNames username
        """
        if not self._data:
            self.load()
        if "geonames" not in self._data:
            self._data["geonames"] = {}
        self._data["geonames"]["username"] = username
        self.save()

    @property
    def data_dir(self) -> Path:
        """Get data directory for database using XDG Base Directory Specification."""
        # Get XDG_DATA_HOME or default to ~/.local/share
        data_home = os.environ.get("XDG_DATA_HOME")
        if data_home:
            base_path = Path(data_home)
        else:
            base_path = Path.home() / ".local" / "share"

        # Create travelbrag data directory if needed
        data_dir = base_path / "travelbrag"
        data_dir.mkdir(parents=True, exist_ok=True)

        return data_dir

    @property
    def database_path(self) -> Path:
        """Get path to SQLite database file."""
        return self.data_dir / "travelogue.sqlite3"

    @property
    def colours(self) -> dict[str, list[str]]:
        """Get colours mapping from config.

        Returns:
            Dictionary mapping hex color codes (without #) to lists of traveler names
        """
        if not self._data:
            self.load()
        return self._data.get("colours", {})

    @property
    def home(self) -> Optional[str]:
        """Get home country from config.

        Returns:
            ISO 3166-1 alpha-2 country code (e.g., "CA", "US") or None if not set
        """
        if not self._data:
            self.load()
        return self._data.get("home")

    @property
    def backup(self) -> Optional[str]:
        """Get backup URL from config.

        Returns:
            URL to open when database is modified, or None if not set
        """
        if not self._data:
            self.load()
        return self._data.get("backup")

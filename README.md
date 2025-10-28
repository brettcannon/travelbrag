# Travelbrag

A GUI application to record trips taken by family members and track which cities were visited on each trip.

## Features

- **Manage Family Members**: Add, edit, and remove people who take trips
- **Track Trips**: Record trips with names, dates, notes, and participants
- **City Tracking**: Add cities visited on each trip using GeoNames geocoding
- **Interactive Maps**: View cities on maps using Toga's MapView widget
- **Multiple Views**:
  - All trips overview with map of all visited cities
  - Individual person view showing their trips and cities
  - Individual trip detail view with participants and cities
  - Statistics view with travel insights
- **Smart City Search**: Filter cities by country and state/province for accurate selection
- **Travel Statistics**: View comprehensive statistics including:
  - Last domestic and international trips
  - Most visited cities
  - Longest trips per person (domestic and international)
  - Longest time away from home in a year per traveler
  - Countries visited in the last 5 years per traveler
  - Canadian provinces and territories visited (when home country is Canada)
- **GeoJSON Export**: Automatically exports visited cities as GeoJSON on app exit for use with mapping tools

## Tech Stack

- **Language**: Python 3.10+
- **GUI Framework**: [Toga](https://toga.readthedocs.io/)
- **Database**: SQLite
- **Geocoding**: [GeoNames](https://www.geonames.org) web services
- **Configuration**: TOML files following XDG Base Directory Specification
- **Testing**: Pytest

## Installation

1. Clone the repository:
```bash
git clone https://github.com/brettcannon/travelbrag.git
cd travelbrag
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
```

3. Get a GeoNames username:
   - Register for free at https://www.geonames.org/login
   - Enable web services in your account settings

4. Run the application:
```bash
travelbrag
```

5. On first run, configure your GeoNames username in the settings

## Configuration

Configuration is stored in `travelbrag.toml` following the XDG Base Directory Specification:
- Linux: `~/.config/travelbrag/travelbrag.toml`
- macOS: `~/Library/Application Support/travelbrag/travelbrag.toml`
- Windows: `%APPDATA%\travelbrag\travelbrag.toml`

### Configuration File Format

The configuration file uses TOML format and supports the following settings:

```toml
home = "CA"
backup = "https://example.com/backup"

[geonames]
username = "your_geonames_username"

[colours]
"005CFA" = ["Brett"]
"F2FA00" = ["Gidget"]
"00FA21" = ["Brett", "Gidget"]
```

**Available Settings:**
- `home` (string): Optional ISO 3166-1 alpha-2 country code (e.g., "CA", "US", "GB") for your home country. Used to differentiate domestic vs international trips in statistics. If not set, all trips are treated as international.
- `backup` (string): Optional URL that will be displayed on application exit when the database has been modified. Useful for reminding you to back up your data to cloud storage or other backup services.
- `geonames.username` (string): Your GeoNames web services username. Required for geocoding city searches. Get one free at https://www.geonames.org/login
- `colours` (table): Optional mapping of hex color codes (without #) to arrays of traveler names. Used to color-code cities in the exported GeoJSON based on which travelers have visited. The set of travelers for a city must exactly match one of the configured arrays to get a marker color.

The configuration file is created automatically on first run with default values. You can edit it manually or configure settings through the application's settings interface.

### Data Storage

The SQLite database is stored following the XDG Base Directory Specification:
- Linux: `~/.local/share/travelbrag/travelogue.sqlite3`
- macOS: `~/Library/Application Support/travelbrag/travelogue.sqlite3`
- Windows: `%APPDATA%\travelbrag\travelogue.sqlite3`

A GeoJSON file (`travelogue.geojson`) is automatically generated in the `site/` directory in the repository root whenever you exit the application. This file contains all visited cities with their coordinates, visit counts, last visit year, and color-coded markers based on which travelers have visited each city (configured in `travelbrag.toml`). This makes it easy to visualize your travels using tools like:
- [Mapbox](https://www.mapbox.com/)
- [Leaflet](https://leafletjs.com/)
- [QGIS](https://qgis.org/)
- [geojson.io](https://geojson.io/)
- Any other GeoJSON-compatible mapping platform

The `marker-color` property follows the [simplestyle-spec](https://github.com/mapbox/simplestyle-spec) convention for styling GeoJSON features.

## Development

### Running Tests

```bash
pytest
```

### Project Structure

```
travelbrag/
├── travelbrag/           # Application code
│   ├── gui/             # GUI components
│   ├── app.py           # Main application entry point
│   ├── config.py        # Configuration management
│   ├── database.py      # Database connection
│   ├── date_parser.py   # Date validation and duration calculation
│   ├── geonames.py      # GeoNames API client
│   ├── geojson_export.py # GeoJSON export functionality
│   ├── models.py        # Data models
│   ├── repository.py    # Database operations
│   └── statistics.py    # Travel statistics calculations
├── tests/               # Test files
├── schema.sql           # Database schema
└── pyproject.toml       # Project configuration
```

## Database Schema

The application uses a normalized SQLite database with tables for:
- `people`: Family members
- `trips`: Trip details (name, dates, notes)
- `cities`: City information from GeoNames
- `trip_participants`: Many-to-many relationship between trips and people
- `trip_cities`: Many-to-many relationship between trips and cities

See [schema.sql](schema.sql) for the complete schema.

## License

MIT License - see [LICENSE](LICENSE) file for details.

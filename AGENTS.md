# Travelbrag

A GUI application for tracking family trips and cities visited. Users manage family members and trips through a Toga-based interface with integrated maps.

## Tech Stack

**Language**: Python
**Database**: SQLite (schema in `schema.sql`, stored in XDG data directory `~/.local/share/travelbrag/`)
**GUI**: [Toga](https://toga.readthedocs.io/) with MapView for maps
**External API**: [GeoNames](https://www.geonames.org/export/web-services.html) for city geocoding
**Config**: TOML files (XDG-compliant paths)
**Testing**: pytest with toga-dummy backend

## Critical Technical Constraints

### Toga API (Your Knowledge is Outdated!)

**Always consult the [API reference](https://toga.readthedocs.io/en/stable/reference/api/index.html)** when working with widgets. Must work on Gtk backend.

**Use margin, not padding**:
```python
Pack(margin=10)  # ✓ correct
Pack(margin=(10, 0, 0, 0))  # ✓ correct
Pack(padding=10)  # ✗ deprecated
```

**Dialog API pattern**:
```python
await window.info_dialog(title, message)  # ✓ current usage
await window.dialog(toga.ConfirmDialog(...))  # ✓ for confirm dialogs
```

**Async event handlers**:
- Toga handles async handlers automatically - no `asyncio.create_task()` wrapping needed
- Functions declared `async` MUST contain `await` statements; if not, make them sync

**Table event handlers** receive 3 parameters:
```python
async def handler(self, widget, row=None, **kwargs)
```

### Database

**Countries**: Stored as ISO 3166-1 alpha-2 codes ("US", "GB", "FR") with CHECK constraint. Convert to full names for display only.

**Dates**: Stored as TEXT in ISO format (YYYY-MM-DD or YYYY-MM) to preserve precision. When only year-month is known, store as YYYY-MM rather than converting to YYYY-MM-01.

**Performance indices** exist on: geonameid, country, start_date, junction table IDs

**Data integrity**: Foreign key constraints with CASCADE deletes; orphaned cities cleaned up automatically

**WAL mode**: Database uses WAL (Write-Ahead Logging) journal mode with FULL synchronous mode for maximum durability and crash resistance

**Automatic backups**:
- Timestamped backup created on every app startup (if DB is healthy)
- Backups stored in `~/.local/share/travelbrag/backups/` (or platform equivalent)
- Automatic rotation keeps 5 most recent backups
- Database integrity check on startup with automatic restoration from backup if corruption detected
- Database modification tracking with optional backup URL notification (configured via `backup` setting in config)

### Testing

**Do NOT run the app** (`python -m travelbrag`) - it's a GUI and will hang. Use pytest with toga-dummy instead.

**Always add tests** when fixing bugs.

## Architecture

Layered design:
- `models.py` - Data classes (Person, Trip, City). Trip dates are strings in ISO format.
- `database.py` - SQLite connection & schema init
- `repository.py` - CRUD operations
- `geonames.py` - API client
- `config.py` - TOML config (GeoNames username, home country)
- `date_parser.py` - Date validation and duration calculation utilities
- `statistics.py` - Statistics calculations (last trips, longest trips, most visited cities, etc.)
- `geojson_export.py` - GeoJSON export functionality (auto-exports on app exit)
- `gui/` - Toga UI components

## Key Implementation Patterns

**City search**: Two-step filtering (country code → city name) to avoid ambiguity. Previously visited cities auto-populate and filter in real-time; new cities require API search.

**Date handling**: ISO format (YYYY-MM-DD or YYYY-MM) stored as TEXT to preserve precision. Real-time validation on input. End date is required; no duration calculation.

**Participant management**: Inline checkboxes with instant save (no separate dialogs).

**Chronological ordering**: Reverse chronological for trips and cities.

**Map usage**: Reusable component with automatic pin placement and zoom.

**GeoJSON export**: Automatically generates `travelogue.geojson` on app exit using `atexit` (reliable across all shutdown methods). Each city feature includes coordinates, name, visit count, last visit year, and optionally a marker-color based on which travelers have visited. Colors are configured in `travelbrag.toml` under the `[colours]` table, mapping hex colors (without #) to arrays of traveler names. File location is in the `site/` directory (repository root) next to `index.html`.

**Statistics**: Comprehensive travel statistics with per-person filtering. Statistics only include trips from each person's first trip with full date precision (YYYY-MM-DD). Trips with month-only dates (YYYY-MM) are excluded from date-based calculations but included in count-based statistics. Home country is configured in `travelbrag.toml` with the `home` key (ISO 3166-1 alpha-2 code) to differentiate domestic vs international trips.

**Web deployment**: The `site/` directory contains a static HTML/Leaflet-based map viewer (`index.html`) that displays the exported GeoJSON data. Deployment via `just publish` (Netlify). The GeoJSON file is automatically updated on app exit for seamless web visualization.

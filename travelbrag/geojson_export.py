"""GeoJSON export functionality for city visit data."""

import json
from pathlib import Path
from typing import Any, Optional

from .database import Database


def _get_marker_color(visitors: set[str], colours: dict[str, list[str]]) -> Optional[str]:
    """Get marker color for a set of visitors.

    Args:
        visitors: Set of visitor names who have been to the city
        colours: Dictionary mapping hex colors to lists of traveler names

    Returns:
        Hex color string with # prefix, or None if no match found
    """
    for color, travelers in colours.items():
        if set(travelers) == visitors:
            return f"#{color}"
    return None


def generate_geojson(db: Database, colours: Optional[dict[str, list[str]]] = None) -> dict[str, Any]:
    """Generate GeoJSON FeatureCollection from database.

    Args:
        db: Database instance
        colours: Optional dictionary mapping hex colors (without #) to lists of traveler names

    Returns:
        Dictionary containing GeoJSON FeatureCollection with city visit data
    """
    if colours is None:
        colours = {}

    # Query to get all cities with visit count, last visit year, and city ID
    cursor = db.connection.execute("""
        SELECT
            c.id,
            c.name,
            c.latitude,
            c.longitude,
            COUNT(tc.trip_id) as visit_count,
            MAX(SUBSTR(t.end_date, 1, 4)) as last_visit_year
        FROM cities c
        JOIN trip_cities tc ON c.id = tc.city_id
        JOIN trips t ON tc.trip_id = t.id
        GROUP BY c.id
        ORDER BY c.name
    """)

    features = []
    for row in cursor.fetchall():
        row_dict = dict(row)
        city_id = row_dict["id"]

        # Get all people who have visited this city
        people_cursor = db.connection.execute("""
            SELECT DISTINCT p.name
            FROM people p
            JOIN trip_participants tp ON p.id = tp.person_id
            JOIN trip_cities tc ON tp.trip_id = tc.trip_id
            WHERE tc.city_id = ?
            ORDER BY p.name
        """, (city_id,))

        visitors = {row[0] for row in people_cursor.fetchall()}

        # Build properties
        properties = {
            "name": row_dict["name"],
            "visit count": row_dict["visit_count"],
            "last visit": int(row_dict["last_visit_year"])
        }

        # Add marker color if we have a match
        if visitors and colours:
            marker_color = _get_marker_color(visitors, colours)
            if marker_color:
                properties["marker-color"] = marker_color

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    float(row_dict["longitude"]),
                    float(row_dict["latitude"])
                ]
            },
            "properties": properties
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return geojson


def export_geojson(db: Database, output_path: Path, colours: Optional[dict[str, list[str]]] = None) -> None:
    """Export city visit data as GeoJSON file.

    Args:
        db: Database instance
        output_path: Path to write the GeoJSON file
        colours: Optional dictionary mapping hex colors (without #) to lists of traveler names
    """
    geojson = generate_geojson(db, colours)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)

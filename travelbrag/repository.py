"""Repository layer for database CRUD operations."""

from typing import Optional
from .database import Database
from .models import City, Person, Trip, TripCity


class Repository:
    """Handles all database operations for Travelbrag."""

    def __init__(self, database: Database):
        """Initialize repository with database connection.

        Args:
            database: Database instance
        """
        self.db = database

    # City operations
    def get_city_by_id(self, city_id: int) -> Optional[City]:
        """Get city by ID."""
        cursor = self.db.connection.execute(
            "SELECT * FROM cities WHERE id = ?", (city_id,)
        )
        row = cursor.fetchone()
        if row:
            return City(**dict(row))
        return None

    def get_city_by_geonameid(self, geonameid: int) -> Optional[City]:
        """Get city by GeoNames ID."""
        cursor = self.db.connection.execute(
            "SELECT * FROM cities WHERE geonameid = ?", (geonameid,)
        )
        row = cursor.fetchone()
        if row:
            return City(**dict(row))
        return None

    def add_city(self, city: City) -> City:
        """Add a new city to the database.

        Args:
            city: City object to add

        Returns:
            City object with assigned ID
        """
        cursor = self.db.connection.execute(
            """INSERT INTO cities (geonameid, name, admin_division, country, latitude, longitude)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (city.geonameid, city.name, city.admin_division, city.country,
             city.latitude, city.longitude)
        )
        self.db.connection.commit()
        self.db.mark_modified()
        city.id = cursor.lastrowid
        return city

    def get_or_create_city(self, city: City) -> City:
        """Get existing city or create new one.

        Args:
            city: City object

        Returns:
            City object with ID from database
        """
        # Try to find existing city by geonameid
        existing = self.get_city_by_geonameid(city.geonameid)
        if existing:
            return existing

        # Create new city
        return self.add_city(city)

    def get_all_cities(self) -> list[City]:
        """Get all cities in the database."""
        cursor = self.db.connection.execute("SELECT * FROM cities ORDER BY name")
        return [City(**dict(row)) for row in cursor.fetchall()]

    # Person operations
    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        """Get person by ID."""
        cursor = self.db.connection.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        )
        row = cursor.fetchone()
        if row:
            return Person(**dict(row))
        return None

    def get_person_by_name(self, name: str) -> Optional[Person]:
        """Get person by name."""
        cursor = self.db.connection.execute(
            "SELECT * FROM people WHERE name = ?", (name,)
        )
        row = cursor.fetchone()
        if row:
            return Person(**dict(row))
        return None

    def add_person(self, person: Person) -> Person:
        """Add a new person.

        Args:
            person: Person object

        Returns:
            Person with assigned ID
        """
        cursor = self.db.connection.execute(
            "INSERT INTO people (name) VALUES (?)", (person.name,)
        )
        self.db.connection.commit()
        self.db.mark_modified()
        person.id = cursor.lastrowid
        return person

    def update_person(self, person: Person) -> None:
        """Update person name.

        Args:
            person: Person object with ID and new name
        """
        self.db.connection.execute(
            "UPDATE people SET name = ? WHERE id = ?",
            (person.name, person.id)
        )
        self.db.connection.commit()
        self.db.mark_modified()

    def delete_person(self, person_id: int) -> None:
        """Delete person by ID.

        Args:
            person_id: Person ID to delete
        """
        self.db.connection.execute("DELETE FROM people WHERE id = ?", (person_id,))
        self.db.connection.commit()
        self.db.mark_modified()

    def get_all_people(self) -> list[Person]:
        """Get all people."""
        cursor = self.db.connection.execute("SELECT * FROM people ORDER BY name")
        return [Person(**dict(row)) for row in cursor.fetchall()]

    # Trip operations
    def get_trip_by_id(self, trip_id: int) -> Optional[Trip]:
        """Get trip by ID."""
        cursor = self.db.connection.execute(
            "SELECT * FROM trips WHERE id = ?", (trip_id,)
        )
        row = cursor.fetchone()
        if row:
            return Trip(**dict(row))
        return None

    def add_trip(self, trip: Trip) -> Trip:
        """Add a new trip.

        Args:
            trip: Trip object

        Returns:
            Trip with assigned ID
        """
        cursor = self.db.connection.execute(
            """INSERT INTO trips (name, notes, start_date, end_date)
               VALUES (?, ?, ?, ?)""",
            (trip.name, trip.notes, trip.start_date, trip.end_date)
        )
        self.db.connection.commit()
        self.db.mark_modified()
        trip.id = cursor.lastrowid
        return trip

    def update_trip(self, trip: Trip) -> None:
        """Update trip details.

        Args:
            trip: Trip object with ID and updated fields
        """
        self.db.connection.execute(
            """UPDATE trips SET name = ?, notes = ?, start_date = ?, end_date = ?
               WHERE id = ?""",
            (trip.name, trip.notes, trip.start_date, trip.end_date, trip.id)
        )
        self.db.connection.commit()
        self.db.mark_modified()

    def delete_trip(self, trip_id: int) -> None:
        """Delete trip by ID.

        Args:
            trip_id: Trip ID to delete
        """
        self.db.connection.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        self.db.connection.commit()
        self.db.mark_modified()
        self._cleanup_orphaned_cities()

    def get_all_trips(self) -> list[Trip]:
        """Get all trips ordered by start date."""
        cursor = self.db.connection.execute(
            "SELECT * FROM trips ORDER BY start_date DESC"
        )
        return [Trip(**dict(row)) for row in cursor.fetchall()]

    # Trip participants
    def add_trip_participant(self, trip_id: int, person_id: int) -> None:
        """Add a participant to a trip.

        Args:
            trip_id: Trip ID
            person_id: Person ID
        """
        self.db.connection.execute(
            "INSERT OR IGNORE INTO trip_participants (trip_id, person_id) VALUES (?, ?)",
            (trip_id, person_id)
        )
        self.db.connection.commit()
        self.db.mark_modified()

    def remove_trip_participant(self, trip_id: int, person_id: int) -> None:
        """Remove a participant from a trip.

        Args:
            trip_id: Trip ID
            person_id: Person ID
        """
        self.db.connection.execute(
            "DELETE FROM trip_participants WHERE trip_id = ? AND person_id = ?",
            (trip_id, person_id)
        )
        self.db.connection.commit()
        self.db.mark_modified()

    def get_trip_participants(self, trip_id: int) -> list[Person]:
        """Get all participants of a trip.

        Args:
            trip_id: Trip ID

        Returns:
            List of Person objects
        """
        cursor = self.db.connection.execute(
            """SELECT p.* FROM people p
               JOIN trip_participants tp ON p.id = tp.person_id
               WHERE tp.trip_id = ?
               ORDER BY p.name""",
            (trip_id,)
        )
        return [Person(**dict(row)) for row in cursor.fetchall()]

    def get_person_trips(self, person_id: int) -> list[Trip]:
        """Get all trips for a person.

        Args:
            person_id: Person ID

        Returns:
            List of Trip objects
        """
        cursor = self.db.connection.execute(
            """SELECT t.* FROM trips t
               JOIN trip_participants tp ON t.id = tp.trip_id
               WHERE tp.person_id = ?
               ORDER BY t.start_date DESC""",
            (person_id,)
        )
        return [Trip(**dict(row)) for row in cursor.fetchall()]

    # Trip cities
    def add_trip_city(self, trip_id: int, city_id: int, notes: Optional[str] = None) -> None:
        """Add a city to a trip.

        Args:
            trip_id: Trip ID
            city_id: City ID
            notes: Optional notes about the visit
        """
        self.db.connection.execute(
            "INSERT OR IGNORE INTO trip_cities (trip_id, city_id, notes) VALUES (?, ?, ?)",
            (trip_id, city_id, notes)
        )
        self.db.connection.commit()
        self.db.mark_modified()

    def remove_trip_city(self, trip_id: int, city_id: int) -> None:
        """Remove a city from a trip.

        Args:
            trip_id: Trip ID
            city_id: City ID
        """
        self.db.connection.execute(
            "DELETE FROM trip_cities WHERE trip_id = ? AND city_id = ?",
            (trip_id, city_id)
        )
        self.db.connection.commit()
        self.db.mark_modified()
        self._cleanup_orphaned_cities()

    def update_trip_city_notes(self, trip_id: int, city_id: int, notes: Optional[str]) -> None:
        """Update notes for a city on a trip.

        Args:
            trip_id: Trip ID
            city_id: City ID
            notes: Updated notes
        """
        self.db.connection.execute(
            "UPDATE trip_cities SET notes = ? WHERE trip_id = ? AND city_id = ?",
            (notes, trip_id, city_id)
        )
        self.db.connection.commit()
        self.db.mark_modified()

    def get_trip_cities(self, trip_id: int) -> list[City]:
        """Get all cities visited on a trip.

        Args:
            trip_id: Trip ID

        Returns:
            List of City objects
        """
        cursor = self.db.connection.execute(
            """SELECT c.* FROM cities c
               JOIN trip_cities tc ON c.id = tc.city_id
               WHERE tc.trip_id = ?
               ORDER BY c.name""",
            (trip_id,)
        )
        return [City(**dict(row)) for row in cursor.fetchall()]

    def get_trip_cities_with_notes(self, trip_id: int) -> list[tuple[City, Optional[str]]]:
        """Get all cities visited on a trip along with their notes.

        Args:
            trip_id: Trip ID

        Returns:
            List of tuples containing (City object, notes)
        """
        cursor = self.db.connection.execute(
            """SELECT c.*, tc.notes FROM cities c
               JOIN trip_cities tc ON c.id = tc.city_id
               WHERE tc.trip_id = ?
               ORDER BY c.name""",
            (trip_id,)
        )
        result = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            notes = row_dict.pop('notes', None)
            city = City(**row_dict)
            result.append((city, notes))
        return result

    def get_city_trips(self, city_id: int) -> list[Trip]:
        """Get all trips that include a specific city.

        Args:
            city_id: City ID

        Returns:
            List of Trip objects ordered by start date descending
        """
        cursor = self.db.connection.execute(
            """SELECT t.* FROM trips t
               JOIN trip_cities tc ON t.id = tc.trip_id
               WHERE tc.city_id = ?
               ORDER BY t.start_date DESC""",
            (city_id,)
        )
        return [Trip(**dict(row)) for row in cursor.fetchall()]

    def get_person_cities(self, person_id: int) -> list[City]:
        """Get all cities visited by a person across all trips.

        Args:
            person_id: Person ID

        Returns:
            List of unique City objects
        """
        cursor = self.db.connection.execute(
            """SELECT DISTINCT c.* FROM cities c
               JOIN trip_cities tc ON c.id = tc.city_id
               JOIN trip_participants tp ON tc.trip_id = tp.trip_id
               WHERE tp.person_id = ?
               ORDER BY c.name""",
            (person_id,)
        )
        return [City(**dict(row)) for row in cursor.fetchall()]

    def get_all_visited_cities(self) -> list[City]:
        """Get all cities that have been visited on any trip.

        Returns:
            List of unique City objects, sorted by most recent visit date
        """
        cursor = self.db.connection.execute(
            """SELECT DISTINCT c.*, MAX(t.start_date) as last_visit
               FROM cities c
               JOIN trip_cities tc ON c.id = tc.city_id
               JOIN trips t ON t.id = tc.trip_id
               GROUP BY c.id
               ORDER BY last_visit DESC, c.name"""
        )
        # We only want to return City objects, not the last_visit date
        cities = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Remove the last_visit field as it's not part of the City model
            row_dict.pop('last_visit', None)
            cities.append(City(**row_dict))
        return cities

    def get_visited_cities_by_country(self, country_code: str) -> list[City]:
        """Get all cities visited in a specific country.

        Args:
            country_code: ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "FR")

        Returns:
            List of unique City objects for the given country, sorted alphabetically
        """
        cursor = self.db.connection.execute(
            """SELECT DISTINCT c.* FROM cities c
               JOIN trip_cities tc ON c.id = tc.city_id
               WHERE UPPER(c.country) = UPPER(?)
               ORDER BY c.name""",
            (country_code.upper(),)
        )
        return [City(**dict(row)) for row in cursor.fetchall()]

    def _cleanup_orphaned_cities(self) -> None:
        """Remove cities that are not associated with any trips."""
        self.db.connection.execute(
            """DELETE FROM cities
               WHERE id NOT IN (SELECT DISTINCT city_id FROM trip_cities)"""
        )
        self.db.connection.commit()
        self.db.mark_modified()

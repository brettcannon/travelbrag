-- Trip recording database schema

-- Cities table (normalized for reuse across trips)
CREATE TABLE cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    geonameid INTEGER UNIQUE,
    name TEXT NOT NULL,
    admin_division TEXT,
    country TEXT NOT NULL,    -- ISO 3166-1 alpha-2 code (e.g., US, GB, FR)
    latitude TEXT NOT NULL,  -- Stored as TEXT to maintain precision
    longitude TEXT NOT NULL, -- Stored as TEXT to maintain precision
    UNIQUE(name, admin_division, country),
    CHECK(LENGTH(country) = 2)  -- Enforce ISO 3166-1 alpha-2 format
);

-- People table
CREATE TABLE people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Main trips table
CREATE TABLE trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    notes TEXT,
    start_date TEXT NOT NULL,  -- ISO format: YYYY-MM-DD or YYYY-MM
    end_date TEXT NOT NULL,    -- ISO format: YYYY-MM-DD or YYYY-MM
    CHECK(end_date >= start_date)
);

-- Junction table for trip participants (many-to-many)
CREATE TABLE trip_participants (
    trip_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    PRIMARY KEY (trip_id, person_id),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
);

-- Junction table for cities visited on trips (many-to-many)
CREATE TABLE trip_cities (
    trip_id INTEGER NOT NULL,
    city_id INTEGER NOT NULL,
    notes TEXT,
    PRIMARY KEY (trip_id, city_id),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE CASCADE
);

-- Example queries for your use cases:

-- Countries a person has visited (returns ISO codes):
-- SELECT DISTINCT c.country
-- FROM people p
-- JOIN trip_participants tp ON p.id = tp.person_id
-- JOIN trip_cities tc ON tp.trip_id = tc.trip_id
-- JOIN cities c ON tc.city_id = c.id
-- WHERE p.name = 'John Doe';

-- Trips in chronological order:
-- SELECT * FROM trips ORDER BY start_date;

-- Who has visited what cities:
-- SELECT p.name, c.name, c.country, t.name as trip_name
-- FROM people p
-- JOIN trip_participants tp ON p.id = tp.person_id
-- JOIN trip_cities tc ON tp.trip_id = tc.trip_id
-- JOIN cities c ON tc.city_id = c.id
-- JOIN trips t ON tp.trip_id = t.id
-- ORDER BY p.name, c.name;

-- Last time a city was visited:
-- SELECT c.name, c.country, MAX(t.end_date) as last_visit
-- FROM cities c
-- JOIN trip_cities tc ON c.id = tc.city_id
-- JOIN trips t ON tc.trip_id = t.id
-- WHERE c.name = 'Paris'
-- GROUP BY c.id;

-- Performance indices
CREATE INDEX IF NOT EXISTS idx_cities_geonameid ON cities(geonameid);
CREATE INDEX IF NOT EXISTS idx_cities_country ON cities(country);
CREATE INDEX IF NOT EXISTS idx_trips_start_date ON trips(start_date DESC);
CREATE INDEX IF NOT EXISTS idx_trip_cities_city_id ON trip_cities(city_id);
CREATE INDEX IF NOT EXISTS idx_trip_participants_person_id ON trip_participants(person_id);
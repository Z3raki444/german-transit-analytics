
CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY,
    route_short_name TEXT,
    route_long_name TEXT,
    agency_id TEXT,
    route_type INTEGER
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT REFERENCES routes(route_id),
    service_id TEXT
);

CREATE TABLE IF NOT EXISTS stop_times (
    trip_id TEXT REFERENCES trips(trip_id),
    stop_id TEXT NOT NULL,
    arrival_time TEXT,
    departure_time TEXT,
    stop_sequence INTEGER NOT NULL,
    stop_headsign TEXT,
    pickup_type TEXT,
    drop_off_type TEXT,
    PRIMARY KEY (trip_id, stop_sequence)
);

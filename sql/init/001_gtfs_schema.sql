-- Executed by the official PostgreSQL image only on first initialization.
-- Matches columns used by the current Python COPY loaders.

CREATE TABLE IF NOT EXISTS public.stops (
    stop_id TEXT PRIMARY KEY,
    stop_name TEXT NOT NULL,
    stop_lat DOUBLE PRECISION,
    stop_lon DOUBLE PRECISION,
    location_type TEXT,
    parent_station TEXT
);

CREATE TABLE IF NOT EXISTS public.routes (
    route_id TEXT PRIMARY KEY,
    route_short_name TEXT,
    route_long_name TEXT,
    agency_id TEXT,
    route_type INTEGER
);

CREATE TABLE IF NOT EXISTS public.trips (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT REFERENCES public.routes(route_id),
    service_id TEXT
);

CREATE TABLE IF NOT EXISTS public.stop_times (
    trip_id TEXT REFERENCES public.trips(trip_id),
    stop_id TEXT NOT NULL,
    arrival_time TEXT,
    departure_time TEXT,
    stop_sequence INTEGER NOT NULL,
    stop_headsign TEXT,
    pickup_type TEXT,
    drop_off_type TEXT,
    PRIMARY KEY (trip_id, stop_sequence)
);

CREATE TABLE IF NOT EXISTS public.service_dates (
    service_id TEXT NOT NULL,
    service_date DATE NOT NULL,
    PRIMARY KEY (service_id, service_date)
);

CREATE INDEX IF NOT EXISTS idx_service_dates_service
    ON public.service_dates (service_id);
CREATE INDEX IF NOT EXISTS idx_service_dates_date
    ON public.service_dates (service_date);
CREATE INDEX IF NOT EXISTS idx_trips_service
    ON public.trips (service_id);
CREATE INDEX IF NOT EXISTS idx_stop_times_stop
    ON public.stop_times (stop_id);

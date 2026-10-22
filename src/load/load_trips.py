
import os
from pathlib import Path
import psycopg

CSV_PATH = Path("data/processed/trips.csv")

if not CSV_PATH.exists():
    raise FileNotFoundError(f"Missing file: {CSV_PATH}")

with psycopg.connect(
    host=os.getenv("TRANSIT_DB_HOST", "127.0.0.1"),
    port=int(os.getenv("TRANSIT_DB_PORT", "5433")),
    dbname="transit_analytics",
    user="transit_user",
    password=os.environ["TRANSIT_DB_PASSWORD"]
) as conn:

    with conn.cursor() as cur:

        # Temporary staging table
        cur.execute("""
            CREATE TEMP TABLE trips_stage (
                trip_id TEXT,
                route_id TEXT,
                service_id TEXT
            ) ON COMMIT DROP
        """)

        # Load cleaned CSV into staging table
        with cur.copy("""
            COPY trips_stage (trip_id, route_id, service_id)
            FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
        """) as copy:

            with CSV_PATH.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    copy.write(chunk)

        # Insert new trips or update existing ones
        cur.execute("""
            INSERT INTO trips (trip_id, route_id, service_id)
            SELECT trip_id, route_id, service_id
            FROM trips_stage
            WHERE TRUE
            ON CONFLICT (trip_id)
            DO UPDATE SET
                route_id = EXCLUDED.route_id,
                service_id = EXCLUDED.service_id
        """)

        cur.execute("SELECT COUNT(*) FROM trips")
        total = cur.fetchone()[0]

print(f"Successfully loaded {total} trips into PostgreSQL!")

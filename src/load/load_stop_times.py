
import os
from pathlib import Path
import psycopg

CSV_PATH = Path("data/processed/stop_times.csv")

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

        # Create temporary staging table
        cur.execute("""
            CREATE TEMP TABLE stop_times_stage
            (LIKE stop_times) ON COMMIT DROP
        """)

        # Copy CSV data into staging
        with cur.copy("""
            COPY stop_times_stage (
                trip_id,
                stop_id,
                arrival_time,
                departure_time,
                stop_sequence,
                stop_headsign,
                pickup_type,
                drop_off_type
            )
            FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
        """) as copy:

            with CSV_PATH.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    copy.write(chunk)

        # Verify staged records
        cur.execute("SELECT COUNT(*) FROM stop_times_stage")
        staged = cur.fetchone()[0]

        # Insert or update timetable records
        cur.execute("""
            INSERT INTO stop_times (
                trip_id,
                stop_id,
                arrival_time,
                departure_time,
                stop_sequence,
                stop_headsign,
                pickup_type,
                drop_off_type
            )
            SELECT
                trip_id,
                stop_id,
                arrival_time,
                departure_time,
                stop_sequence,
                stop_headsign,
                pickup_type,
                drop_off_type
            FROM stop_times_stage
            WHERE TRUE
            ON CONFLICT (trip_id, stop_sequence)
            DO UPDATE SET
                stop_id = EXCLUDED.stop_id,
                arrival_time = EXCLUDED.arrival_time,
                departure_time = EXCLUDED.departure_time,
                stop_headsign = EXCLUDED.stop_headsign,
                pickup_type = EXCLUDED.pickup_type,
                drop_off_type = EXCLUDED.drop_off_type
        """)

        cur.execute("SELECT COUNT(*) FROM stop_times")
        total = cur.fetchone()[0]

print(f"Records staged: {staged}")
print(f"Total stop times in PostgreSQL: {total}")
print("Timetable loading completed!")

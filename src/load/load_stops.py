
import os
from pathlib import Path
import psycopg

CSV_PATH = Path("data/processed/stops.csv")

if not CSV_PATH.exists():
    raise FileNotFoundError(f"Missing file: {CSV_PATH}")

# Connect to PostgreSQL running in Docker
with psycopg.connect(
    host="localhost",
    port=5433,
    dbname="transit_analytics",
    user="transit_user",
    password=os.getenv("TRANSIT_DB_PASSWORD", "local_dev_password")
) as conn:

    with conn.cursor() as cur:

        # Replace previous station records
        cur.execute("TRUNCATE TABLE stops")

        # Load the cleaned CSV
        with cur.copy("""
            COPY stops (
                stop_id, stop_name, stop_lat,
                stop_lon, location_type, parent_station
            )
            FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
        """) as copy:

            with CSV_PATH.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    copy.write(chunk)

        # Verify the imported records
        cur.execute("SELECT COUNT(*) FROM stops")
        total = cur.fetchone()[0]

print(f"Successfully loaded {total} stops into PostgreSQL!")

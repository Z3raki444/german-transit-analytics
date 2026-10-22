
import os
from pathlib import Path
import psycopg

CSV_PATH = Path("data/processed/service_dates.csv")

if not CSV_PATH.exists():
    raise FileNotFoundError(f"Missing file: {CSV_PATH}")

with psycopg.connect(
    host=os.getenv("TRANSIT_DB_HOST", "127.0.0.1"),
    port=int(os.getenv("TRANSIT_DB_PORT", "5433")),
    dbname="transit_analytics",
    user="transit_user",
    password=os.getenv("TRANSIT_DB_PASSWORD", "local_dev_password")
) as conn:

    with conn.cursor() as cur:

        # Refresh calendar data within one transaction
        cur.execute("TRUNCATE TABLE service_dates")

        with cur.copy("""
            COPY service_dates (service_id, service_date)
            FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
        """) as copy:

            with CSV_PATH.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    copy.write(chunk)

        cur.execute("""
            SELECT COUNT(*), MIN(service_date), MAX(service_date)
            FROM service_dates
        """)

        total, first_date, last_date = cur.fetchone()

print(f"Loaded {total} service-date records!")
print(f"Calendar coverage: {first_date} to {last_date}")

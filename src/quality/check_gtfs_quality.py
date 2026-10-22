
import csv
import os
from pathlib import Path
import psycopg

BASE_DIR = Path(__file__).resolve().parents[2]

tables = [
    "stops",
    "routes",
    "trips",
    "stop_times",
    "service_dates"
]

errors = []

with psycopg.connect(
    host=os.getenv("TRANSIT_DB_HOST", "127.0.0.1"),
    port=int(os.getenv("TRANSIT_DB_PORT", "5433")),
    dbname="transit_analytics",
    user="transit_user",
    password=os.getenv("TRANSIT_DB_PASSWORD", "local_dev_password")
) as conn:

    with conn.cursor() as cur:

        print("Checking GTFS data quality...\n")

        # 1. Check table counts against CSV files
        for table in tables:
            csv_path = BASE_DIR / "data" / "processed" / f"{table}.csv"

            with csv_path.open(
                encoding="utf-8-sig", newline=""
            ) as file:
                csv_count = sum(1 for _ in csv.DictReader(file))

            cur.execute(f"SELECT COUNT(*) FROM {table}")
            db_count = cur.fetchone()[0]

            print(f"{table}: CSV={csv_count}, DB={db_count}")

            if db_count == 0 or csv_count != db_count:
                errors.append(f"{table}: missing or mismatched rows")

        # 2. Check trips with missing routes
        cur.execute("""
            SELECT COUNT(*)
            FROM trips t
            LEFT JOIN routes r ON t.route_id = r.route_id
            WHERE r.route_id IS NULL
        """)

        orphan_trips = cur.fetchone()[0]

        if orphan_trips:
            errors.append(f"Invalid trip references: {orphan_trips}")

        # 3. Check stop times with missing trips
        cur.execute("""
            SELECT COUNT(*)
            FROM stop_times st
            LEFT JOIN trips t ON st.trip_id = t.trip_id
            WHERE t.trip_id IS NULL
        """)

        orphan_times = cur.fetchone()[0]

        if orphan_times:
            errors.append(f"Invalid timetable references: {orphan_times}")

        # 4. Report missing station references
        cur.execute("""
            SELECT COUNT(*)
            FROM stop_times st
            LEFT JOIN stops s ON st.stop_id = s.stop_id
            WHERE s.stop_id IS NULL
        """)

        missing_stops = cur.fetchone()[0]
        print(f"\nUnmatched stop references: {missing_stops}")

if errors:
    print("\nDATA QUALITY FAILED")
    for error in errors:
        print(f"ERROR: {error}")
    raise SystemExit(1)

print("\nALL REQUIRED DATA QUALITY CHECKS PASSED!")

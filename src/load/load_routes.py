
import os
from pathlib import Path
import psycopg

CSV_PATH = Path("data/processed/routes.csv")

if not CSV_PATH.exists():
    raise FileNotFoundError(f"File not found: {CSV_PATH}")

with psycopg.connect(
    host=os.getenv("TRANSIT_DB_HOST", "127.0.0.1"),
    port=int(os.getenv("TRANSIT_DB_PORT", "5433")),
    dbname="transit_analytics",
    user="transit_user",
    password=os.environ["TRANSIT_DB_PASSWORD"]
) as conn:

    with conn.cursor() as cur:

        # Create a temporary staging table
        cur.execute("""
            CREATE TEMP TABLE routes_stage
            (LIKE routes) ON COMMIT DROP
        """)

        # Load CSV into staging table
        with cur.copy("""
            COPY routes_stage (
                route_id,
                route_short_name,
                route_long_name,
                agency_id,
                route_type
            )
            FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
        """) as copy:

            with CSV_PATH.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    copy.write(chunk)

        # Insert new routes or update existing routes
        cur.execute("""
            INSERT INTO routes (
                route_id, route_short_name,
                route_long_name, agency_id, route_type
            )
            SELECT
                route_id, route_short_name,
                route_long_name, agency_id, route_type
            FROM routes_stage
            ON CONFLICT (route_id)
            DO UPDATE SET
                route_short_name = EXCLUDED.route_short_name,
                route_long_name = EXCLUDED.route_long_name,
                agency_id = EXCLUDED.agency_id,
                route_type = EXCLUDED.route_type
        """)

        cur.execute("SELECT COUNT(*) FROM routes")
        total = cur.fetchone()[0]

print(f"Successfully loaded {total} routes into PostgreSQL!")

"""Run the full batch GTFS extract/transform/load/quality workflow locally.

Requires PostgreSQL tables already initialized and TRANSIT_DB_PASSWORD set.
Airflow (not this script) also runs the dbt analytics build.
"""
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STEPS = [
    "src/ingestion/extract_gtfs_static.py",
    "src/transform/clean_stops.py",
    "src/load/load_stops.py",
    "src/transform/clean_routes.py",
    "src/load/load_routes.py",
    "src/transform/clean_trips.py",
    "src/load/load_trips.py",
    "src/transform/clean_stop_times.py",
    "src/load/load_stop_times.py",
    "src/transform/clean_service_calendar.py",
    "src/load/load_service_dates.py",
    "src/quality/check_gtfs_quality.py",
]

def main():
    print(f"Started: {datetime.now(timezone.utc).isoformat()}", flush=True)
    for script in STEPS:
        print(f"Running {script} ...", flush=True)
        subprocess.run([sys.executable, script], cwd=BASE_DIR, check=True)
    print("GTFS ETL and quality checks completed.", flush=True)

if __name__ == "__main__":
    main()

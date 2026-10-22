
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

steps = [
    ("EXTRACT", "src/ingestion/extract_gtfs_static.py"),
    ("TRANSFORM", "src/transform/clean_stops.py"),
    ("LOAD", "src/load/load_stops.py"),
]

print(f"ETL started: {datetime.now()}", flush=True)

for step_name, script in steps:
    print(f"\nRunning {step_name}...", flush=True)

    subprocess.run(
        [sys.executable, str(BASE_DIR / script)],
        cwd=BASE_DIR,
        check=True
    )

    print(f"{step_name} completed!", flush=True)

print(f"\nETL finished: {datetime.now()}", flush=True)

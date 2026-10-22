
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

URL = "https://download.gtfs.de/germany/fv_free/latest.zip"

OUTPUT = Path("data/raw/long_distance_rail_gtfs.zip")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

temp_path = None

try:
    print("Downloading GTFS data...")

    # Download to a temporary file first
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=OUTPUT.parent,
        prefix=".gtfs_",
        suffix=".zip",
        delete=False
    ) as temp_file:

        temp_path = Path(temp_file.name)

        with urlopen(URL, timeout=120) as response:
            shutil.copyfileobj(response, temp_file)

    print("Validating downloaded ZIP...")

    # Validate archive before replacing the old data
    with zipfile.ZipFile(temp_path) as archive:

        required_files = {
            "stops.txt",
            "routes.txt",
            "trips.txt",
            "stop_times.txt"
        }

        missing = required_files - set(archive.namelist())

        if missing:
            raise ValueError(f"Missing GTFS files: {missing}")

        corrupted = archive.testzip()

        if corrupted is not None:
            raise ValueError(f"Corrupted ZIP entry: {corrupted}")

    # Replace the old ZIP only after validation
    os.replace(temp_path, OUTPUT)

    size_mb = OUTPUT.stat().st_size / (1024 * 1024)

    print("GTFS extraction successful!")
    print(f"Saved to: {OUTPUT}")
    print(f"File size: {size_mb:.2f} MB")

finally:
    # Remove temporary files after failure
    if temp_path is not None:
        temp_path.unlink(missing_ok=True)

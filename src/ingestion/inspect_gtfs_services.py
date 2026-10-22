
import zipfile
import csv
import io

ZIP_PATH = "data/raw/long_distance_rail_gtfs.zip"

files = [
    "routes.txt",
    "trips.txt",
    "stop_times.txt"
]

with zipfile.ZipFile(ZIP_PATH) as archive:

    for filename in files:
        print(f"\n--- {filename} ---")

        with archive.open(filename) as file:
            reader = csv.DictReader(
                io.TextIOWrapper(file, encoding="utf-8-sig")
            )

            print("Columns:", reader.fieldnames)

            print("Sample records:")
            for _, row in zip(range(2), reader):
                print(row)

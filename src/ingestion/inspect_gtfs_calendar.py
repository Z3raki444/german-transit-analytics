
import zipfile
import csv
import io

ZIP_PATH = "data/raw/long_distance_rail_gtfs.zip"

with zipfile.ZipFile(ZIP_PATH) as archive:

    files = archive.namelist()

    for filename in ["calendar.txt", "calendar_dates.txt"]:

        print(f"\n--- {filename} ---")

        if filename not in files:
            print("File not available")
            continue

        with archive.open(filename) as file:
            reader = csv.DictReader(
                io.TextIOWrapper(file, encoding="utf-8-sig")
            )

            print("Columns:", reader.fieldnames)

            for _, row in zip(range(3), reader):
                print(row)

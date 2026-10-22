
import csv
import io
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

SOURCE = Path("data/raw/long_distance_rail_gtfs.zip")
OUTPUT = Path("data/processed/service_dates.csv")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

active_services = set()

weekdays = [
    "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday"
]

def parse_date(value):
    return datetime.strptime(value, "%Y%m%d").date()

def read_gtfs_file(archive, filename):
    with archive.open(filename) as file:
        reader = csv.DictReader(
            io.TextIOWrapper(file, encoding="utf-8-sig")
        )
        yield from reader

with zipfile.ZipFile(SOURCE) as archive:
    filenames = archive.namelist()

    # Step 1: Regular weekly schedules
    if "calendar.txt" in filenames:
        for row in read_gtfs_file(archive, "calendar.txt"):
            service_id = row["service_id"]
            current = parse_date(row["start_date"])
            end = parse_date(row["end_date"])

            while current <= end:
                day_name = weekdays[current.weekday()]

                if row[day_name] == "1":
                    active_services.add(
                        (service_id, current.isoformat())
                    )

                current += timedelta(days=1)

    # Step 2: Apply service additions and removals
    if "calendar_dates.txt" in filenames:
        for row in read_gtfs_file(
            archive, "calendar_dates.txt"
        ):
            service_id = row["service_id"]
            service_date = parse_date(row["date"])

            key = (service_id, service_date.isoformat())

            if row["exception_type"] == "1":
                active_services.add(key)

            elif row["exception_type"] == "2":
                active_services.discard(key)

if not active_services:
    raise ValueError("No active service dates found")

# Step 3: Export cleaned data
with OUTPUT.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["service_id", "service_date"])

    for service_id, service_date in sorted(active_services):
        writer.writerow([service_id, service_date])

print(f"Active service-date records: {len(active_services)}")
print(f"Saved to: {OUTPUT}")

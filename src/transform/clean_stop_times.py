
import csv
import io
import re
import zipfile
from pathlib import Path

SOURCE = Path("data/raw/long_distance_rail_gtfs.zip")
TRIPS = Path("data/processed/trips.csv")
STOPS = Path("data/processed/stops.csv")
OUTPUT = Path("data/processed/stop_times.csv")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# Load valid trip and stop IDs
with TRIPS.open(encoding="utf-8-sig", newline="") as file:
    valid_trips = {
        row["trip_id"] for row in csv.DictReader(file)
    }

with STOPS.open(encoding="utf-8-sig", newline="") as file:
    valid_stops = {
        row["stop_id"] for row in csv.DictReader(file)
    }

# GTFS permits times like 25:30:00
time_pattern = re.compile(r"\d{2,}:[0-5]\d:[0-5]\d")

def valid_time(value):
    return not value or bool(time_pattern.fullmatch(value))

columns = [
    "trip_id",
    "stop_id",
    "arrival_time",
    "departure_time",
    "stop_sequence",
    "stop_headsign",
    "pickup_type",
    "drop_off_type"
]

seen = set()
cleaned = 0
skipped = 0
unmatched_stops = 0

with zipfile.ZipFile(SOURCE) as archive:
    with archive.open("stop_times.txt") as file:
        reader = csv.DictReader(
            io.TextIOWrapper(file, encoding="utf-8-sig")
        )

        with OUTPUT.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()

            for row in reader:
                trip_id = (row.get("trip_id") or "").strip()
                stop_id = (row.get("stop_id") or "").strip()
                arrival = (row.get("arrival_time") or "").strip()
                departure = (row.get("departure_time") or "").strip()

                try:
                    sequence = int(row["stop_sequence"])
                except (ValueError, TypeError, KeyError):
                    skipped += 1
                    continue

                key = (trip_id, sequence)

                if (
                    trip_id not in valid_trips
                    or not stop_id
                    or sequence < 0
                    or key in seen
                    or not valid_time(arrival)
                    or not valid_time(departure)
                ):
                    skipped += 1
                    continue

                writer.writerow({
                    "trip_id": trip_id,
                    "stop_id": stop_id,
                    "arrival_time": arrival,
                    "departure_time": departure,
                    "stop_sequence": sequence,
                    "stop_headsign": row.get("stop_headsign") or "",
                    "pickup_type": row.get("pickup_type") or "",
                    "drop_off_type": row.get("drop_off_type") or ""
                })

                if stop_id not in valid_stops:
                    unmatched_stops += 1

                seen.add(key)
                cleaned += 1

print(f"Cleaned stop times: {cleaned}")
print(f"Skipped records: {skipped}")
print(f"Unmatched stop references: {unmatched_stops}")
print(f"Saved to: {OUTPUT}")


import csv
import io
import zipfile
from pathlib import Path

SOURCE = Path("data/raw/long_distance_rail_gtfs.zip")
ROUTES = Path("data/processed/routes.csv")
OUTPUT = Path("data/processed/trips.csv")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# Read valid route IDs
with ROUTES.open("r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)
    valid_routes = {row["route_id"] for row in reader}

seen_trips = set()
cleaned = 0
skipped = 0

# Read trips directly from the ZIP
with zipfile.ZipFile(SOURCE) as archive:
    with archive.open("trips.txt") as file:

        reader = csv.DictReader(
            io.TextIOWrapper(file, encoding="utf-8-sig")
        )

        with OUTPUT.open("w", newline="", encoding="utf-8") as output:

            writer = csv.DictWriter(
                output,
                fieldnames=["trip_id", "route_id", "service_id"]
            )
            writer.writeheader()

            for row in reader:
                trip_id = (row.get("trip_id") or "").strip()
                route_id = (row.get("route_id") or "").strip()
                service_id = (row.get("service_id") or "").strip()

                if (
                    not trip_id
                    or not service_id
                    or route_id not in valid_routes
                    or trip_id in seen_trips
                ):
                    skipped += 1
                    continue

                writer.writerow({
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "service_id": service_id
                })

                seen_trips.add(trip_id)
                cleaned += 1

print(f"Cleaned trips: {cleaned}")
print(f"Skipped trips: {skipped}")
print(f"Saved to: {OUTPUT}")

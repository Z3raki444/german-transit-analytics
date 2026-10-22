
import zipfile
import csv
import io
from pathlib import Path

SOURCE = Path("data/raw/long_distance_rail_gtfs.zip")
OUTPUT = Path("data/processed/routes.csv")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

columns = [
    "route_id",
    "route_short_name",
    "route_long_name",
    "agency_id",
    "route_type"
]

seen_routes = set()
cleaned = 0
skipped = 0

with zipfile.ZipFile(SOURCE) as archive:
    with archive.open("routes.txt") as file:

        reader = csv.DictReader(
            io.TextIOWrapper(file, encoding="utf-8-sig")
        )

        with OUTPUT.open("w", newline="", encoding="utf-8") as output:

            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()

            for row in reader:
                route_id = (row.get("route_id") or "").strip()

                try:
                    route_type = int(row["route_type"])
                except (ValueError, TypeError, KeyError):
                    skipped += 1
                    continue

                if not route_id or route_id in seen_routes:
                    skipped += 1
                    continue

                writer.writerow({
                    "route_id": route_id,
                    "route_short_name": row.get("route_short_name", ""),
                    "route_long_name": row.get("route_long_name", ""),
                    "agency_id": row.get("agency_id", ""),
                    "route_type": route_type
                })

                seen_routes.add(route_id)
                cleaned += 1

print(f"Cleaned routes: {cleaned}")
print(f"Skipped routes: {skipped}")
print(f"Saved to: {OUTPUT}")

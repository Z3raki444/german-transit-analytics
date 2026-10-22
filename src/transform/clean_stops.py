
import csv
import io
import zipfile
from pathlib import Path

SOURCE = Path("data/raw/long_distance_rail_gtfs.zip")
OUTPUT = Path("data/processed/stops.csv")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

seen_ids = set()
cleaned_count = 0
skipped_count = 0

with zipfile.ZipFile(SOURCE) as archive:
    with archive.open("stops.txt") as file:
        reader = csv.DictReader(
            io.TextIOWrapper(file, encoding="utf-8-sig")
        )

        with OUTPUT.open("w", newline="", encoding="utf-8") as output:
            columns = [
                "stop_id", "stop_name",
                "stop_lat", "stop_lon",
                "location_type", "parent_station"
            ]

            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()

            for row in reader:
                stop_id = (row.get("stop_id") or "").strip()
                name = (row.get("stop_name") or "").strip()

                try:
                    lat = float(row["stop_lat"])
                    lon = float(row["stop_lon"])
                except (ValueError, TypeError, KeyError):
                    skipped_count += 1
                    continue

                if (
                    not stop_id
                    or not name
                    or stop_id in seen_ids
                    or not (-90 <= lat <= 90)
                    or not (-180 <= lon <= 180)
                ):
                    skipped_count += 1
                    continue

                writer.writerow({
                    "stop_id": stop_id,
                    "stop_name": name,
                    "stop_lat": lat,
                    "stop_lon": lon,
                    "location_type": row.get("location_type") or "0",
                    "parent_station": row.get("parent_station") or ""
                })

                seen_ids.add(stop_id)
                cleaned_count += 1

print(f"Cleaned records: {cleaned_count}")
print(f"Skipped records: {skipped_count}")
print(f"Saved to: {OUTPUT}")

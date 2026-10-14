
import json
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "departures_cleaned.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_datetime(value):
    if not value:
        return pd.NaT
    return pd.to_datetime(value, utc=True, errors="coerce")


def get_delay_category(delay_seconds):
    if pd.isna(delay_seconds):
        return "Unknown"
    if delay_seconds < 0:
        return "Early"
    if delay_seconds <= 300:
        return "On time"
    if delay_seconds <= 600:
        return "Minor delay"
    if delay_seconds <= 1200:
        return "Moderate delay"
    return "Severe delay"


def transform_departure(departure, metadata):
    line = departure.get("line") or {}
    stop = departure.get("stop") or {}

    planned = parse_datetime(
        departure.get("plannedWhen")
    )
    predicted = parse_datetime(
        departure.get("when")
    )

    delay = departure.get("delay")
    if delay is not None:
        delay = pd.to_numeric(delay, errors="coerce")
        if pd.isna(delay):
            delay = None

    planned_platform = departure.get("plannedPlatform")
    platform = departure.get("platform")

    platform_changed = None
    if planned_platform is not None and platform is not None:
        platform_changed = (
            str(planned_platform) != str(platform)
        )

    return {
        "station_id": stop.get("id") or metadata["station_id"],
        "station_name": stop.get("name"),
        "trip_id": departure.get("tripId"),
        "line_id": line.get("id"),
        "line_name": line.get("name"),
        "transport_type": line.get("product"),
        "direction": departure.get("direction"),
        "planned_departure": planned,
        "predicted_departure": predicted,
        "delay_seconds": delay,
        "delay_minutes": (
            delay / 60 if delay is not None else None
        ),
        "planned_platform": planned_platform,
        "platform": platform,
        "platform_changed": platform_changed,
        "cancelled": departure.get("cancelled"),
        "delay_category": get_delay_category(delay),
        "collected_at": metadata["collected_at"],
        "source_file": metadata["source_file"],
    }


def main():
    records = []
    rejected = 0

    files = sorted(RAW_DIR.glob("departures_*.json"))

    if not files:
        print("No JSON files found in data/raw/")
        return

    for file_path in files:
        try:
            with open(file_path, encoding="utf-8") as file:
                payload = json.load(file)

            # Matches the JSON structure from Step 1
            data = payload.get("api_response") or {}
            departures = data.get("departures") or []

            metadata = {
                "station_id": payload.get("station_id"),
                "collected_at": parse_datetime(
                    payload.get("collected_at")
                ),
                "source_file": file_path.name,
            }

            if pd.isna(metadata["collected_at"]):
                print(f"Skipping {file_path.name}: invalid collection time")
                rejected += len(departures)
                continue

            for departure in departures:
                if not isinstance(departure, dict):
                    rejected += 1
                    continue

                row = transform_departure(
                    departure, metadata
                )

                # Essential fields for meaningful records
                if (
                    not row["station_id"]
                    or pd.isna(row["planned_departure"])
                    or not row["line_name"]
                ):
                    rejected += 1
                    continue

                records.append(row)

        except (OSError, ValueError, TypeError) as error:
            print(f"Error reading {file_path.name}: {error}")

    if not records:
        print("No valid departure records found.")
        return

    df = pd.DataFrame(records)

    # Remove duplicate records within the same snapshot
    df = df.drop_duplicates(
        subset=[
            "source_file",
            "station_id",
            "trip_id",
            "planned_departure",
            "line_name",
        ]
    )

    # Validate data
    df["valid_delay"] = (
        df["delay_seconds"].isna()
        | df["delay_seconds"].between(-3600, 86400)
    )

    invalid_delays = (~df["valid_delay"]).sum()

    # Preserve records, but mark implausible delays missing
    df.loc[~df["valid_delay"], [
        "delay_seconds", "delay_minutes"
    ]] = None

    df["delay_category"] = df["delay_seconds"].apply(
        get_delay_category
    )

    df = df.drop(columns=["valid_delay"])

    # Validate chronology of snapshots
    df = df.sort_values(
        ["collected_at", "station_id", "planned_departure"]
    )

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nTransformation completed!")
    print(f"Input files: {len(files)}")
    print(f"Clean records: {len(df)}")
    print(f"Rejected records: {rejected}")
    print(f"Invalid delay values: {invalid_delays}")
    print(f"Saved: {OUTPUT_FILE}")

    print("\nMissing values:")
    print(df.isna().sum())

    print("\nTransport types:")
    print(df["transport_type"].value_counts(dropna=False))

    print("\nDelay categories:")
    print(df["delay_category"].value_counts(dropna=False))


if __name__ == "__main__":
    main()

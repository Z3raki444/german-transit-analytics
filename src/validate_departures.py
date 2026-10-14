
import pandas as pd
from pathlib import Path

csv_path = Path("data/processed/departures_cleaned.csv")

df = pd.read_csv(csv_path)

print("Total rows:", len(df))
print("Columns:", len(df.columns))

print("\nSample data:")
print(df.head(5).to_string(index=False))

print("\nValidation checks:")

checks = {
    "Dataset is not empty": len(df) > 0,
    "Station IDs present": df["station_id"].notna().all(),
    "Line names present": df["line_name"].notna().all(),
    "Scheduled times present": df["planned_departure"].notna().all(),
    "Collection times present": df["collected_at"].notna().all(),
    "No duplicate snapshot keys": not df.duplicated(
        subset=[
            "source_file",
            "station_id",
            "trip_id",
            "planned_departure",
            "line_name",
        ]
    ).any(),
}

for check, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}: {check}")

print("\nSummary statistics:")
print(df["delay_minutes"].describe())

if not all(checks.values()):
    raise SystemExit("Validation failed")

print("\nValidation successful!")

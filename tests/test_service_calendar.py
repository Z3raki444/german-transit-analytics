"""Offline integration tests for GTFS service-calendar expansion."""
import csv
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "src" / "transform" / "clean_service_calendar.py"


class ServiceCalendarTests(unittest.TestCase):
    def run_calendar(self, calendar=None, exceptions=None):
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            archive_path = root / "data" / "raw" / "long_distance_rail_gtfs.zip"
            archive_path.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(archive_path, "w") as archive:
                if calendar is not None:
                    archive.writestr("calendar.txt", calendar)
                if exceptions is not None:
                    archive.writestr("calendar_dates.txt", exceptions)

            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            output = root / "data" / "processed" / "service_dates.csv"
            with output.open(newline="", encoding="utf-8") as file:
                return list(csv.DictReader(file))

    def test_weekly_calendar_with_exception_add_and_remove(self):
        calendar = (
            "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
            "S1,1,1,1,0,0,0,0,20261019,20261021\n"
        )
        exceptions = (
            "service_id,date,exception_type\n"
            "S1,20261020,2\n"
            "S1,20261022,1\n"
        )
        records = self.run_calendar(calendar, exceptions)
        self.assertEqual(
            {(r["service_id"], r["service_date"]) for r in records},
            {
                ("S1", "2026-10-19"),
                ("S1", "2026-10-21"),
                ("S1", "2026-10-22"),
            },
        )

    def test_exception_only_feed(self):
        records = self.run_calendar(
            exceptions="service_id,date,exception_type\nSpecial,20261023,1\n"
        )
        self.assertEqual(records, [{"service_id": "Special", "service_date": "2026-10-23"}])


if __name__ == "__main__":
    unittest.main()


import requests
import json
from pathlib import Path
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://v6.vbb.transport.rest"
STATION_ID = "900100003"

# Fetch departures
url = f"{BASE_URL}/stops/{STATION_ID}/departures"

try:
    response = requests.get(
        url,
        params={"duration": 30},
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    departures = data.get("departures", [])

    print(f"Departures found: {len(departures)}")

    # Preview first 5 records
    for departure in departures[:5]:
        line = departure.get("line") or {}

        print({
            "line": line.get("name"),
            "transport_type": line.get("product"),
            "direction": departure.get("direction"),
            "planned_departure": departure.get("plannedWhen"),
            "expected_departure": departure.get("when"),
            "delay_seconds": departure.get("delay"),
            "cancelled": departure.get("cancelled"),
            "platform": departure.get("platform")
        })

    # Save raw JSON
    output_folder = Path("data/raw")
    output_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    output_file = output_folder / f"departures_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            {
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "station_id": STATION_ID,
                "api_response": data
            },
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"Data saved: {output_file}")

except requests.RequestException as error:
    print(f"API request failed: {error}")

except (ValueError, TypeError) as error:
    print(f"Invalid API data: {error}")

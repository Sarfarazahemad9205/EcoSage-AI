
import os
import json
import requests

from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load API key from backend/.env
load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    raise ValueError("OPENAQ_API_KEY not found in .env")

BASE_URL = "https://api.openaq.org/v3"

HEADERS = {
    "X-API-Key": API_KEY
}

# Karnataka search-area bounding box
BBOX = "74.0,11.5,78.6,18.5"

# Save discovery results in Bronze
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "openaq"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_locations():
    url = f"{BASE_URL}/locations"

    params = {
        "iso": "IN",
        "bbox": BBOX,
        "limit": 1000,
        "page": 1
    }

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()
    return response.json()


def get_location_sensors(location_id):
    url = f"{BASE_URL}/locations/{location_id}/sensors"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()
    return response.json()


def main():
    print("Discovering monitoring stations...")

    locations_data = get_locations()
    locations = locations_data.get("results", [])

    print(f"Locations returned: {len(locations)}")

    discovered = []

    for location in locations:
        location_id = location["id"]
        location_name = location.get("name", "Unknown")

        print(f"Checking sensors: {location_name} ({location_id})")

        try:
            sensor_data = get_location_sensors(location_id)

            for sensor in sensor_data.get("results", []):
                parameter = sensor.get("parameter", {})

                if parameter.get("name", "").lower() == "pm25":
                    discovered.append({
                        "location_id": location_id,
                        "location_name": location_name,
                        "coordinates": location.get("coordinates"),
                        "sensor_id": sensor["id"],
                        "parameter": parameter.get("name"),
                        "unit": parameter.get("units"),
                        "sensor_name": sensor.get("name")
                    })

        except requests.RequestException as error:
            print(f"Could not retrieve sensors for {location_id}: {error}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    output_file = OUTPUT_DIR / f"karnataka_pm25_sensors_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(discovered, file, indent=4)

    print("\n========== DISCOVERY SUMMARY ==========")
    print(f"Locations checked: {len(locations)}")
    print(f"PM2.5 sensors found: {len(discovered)}")
    print(f"Saved to: {output_file}")

    for item in discovered:
        print(
            f"{item['location_name']} | "
            f"Location: {item['location_id']} | "
            f"Sensor: {item['sensor_id']} | "
            f"Unit: {item['unit']}"
        )


if __name__ == "__main__":
    main()

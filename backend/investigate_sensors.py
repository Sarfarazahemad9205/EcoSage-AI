
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

# Get the backend directory
BACKEND_DIR = Path(__file__).resolve().parent

# Load environment variables from backend/.env
load_dotenv(BACKEND_DIR / ".env")

# Read OpenAQ API key
API_KEY = os.getenv("OPENAQ_API_KEY")

BASE_URL = "https://api.openaq.org/v3/sensors"

# Sensors that returned zero measurements
SENSOR_IDS = [13852, 13836, 13898, 14641]

# Check API key before making requests
if not API_KEY:
    raise ValueError("OPENAQ_API_KEY not found in backend/.env")

headers = {
    "X-API-Key": API_KEY
}

# --------------------------------------------------
# SENSOR INVESTIGATION
# --------------------------------------------------

for sensor_id in SENSOR_IDS:

    print(f"\n{'=' * 50}")
    print(f"Investigating Sensor: {sensor_id}")
    print("=" * 50)

    try:
        response = requests.get(
            f"{BASE_URL}/{sensor_id}",
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            print("No sensor details returned.")
            continue

        sensor = results[0]

        print("Sensor Name:", sensor.get("name"))
        print("Parameter:", sensor.get("parameter", {}).get("name"))

        print("First Measurement:",
              sensor.get("datetimeFirst"))

        print("Last Measurement:",
              sensor.get("datetimeLast"))

        print("Latest Reading:",
              sensor.get("latest"))

        print("Coverage:",
              json.dumps(sensor.get("coverage"), indent=2))

    except requests.exceptions.RequestException as e:
        print("API Request Failed:", e)

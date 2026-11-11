
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SENSOR_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "openaq"
    / "karnataka_pm25_sensors.json"
)

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "openaq"

API_URL = "https://api.openaq.org/v3/sensors/{sensor_id}/measurements"

LIMIT = 1000

# Pilot: collect data for only 5 sensors.
# Later, change this to None to collect all sensors.
MAX_SENSORS = 5

DAYS_BACK = 7
MAX_RETRIES = 3


# --------------------------------------------------
# INITIALIZATION
# --------------------------------------------------

load_dotenv(PROJECT_ROOT / "backend" / ".env")

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    raise ValueError("OPENAQ_API_KEY not found in backend/.env")

headers = {
    "X-API-Key": API_KEY
}

session = requests.Session()
session.headers.update(headers)


# --------------------------------------------------
# LOAD SENSORS
# --------------------------------------------------

def load_sensors():
    with open(SENSOR_FILE, "r", encoding="utf-8") as file:
        sensors = json.load(file)

    if MAX_SENSORS is not None:
        sensors = sensors[:MAX_SENSORS]

    return sensors


# --------------------------------------------------
# FETCH ONE PAGE WITH RETRIES
# --------------------------------------------------

def fetch_page(sensor_id, page, datetime_from, datetime_to):

    url = API_URL.format(sensor_id=sensor_id)

    params = {
        "datetime_from": datetime_from,
        "datetime_to": datetime_to,
        "limit": LIMIT,
        "page": page
    }

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            response = session.get(
                url,
                params=params,
                timeout=30
            )

            response.raise_for_status()

            return response

        except requests.RequestException as error:

            print(
                f"  Request failed for sensor {sensor_id}, "
                f"page {page}, attempt {attempt}: {error}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)

    return None


# --------------------------------------------------
# SAVE RAW API RESPONSE
# --------------------------------------------------

def save_raw_response(response, sensor_id, page, run_dir):

    output_file = run_dir / f"sensor_{sensor_id}_page_{page}.json"

    with open(output_file, "wb") as file:
        file.write(response.content)

    return output_file


# --------------------------------------------------
# COLLECT MEASUREMENTS FOR ONE SENSOR
# --------------------------------------------------

def collect_sensor(sensor, datetime_from, datetime_to, run_dir):

    sensor_id = sensor["sensor_id"]

    print(
        f"\nCollecting: {sensor['location_name']} "
        f"| Sensor ID: {sensor_id}"
    )

    page = 1
    total_records = 0
    successful_pages = 0

    while True:

        response = fetch_page(
            sensor_id,
            page,
            datetime_from,
            datetime_to
        )

        if response is None:
            return {
                "sensor_id": sensor_id,
                "location_name": sensor["location_name"],
                "status": "failed",
                "records": total_records,
                "successful_pages": successful_pages,
                "failed_page": page
            }

        # Preserve the original response in Bronze.
        save_raw_response(response, sensor_id, page, run_dir)

        try:
            data = response.json()
            results = data.get("results", [])

            if not isinstance(results, list):
                raise ValueError("Unexpected API results format")

        except (ValueError, requests.exceptions.JSONDecodeError) as error:
            print(f"  Invalid JSON response: {error}")

            return {
                "sensor_id": sensor_id,
                "location_name": sensor["location_name"],
                "status": "invalid_response",
                "records": total_records,
                "successful_pages": successful_pages,
                "failed_page": page
            }

        count = len(results)

        total_records += count
        successful_pages += 1

        print(f"  Page {page}: {count} measurements")

        # A short page means there are no more pages.
        if count < LIMIT:
            break

        page += 1

        # Avoid sending requests too rapidly.
        time.sleep(0.2)

    print(f"  Total measurements: {total_records}")

    return {
        "sensor_id": sensor_id,
        "location_name": sensor["location_name"],
        "status": "success",
        "records": total_records,
        "successful_pages": successful_pages,
        "failed_page": None
    }


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def main():

    print("Starting Karnataka PM2.5 collection...")

    sensors = load_sensors()

    print(f"Sensors selected: {len(sensors)}")

    now = datetime.now(timezone.utc)

    start_time = now - timedelta(days=DAYS_BACK)

    datetime_from = start_time.isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    datetime_to = now.isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    run_id = now.strftime("%Y%m%dT%H%M%SZ")

    run_dir = RAW_DIR / "measurements" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"From: {datetime_from}")
    print(f"To:   {datetime_to}")
    print(f"Raw output: {run_dir}")

    summaries = []

    for sensor in sensors:

        summary = collect_sensor(
            sensor,
            datetime_from,
            datetime_to,
            run_dir
        )

        summaries.append(summary)

        time.sleep(0.2)

    # Save collection summary.
    summary_file = run_dir / "collection_summary.json"

    with open(summary_file, "w", encoding="utf-8") as file:
        json.dump(summaries, file, indent=4)

    successful = sum(
        item["status"] == "success"
        for item in summaries
    )

    failed = len(summaries) - successful

    total_records = sum(
        item["records"]
        for item in summaries
    )

    print("\n========== COLLECTION SUMMARY ==========")
    print(f"Sensors attempted: {len(sensors)}")
    print(f"Successful sensors: {successful}")
    print(f"Failed sensors: {failed}")
    print(f"Total measurements: {total_records}")
    print(f"Raw data directory: {run_dir}")
    print(f"Summary file: {summary_file}")

    print("\nCollection completed!")


if __name__ == "__main__":
    main()

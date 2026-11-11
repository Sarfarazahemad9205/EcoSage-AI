
import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

BOUNDARY_FILE = PROJECT_ROOT / "data" / "boundaries" / "karnataka.geojson"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "openaq"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "openaq"
REVIEW_DIR = PROJECT_ROOT / "data" / "rejected" / "openaq"


def find_latest_sensor_file():
    files = list(RAW_DIR.glob("karnataka_pm25_sensors_*.json"))

    if not files:
        raise FileNotFoundError("No Karnataka PM2.5 sensor discovery file found.")

    return max(files, key=lambda file: file.stat().st_mtime)


def main():
    print("Starting Karnataka geographic filtering...")

    # Load the Karnataka boundary
    boundary = gpd.read_file(BOUNDARY_FILE)

    if boundary.empty or boundary.crs is None:
        raise ValueError("Boundary file is empty or has no CRS information.")

    boundary = boundary.to_crs("EPSG:4326")
    karnataka_polygon = boundary.geometry.union_all()

    # Load discovered sensors
    input_file = find_latest_sensor_file()

    with open(input_file, "r", encoding="utf-8") as file:
        sensors = json.load(file)

    if not isinstance(sensors, list):
        raise ValueError("Expected the sensor JSON file to contain a list.")

    inside = []
    outside = []
    review = []

    for sensor in sensors:
        coordinates = sensor.get("coordinates") or {}

        latitude = coordinates.get("latitude")
        longitude = coordinates.get("longitude")

        try:
            latitude = float(latitude)
            longitude = float(longitude)

            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("Coordinates outside valid geographic ranges.")

            # Point order is longitude first, latitude second.
            point = Point(longitude, latitude)

            if karnataka_polygon.covers(point):
                inside.append(sensor)
            else:
                outside.append(sensor)

        except (TypeError, ValueError):
            review.append({
                "sensor": sensor,
                "reason": "Missing or invalid coordinates"
            })

    # Create output directories
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    # Save filtered Karnataka sensors
    output_file = PROCESSED_DIR / "karnataka_pm25_sensors.json"
    outside_file = REVIEW_DIR / "outside_karnataka_sensors.json"
    review_file = REVIEW_DIR / "sensors_needing_coordinate_review.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(inside, file, indent=4)

    with open(outside_file, "w", encoding="utf-8") as file:
        json.dump(outside, file, indent=4)

    with open(review_file, "w", encoding="utf-8") as file:
        json.dump(review, file, indent=4)

    print("\n========== FILTERING SUMMARY ==========")
    print(f"Discovered sensors: {len(sensors)}")
    print(f"Inside Karnataka: {len(inside)}")
    print(f"Outside Karnataka: {len(outside)}")
    print(f"Needs coordinate review: {len(review)}")
    print(f"\nFiltered file: {output_file}")
    print("Geographic filtering completed!")


if __name__ == "__main__":
    main()

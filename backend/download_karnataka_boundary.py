
import requests
import json
from pathlib import Path

URL = (
    "https://livingatlas.esri.in/server/rest/services/"
    "IAB2024/India_Administrative_Boundaries_2024/"
    "MapServer/1/query"
)

params = {
    "where": "name='Karnataka'",
    "outFields": "*",
    "returnGeometry": "true",
    "outSR": 4326,
    "f": "geojson"
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = PROJECT_ROOT / "data" / "boundaries"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "karnataka.geojson"


def main():
    print("Downloading Karnataka boundary from Esri India...")

    try:
        response = requests.get(
            URL,
            params=params,
            timeout=60
        )

        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])

        if not features:
            raise ValueError(
                "No Karnataka boundary found. "
                "Check the API response."
            )

        if len(features) != 1:
            raise ValueError(
                f"Expected 1 feature, received {len(features)}"
            )

        geometry = features[0].get("geometry")

        if not geometry:
            raise ValueError("Boundary geometry is missing.")

        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        print("\nBoundary downloaded successfully!")
        print("Features:", len(features))
        print("Geometry type:", geometry["type"])
        print("Saved to:", OUTPUT_FILE)

    except requests.RequestException as error:
        print("Network/API error:", error)

    except (ValueError, KeyError) as error:
        print("Data error:", error)


if __name__ == "__main__":
    main()

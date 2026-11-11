
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    raise ValueError("OpenAQ API key not found!")

url = "https://api.openaq.org/v3/locations"

headers = {
    "X-API-Key": API_KEY
}

params = {
    "iso": "IN",
    "bbox": "74.0,11.5,78.6,18.5",
    "limit": 1000,
    "page": 1
}

response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30
)

print("Status Code:", response.status_code)

response.raise_for_status()

data = response.json()

locations = data.get("results", [])

print("\nKARNATAKA REGION LOCATION SEARCH")
print("Total locations found:", len(locations))
print("Metadata:", data.get("meta"))

for location in locations:

    coordinates = location.get("coordinates", {})

    print("\n-----------------------------")
    print("Location:", location.get("name"))
    print("Location ID:", location.get("id"))

    print(
        "Latitude:",
        coordinates.get("latitude")
    )

    print(
        "Longitude:",
        coordinates.get("longitude")
    )

    sensors = location.get("sensors", [])

    print("Available sensors:")

    for sensor in sensors:
        parameter = sensor.get("parameter", {})

        print(
            " -",
            parameter.get("name"),
            "| Unit:",
            parameter.get("units"),
            "| Sensor ID:",
            sensor.get("id")
        )

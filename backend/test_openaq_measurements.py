
import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    raise ValueError("OpenAQ API key not found!")

# Kasturi Nagar PM2.5 sensor
SENSOR_ID = 12237600

url = f"https://api.openaq.org/v3/sensors/{SENSOR_ID}/measurements"

headers = {
    "X-API-Key": API_KEY
}

# Retrieve a small sample from the last 7 days
now = datetime.now(timezone.utc)
seven_days_ago = now - timedelta(days=7)

params = {
    "datetime_from": seven_days_ago.isoformat(),
    "datetime_to": now.isoformat(),
    "limit": 10,
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

measurements = data.get("results", [])

print("\nMEASUREMENT API SUCCESSFUL!")
print("Metadata:", data.get("meta"))
print("Measurements retrieved:", len(measurements))

for item in measurements:

    print("\n-------------------------")

    print("Value:", item.get("value"))

    parameter = item.get("parameter", {})

    print("Parameter:", parameter.get("name"))
    print("Unit:", parameter.get("units"))

    period = item.get("period", {})

    print("Observed at:", period.get("datetimeFrom", {}).get("utc"))
    print("Quality flags:", item.get("flagInfo"))

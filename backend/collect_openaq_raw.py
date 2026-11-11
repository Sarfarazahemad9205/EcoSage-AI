
import os
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    raise ValueError("OpenAQ API key not found!")

SENSOR_ID = 12237600

url = f"https://api.openaq.org/v3/sensors/{SENSOR_ID}/measurements"

headers = {
    "X-API-Key": API_KEY
}

now = datetime.now(timezone.utc)
seven_days_ago = now - timedelta(days=7)

params = {
    "datetime_from": seven_days_ago.isoformat(),
    "datetime_to": now.isoformat(),
    "limit": 10,
    "page": 1
}

# Make API request
response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30
)

print("Status Code:", response.status_code)

response.raise_for_status()

# Create Bronze storage directory
project_root = Path(__file__).resolve().parent.parent

raw_dir = project_root / "data" / "raw" / "openaq"
raw_dir.mkdir(parents=True, exist_ok=True)

# Generate unique filename
collected_at = datetime.now(timezone.utc)

filename = (
    f"sensor_{SENSOR_ID}_"
    f"{collected_at.strftime('%Y%m%dT%H%M%SZ')}.json"
)

file_path = raw_dir / filename

# Preserve original API response bytes
file_path.write_bytes(response.content)

print("\nRAW DATA SAVED SUCCESSFULLY!")
print("File:", file_path)
print("Measurements:", len(response.json().get("results", [])))
print("Collected at:", collected_at.isoformat())

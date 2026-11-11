
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    raise ValueError("OpenAQ API key not found!")

# OpenAQ locations endpoint
url = "https://api.openaq.org/v3/locations"

headers = {
    "X-API-Key": API_KEY
}

params = {
    "iso": "IN",
    "limit": 100,
    "page": 1
}

# Send API request
response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30
)

print("Status Code:", response.status_code)

# Check response
response.raise_for_status()

data = response.json()

print("\nAPI CONNECTION SUCCESSFUL!")

print("\nMetadata:")
print(data.get("meta"))

locations = data.get("results", [])

print("\nTotal locations retrieved:", len(locations))

for location in locations[:5]:
    print("\nLocation:", location.get("name"))
    print("ID:", location.get("id"))
    print("Coordinates:", location.get("coordinates"))
    print("Locality:", location.get("locality"))

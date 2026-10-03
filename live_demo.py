from dust_sdk.client import DustClient
import os

client = DustClient(
    api_key=os.environ.get("DUST_API_KEY"),
    workspace_id=os.environ.get("DUST_WORKSPACE_ID"),
    base_url=os.environ.get("DUST_BASE_URL"),
)

import requests
import os

API_KEY = os.environ.get("DUST_API_KEY")
WORKSPACE_ID = os.environ.get("DUST_WORKSPACE_ID")
BASE_URL = os.environ.get("DUST_BASE_URL")

url = f"{BASE_URL}/api/v1/w/{WORKSPACE_ID}/analytics/export"
headers = {"Authorization": f"Bearer {API_KEY}"}
params = {
    "table": "usage_metrics",
    "startDate": "2026-09-01",
    "endDate": "2026-10-03",
    "format": "json",
}

response = requests.get(url, headers=headers, params=params)
print("Status code:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))
print("Response text:")
print(response.text)
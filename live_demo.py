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
SPACE_ID = "vlt_gXHmJTnpgyOFCSTlCnFi"
APP_ID = "fake-app-id"

url = f"{BASE_URL}/api/v1/w/{WORKSPACE_ID}/spaces/{SPACE_ID}/apps/{APP_ID}/runs"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
payload = {
    "specification_hash": "fake-hash",
    "config": {
        "model": {
            "provider_id": "anthropic",
            "model_id": "claude-sonnet-5",
            "use_cache": True,
            "use_stream": False,
        }
    },
    "inputs": [{}],
    "blocking": True,
}

response = requests.post(url, headers=headers, json=payload)
print("Status code:", response.status_code)
print(response.text)
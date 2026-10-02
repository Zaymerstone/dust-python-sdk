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
AGENT_SID = "0lXhhdzRZQ"  # твой lawyer

url = f"{BASE_URL}/api/v1/w/{WORKSPACE_ID}/assistant/agent_configurations/{AGENT_SID}"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
payload = {"userFavorite": True}

response = requests.patch(url, headers=headers, json=payload)
print("Status code:", response.status_code)
print(response.json())
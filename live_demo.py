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
DS_ID = "fake-ds-id"  # у нас нет реального data source, но попробуем узнать тип ошибки

url = f"{BASE_URL}/api/v1/w/{WORKSPACE_ID}/spaces/{SPACE_ID}/data_sources/{DS_ID}/search"
headers = {"Authorization": f"Bearer {API_KEY}"}
params = {
    "query": "test",
    "top_k": 5,
    "full_text": False,
}

response = requests.get(url, headers=headers, params=params)
print("Status code:", response.status_code)
print("Response text:", response.text)
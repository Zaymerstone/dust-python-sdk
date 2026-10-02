from dust_sdk.client import DustClient
import os

client = DustClient(
    api_key=os.environ.get("DUST_API_KEY"),
    workspace_id=os.environ.get("DUST_WORKSPACE_ID"),
    base_url=os.environ.get("DUST_BASE_URL"),
)

print("=" * 50)
print("Fetching agents from the workspace")
print("=" * 50)
agents = client.list_agents()
for agent in agents:
    print(f"  [{agent['sId']}] {agent['name']} — {agent['model']['providerId']}/{agent['model']['modelId']}")

print()
print("=" * 50)
print("Reading an existing conversation")
print("=" * 50)
conversation = client.get_conversation("3U61h9tf0Y")
print(f"Title: {conversation['title']}")
answer = client.get_last_agent_message_text(conversation)
print(f"Agent's reply: {answer}")
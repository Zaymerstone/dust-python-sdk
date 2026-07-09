import json
import requests_mock
from dust_sdk.client import DustClient, DustAPIError


def load_fixture(name: str):
    with open(f"tests/fixtures/{name}", encoding="utf-8") as f:
        return json.load(f)


def test_list_agents_returns_agent_list():
    fixture = load_fixture("agent_configurations.json")

    client = DustClient(
        api_key="fake-key",
        workspace_id="fake-workspace",
        base_url="https://eu.dust.tt",
    )

    with requests_mock.Mocker() as m:
        m.get(
            "https://eu.dust.tt/api/v1/w/fake-workspace/assistant/agent_configurations",
            json=fixture,
        )
        agents = client.list_agents()

    assert len(agents) == 10
    assert agents[0]["sId"] == "helper"
    
def test_create_conversation_returns_agent_answer():
    fixture = load_fixture("conversation_response.json")

    client = DustClient(
        api_key="fake-key",
        workspace_id="fake-workspace",
        base_url="https://eu.dust.tt",
    )

    with requests_mock.Mocker() as m:
        m.post(
            "https://eu.dust.tt/api/v1/w/fake-workspace/assistant/conversations",
            json=fixture,
        )
        conversation = client.create_conversation(
            message_content="Привет!",
            agent_sid="claude-5-sonnet",
        )

    answer = client.get_last_agent_message_text(conversation)
    assert answer is not None
    assert "помогаю" in answer
    
def test_list_spaces_returns_spaces():
    fixture = load_fixture("spaces_response.json")

    client = DustClient(
        api_key="fake-key",
        workspace_id="fake-workspace",
        base_url="https://eu.dust.tt",
    )

    with requests_mock.Mocker() as m:
        m.get(
            "https://eu.dust.tt/api/v1/w/fake-workspace/spaces",
            json=fixture,
        )
        spaces = client.list_spaces()

    assert len(spaces) == 1
    assert spaces[0]["name"] == "Company Data"
    
def test_list_data_sources_returns_data_sources():
    fixture = load_fixture("data_sources_response.json")

    client = DustClient(
        api_key="fake-key",
        workspace_id="fake-workspace",
        base_url="https://eu.dust.tt",
    )

    with requests_mock.Mocker() as m:
        m.get(
            "https://eu.dust.tt/api/v1/w/fake-workspace/spaces/fake-space/data_sources",
            json=fixture,
        )
        data_sources = client.list_data_sources(space_id="fake-space")

    assert data_sources == []
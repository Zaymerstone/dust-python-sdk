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
            message_content="Hello!",
            agent_sid="claude-5-sonnet",
        )

    answer = client.get_last_agent_message_text(conversation)
    assert answer is not None
    assert "how can i help" in answer.lower()


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


def test_get_agent_returns_single_agent():
    fixture = load_fixture("single_agent_response.json")

    client = DustClient(
        api_key="fake-key",
        workspace_id="fake-workspace",
        base_url="https://eu.dust.tt",
    )

    with requests_mock.Mocker() as m:
        m.get(
            "https://eu.dust.tt/api/v1/w/fake-workspace/assistant/agent_configurations/claude-5-sonnet",
            json=fixture,
        )
        agent = client.get_agent("claude-5-sonnet")

    assert agent["sId"] == "claude-5-sonnet"
    assert agent["model"]["providerId"] == "anthropic"


def test_get_tables_returns_table_list():
    fixture = load_fixture("tables_response.json")

    client = DustClient(
        api_key="fake-key",
        workspace_id="fake-workspace",
        base_url="https://eu.dust.tt",
    )

    with requests_mock.Mocker() as m:
        m.get(
            "https://eu.dust.tt/api/v1/w/fake-workspace/spaces/fake-space/data_sources/fake-ds/tables",
            json=fixture,
        )
        tables = client.get_tables(space_id="fake-space", data_source_id="fake-ds")

    assert len(tables) == 1
    assert tables[0]["title"] == "ROI Data"


def test_list_documents_returns_document_list():
    fixture = load_fixture("documents_response.json")

    client = DustClient(
        api_key="fake-key",
        workspace_id="fake-workspace",
        base_url="https://eu.dust.tt",
    )

    with requests_mock.Mocker() as m:
        m.get(
            "https://eu.dust.tt/api/v1/w/fake-workspace/spaces/fake-space/data_sources/fake-ds/documents",
            json=fixture,
        )
        documents = client.list_documents(space_id="fake-space", data_source_id="fake-ds")

    assert len(documents) == 1
    assert documents[0]["title"] == "Customer Support FAQ"


def test_get_conversation_returns_conversation():
    fixture = load_fixture("get_conversation_response.json")

    client = DustClient(
        api_key="fake-key",
        workspace_id="fake-workspace",
        base_url="https://eu.dust.tt",
    )

    with requests_mock.Mocker() as m:
        m.get(
            "https://eu.dust.tt/api/v1/w/fake-workspace/assistant/conversations/fake-cid",
            json=fixture,
        )
        conversation = client.get_conversation(conversation_id="fake-cid")

    assert conversation["sId"] == "3U61h9tf0Y"
    assert conversation["title"] == "Test greeting message"


def test_import_agent_creates_agent():
    fixture = load_fixture("import_agent_response.json")

    client = DustClient(
        api_key="fake-key",
        workspace_id="fake-workspace",
        base_url="https://eu.dust.tt",
    )

    with requests_mock.Mocker() as m:
        m.post(
            "https://eu.dust.tt/api/v1/w/fake-workspace/assistant/agent_configurations/import",
            json=fixture,
        )
        agent = client.import_agent(
            handle="sdk-test-agent",
            description="Test agent",
            instructions="You are a test agent.",
            editors=["test@example.com"],
            avatar_url="https://dust.tt/static/systemavatar/dust_avatar_full.png",
        )

    assert agent["sId"] == "hKKykKCnRI"
    assert agent["name"] == "sdk-test-agent"


def test_archive_agent_returns_success():
    fixture = load_fixture("archive_agent_response.json")

    client = DustClient(
        api_key="fake-key",
        workspace_id="fake-workspace",
        base_url="https://eu.dust.tt",
    )

    with requests_mock.Mocker() as m:
        m.delete(
            "https://eu.dust.tt/api/v1/w/fake-workspace/assistant/agent_configurations/fake-sid",
            json=fixture,
        )
        result = client.archive_agent(agent_sid="fake-sid")

    assert result["success"] is True
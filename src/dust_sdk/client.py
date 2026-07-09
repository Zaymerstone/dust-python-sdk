import requests


class DustAPIError(Exception):
    """Base exception for all Dust API errors."""
    pass


class DustClient:
    def __init__(self, api_key: str, workspace_id: str, base_url: str):
        """
        base_url is required with no default on purpose: Dust hosts
        separate regional infrastructure (e.g. https://eu.dust.tt
        and https://dust.tt), and passing the wrong region produces
        a confusing 'invalid_api_key_error' rather than a
        'wrong region' error. So we force the SDK user to specify
        it explicitly.
        """
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _handle_response(self, response: requests.Response) -> dict:
        """
        Shared response handling for all methods: status check and
        JSON parsing. Extracted here after this same check started
        being duplicated across 4 methods in a row (list_agents,
        create_conversation, list_spaces, list_data_sources).
        """
        if response.status_code != 200:
            raise DustAPIError(
                f"Dust API returned {response.status_code}: {response.text}"
            )
        return response.json()

    def list_agents(self) -> list[dict]:
        """Returns the list of agent configurations in the workspace."""
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/assistant/agent_configurations"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["agentConfigurations"]

    def create_conversation(
        self,
        message_content: str,
        agent_sid: str,
        username: str = "sdk-user",
        timezone: str = "UTC",
        blocking: bool = True,
    ) -> dict:
        """
        Creates a conversation and sends the first message to an agent.
        Response schema confirmed against live data on 2026-07-09
        (see NOTES.md).
        """
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/assistant/conversations"

        payload = {
            "message": {
                "content": message_content,
                "mentions": [{"configurationId": agent_sid}],
                "context": {
                    "timezone": timezone,
                    "username": username,
                },
            },
            "blocking": blocking,
        }

        response = requests.post(url, headers=self._headers(), json=payload)
        return self._handle_response(response)["conversation"]

    @staticmethod
    def get_last_agent_message_text(conversation: dict) -> str | None:
        """
        Extracts the text of the last agent message.
        conversation['content'] is a 2D array content[rank][version]:
        rank = the message's position in the conversation, version =
        edit/revision at that position. We take the latest version at
        each rank and look for the last message of type agent_message.
        """
        for rank_group in reversed(conversation["content"]):
            latest_version = rank_group[-1]
            if latest_version.get("type") == "agent_message":
                return latest_version.get("content")
        return None

    def list_spaces(self) -> list[dict]:
        """Returns the list of spaces in the workspace."""
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/spaces"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["spaces"]

    def list_data_sources(self, space_id: str) -> list[dict]:
        """Returns the list of data sources in the given space."""
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/spaces/{space_id}/data_sources"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["data_sources"]

    def get_agent(self, agent_sid: str) -> dict:
        """Returns a single agent's configuration by its sId."""
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/assistant/agent_configurations/{agent_sid}"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["agentConfiguration"]

    def get_tables(self, space_id: str, data_source_id: str) -> list[dict]:
        """
        Returns the list of tables in the given data source.

        Note: unlike the other methods, this endpoint returns a bare
        JSON array ([...]) rather than a wrapper object (e.g.
        {"data_sources": [...]}). Because of that, _handle_response()
        can't be used as-is here — it assumes response.json() is a
        dict, but here it's a list.
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/spaces/{space_id}/data_sources/{data_source_id}/tables"
        )
        response = requests.get(url, headers=self._headers())

        if response.status_code != 200:
            raise DustAPIError(
                f"Dust API returned {response.status_code}: {response.text}"
            )

        return response.json()

    def list_documents(self, space_id: str, data_source_id: str) -> list[dict]:
        """Returns the list of documents in the given data source."""
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/spaces/{space_id}/data_sources/{data_source_id}/documents"
        )
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["documents"]

    def get_conversation(self, conversation_id: str) -> dict:
        """Returns a conversation by its id, including its full message history."""
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/assistant/conversations/{conversation_id}"
        )
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["conversation"]

    def import_agent(
        self,
        handle: str,
        description: str,
        instructions: str,
        editors: list[str],
        avatar_url: str,
        model_id: str = "claude-sonnet-5",
        provider_id: str = "anthropic",
        temperature: float = 0.7,
        reasoning_effort: str = "medium",
        max_steps_per_run: int = 5,
        scope: str = "hidden",
        visualization_enabled: bool = False,
    ) -> dict:
        """
        Creates a new agent in the workspace.

        Field requirements were discovered empirically on 2026-07-09
        through a series of live 400 errors (see NOTES.md) — the
        official OpenAPI spec is inaccurate in several places:
        - avatar_url is required, though marked optional in the spec
        - editors is a list of strings (emails), not objects as shown
          in the spec
        - editors requires at least 1 element
        - generation_settings.reasoning_effort is required

        Note: unlike create_conversation, this method does NOT invoke
        a model — it's a pure write operation, so it works even on
        the Free plan despite "Programmatic access: No access".
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/assistant/agent_configurations/import"
        )

        payload = {
            "agent": {
                "handle": handle,
                "description": description,
                "scope": scope,
                "avatar_url": avatar_url,
                "max_steps_per_run": max_steps_per_run,
                "visualization_enabled": visualization_enabled,
            },
            "instructions": instructions,
            "generation_settings": {
                "model_id": model_id,
                "provider_id": provider_id,
                "temperature": temperature,
                "reasoning_effort": reasoning_effort,
            },
            "tags": [],
            "editors": editors,
            "toolset": [],
        }

        response = requests.post(url, headers=self._headers(), json=payload)
        return self._handle_response(response)["agentConfiguration"]

    def archive_agent(self, agent_sid: str) -> dict:
        """
        Archives (soft-deletes) an agent by its sId.

        Like import_agent, this operation does not invoke a model, so
        it works on the Free plan despite "Programmatic access: No
        access". Confirmed with a live call on 2026-07-09 — it worked
        on the first try, with no validation errors.
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/assistant/agent_configurations/{agent_sid}"
        )
        response = requests.delete(url, headers=self._headers())
        return self._handle_response(response)
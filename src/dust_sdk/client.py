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

        Note: this endpoint used to return a bare JSON array instead of
        a wrapper object, which required bypassing _handle_response().
        Confirmed via Dust support (2026-07-XX) that the API now wraps
        results as {"tables": [...]}, consistent with other list
        endpoints — the docs page is still showing the old shape.
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/spaces/{space_id}/data_sources/{data_source_id}/tables"
        )
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["tables"]

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
    def list_apps(self, space_id: str) -> list[dict]:
        """Returns the list of Dust Apps in the given space."""
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/spaces/{space_id}/apps"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["apps"]
    def search_data_source(
        self,
        space_id: str,
        data_source_id: str,
        query: str,
        top_k: int = 10,
        full_text: bool = False,
    ) -> list[dict]:
        """
        Performs a semantic search against a data source.

        Unlike most other read methods, this is a query parameter
        based GET request rather than a path-only one. top_k and
        full_text are required by the API but given sensible defaults
        here so callers only need to pass query in the common case.
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/spaces/{space_id}/data_sources/{data_source_id}/search"
        )
        params = {
            "query": query,
            "top_k": top_k,
            "full_text": full_text,
        }
        response = requests.get(url, headers=self._headers(), params=params)
        return self._handle_response(response)["documents"]
    
    
    def list_skills(self) -> list[dict]:
        """
        Returns the list of custom skills in the workspace.

        Confirmed live (2026-10-02) against a skill created through
        the Dust web UI moments earlier — the API reflects changes
        from the UI near-instantly.
        """
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/skills"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["skills"]
    
    def search_agents_by_name(self, query: str) -> list[dict]:
        """
        Searches agent configurations by name.

        Returns both custom agents and global/system agents (e.g.
        "dust", "helper"). Verified live on 2026-10-08.

        Note: on 2026-10-02 this endpoint was observed to omit global
        agents and to return nothing for an agent's exact full name.
        Dust confirmed the global-agent omission as a bug; neither
        behavior reproduced on 2026-10-08. If results look incomplete,
        fall back to filtering the output of list_agents().
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/assistant/agent_configurations/search"
        )
        params = {"q": query}
        response = requests.get(url, headers=self._headers(), params=params)
        return self._handle_response(response)["agentConfigurations"]
    
    def export_agent_as_yaml(self, agent_sid: str) -> str:
        """
        Exports an agent configuration as a raw YAML string.

        Unlike every other method, this endpoint returns
        Content-Type: text/yaml, not JSON — so this bypasses
        _handle_response() entirely and returns response.text
        directly, rather than parsing or unwrapping anything.

        The exported schema matches the payload shape expected by
        import_agent(), confirmed by inspecting a real export
        (2026-10-02): both use agent.handle, agent.description,
        editors, generation_settings, etc.
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/assistant/agent_configurations/{agent_sid}/export/yaml"
        )
        response = requests.get(url, headers=self._headers())

        if response.status_code != 200:
            raise DustAPIError(
                f"Dust API returned {response.status_code}: {response.text}"
            )

        return response.text
    
    def list_data_source_views(self, space_id: str) -> list[dict]:
        """
        Returns the list of data source views in the given space.

        Note: distinct from list_data_sources(). A "view" is a scoped
        window into a data source (e.g. restricted to certain parent
        folders), whereas list_data_sources() returns the underlying
        data sources themselves. Dust also has a separate, private
        version of this endpoint at /api/w/... (no /v1/) — this uses
        the public one.
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/spaces/{space_id}/data_source_views"
        )
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["dataSourceViews"]
    def update_agent_configuration(
        self,
        agent_sid: str,
        user_favorite: bool | None = None,
        handle: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        editors: list[str] | None = None,
    ) -> dict:
        """
        Updates an existing agent configuration. All fields are
        optional: only the ones provided are changed.

        Requires an API key with the admin scope (Admin > API Keys).
        A key without it returns 403 workspace_auth_error. Verified
        live on 2026-10-08 with an admin-scope key; `description`
        was confirmed to change and be restorable.

        Note: `user_favorite` is accepted (HTTP 200) but had no
        visible effect when called with an API key. Favorites are
        likely per-user, and an API key is not tied to a user.
        `handle`, `instructions` and `editors` were not tested live.
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/assistant/agent_configurations/{agent_sid}"
        )

        payload = {}
        if user_favorite is not None:
            payload["userFavorite"] = user_favorite
        if handle is not None or description is not None:
            payload["agent"] = {}
            if handle is not None:
                payload["agent"]["handle"] = handle
            if description is not None:
                payload["agent"]["description"] = description
        if instructions is not None:
            payload["instructions"] = instructions
        if editors is not None:
            payload["editors"] = editors

        response = requests.patch(url, headers=self._headers(), json=payload)
        return self._handle_response(response)["agentConfiguration"]
    def parse_mentions_in_markdown(self, markdown: str) -> str:
        """
        Parses @-mentions in markdown text and converts them into
        Dust's serialized mention format (e.g. "@dust" becomes
        ":mention[dust]{sId=dust}"). Stateless utility — doesn't
        require an existing conversation or invoke a model. Confirmed
        live (2026-10-02) with both a global agent (@dust) and a
        custom agent (@example-agent) in the same request.
        """
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/assistant/mentions/parse"
        payload = {"markdown": markdown}
        response = requests.post(url, headers=self._headers(), json=payload)
        return self._handle_response(response)["markdown"]

    def export_workspace_analytics(
        self,
        table: str,
        start_date: str,
        end_date: str,
        timezone: str = "UTC",
        format: str = "csv",
    ) -> str:
        """
        Exports workspace analytics data as a raw CSV or JSON string.

        Requires an API key with the admin scope (Admin > API Keys);
        a key without it returns 403 workspace_auth_error. Dates use
        the YYYY-MM-DD format. Verified live on 2026-10-08.

        table must be one of: usage_metrics, active_users, source,
        agents, users, skills, skill_usage, tool_usage, messages,
        feedback.

        Returns the raw response body as text, not parsed: the shape
        depends entirely on `table` and `format`, so parsing is left
        to the caller.
        """
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/analytics/export"
        params = {
            "table": table,
            "startDate": start_date,
            "endDate": end_date,
            "timezone": timezone,
            "format": format,
        }
        response = requests.get(url, headers=self._headers(), params=params)

        if response.status_code != 200:
            raise DustAPIError(
                f"Dust API returned {response.status_code}: {response.text}"
            )

        return response.text

    def get_feedbacks_for_conversation(self, conversation_id: str) -> list[dict]:
        """
        Returns feedback entries (thumbs up/down + comments) for a
        conversation.

        Does not work with workspace API keys. Live testing
        (2026-10-03) returned 401 user_authentication_required
        ("You must be logged in as a user to access this resource").
        Dust confirmed this is expected: feedback is tied to a
        specific user, and an API key is not tied to anyone, so
        there is currently no way to call this endpoint with a
        workspace API key.

        Response schema is reconstructed from Dust's official docs,
        not live-verified.
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/assistant/conversations/{conversation_id}/feedbacks"
        )
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["feedbacks"]
    
    def create_app_run(
        self,
        space_id: str,
        app_id: str,
        specification_hash: str,
        provider_id: str,
        model_id: str,
        inputs: list[dict],
        use_cache: bool = True,
        use_stream: bool = False,
        blocking: bool = True,
    ) -> dict:
        """
        Creates and executes a run for a Dust App.

        Confirmed live (2026-10-03) that this endpoint is reachable
        with a workspace API key — got app_not_found on a fake app_id
        rather than a credits or role error, unlike several other
        endpoints found this session. Full run execution wasn't
        verified against a real app, since this dev workspace has no
        apps configured. Response schema reconstructed from Dust's
        official docs.
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/spaces/{space_id}/apps/{app_id}/runs"
        )
        payload = {
            "specification_hash": specification_hash,
            "config": {
                "model": {
                    "provider_id": provider_id,
                    "model_id": model_id,
                    "use_cache": use_cache,
                    "use_stream": use_stream,
                }
            },
            "inputs": inputs,
            "blocking": blocking,
        }
        response = requests.post(url, headers=self._headers(), json=payload)
        return self._handle_response(response)["run"]
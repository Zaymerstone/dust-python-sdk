import requests


class DustAPIError(Exception):
    """Базовое исключение для всех ошибок Dust API."""
    pass


class DustClient:
    def __init__(self, api_key: str, workspace_id: str, base_url: str):
        """
        base_url обязателен и не имеет дефолта специально:
        у Dust есть отдельные регионы (например https://eu.dust.tt
        и https://dust.tt), и подстановка неверного региона даёт
        непонятную ошибку 'invalid_api_key_error', а не 'wrong region'.
        Так что заставляем пользователя SDK явно его указать.
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
        Общая обработка ответа для всех методов: проверка статуса
        и парсинг JSON. Вынесено сюда после того, как эта же проверка
        стала дублироваться в 4 разных методах подряд (list_agents,
        create_conversation, list_spaces, list_data_sources).
        """
        if response.status_code != 200:
            raise DustAPIError(
                f"Dust API вернул {response.status_code}: {response.text}"
            )
        return response.json()

    def list_agents(self) -> list[dict]:
        """Возвращает список agent configurations в workspace."""
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
        Создаёт разговор и отправляет первое сообщение агенту.
        Схема ответа подтверждена на живых данных 09.07.2026
        (см. NOTES.md)
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
        Извлекает текст последнего сообщения агента.
        conversation['content'] — двумерный массив content[rank][version]:
        rank = позиция сообщения в разговоре, version = версия (правки).
        Мы берём последнюю версию на каждом ранге и ищем последнее
        сообщение типа agent_message.
        """
        for rank_group in reversed(conversation["content"]):
            latest_version = rank_group[-1]
            if latest_version.get("type") == "agent_message":
                return latest_version.get("content")
        return None

    def list_spaces(self) -> list[dict]:
        """Возвращает список spaces (пространств) в workspace."""
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/spaces"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["spaces"]

    def list_data_sources(self, space_id: str) -> list[dict]:
        """Возвращает список data sources в указанном space."""
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/spaces/{space_id}/data_sources"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["data_sources"]
    
    def get_agent(self, agent_sid: str) -> dict:
        """Возвращает конфигурацию одного агента по его sId."""
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/assistant/agent_configurations/{agent_sid}"
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["agentConfiguration"]
    
    def get_tables(self, space_id: str, data_source_id: str) -> list[dict]:
        """
        Возвращает список таблиц в указанном data source.

        Обрати внимание: в отличие от остальных методов, этот эндпоинт
        возвращает голый JSON-массив ([...]), а не объект-обёртку
        (например {"data_sources": [...]}). Поэтому тут нельзя
        использовать _handle_response() как есть — она предполагает,
        что response.json() это dict, а тут будет list.
        """
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/spaces/{space_id}/data_sources/{data_source_id}/tables"
        )
        response = requests.get(url, headers=self._headers())

        if response.status_code != 200:
            raise DustAPIError(
                f"Dust API вернул {response.status_code}: {response.text}"
            )

        return response.json()
    
    def list_documents(self, space_id: str, data_source_id: str) -> list[dict]:
        """Возвращает список документов в указанном data source."""
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/spaces/{space_id}/data_sources/{data_source_id}/documents"
        )
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["documents"]
    
    def get_conversation(self, conversation_id: str) -> dict:
        """Возвращает разговор по его id, включая всю историю сообщений."""
        url = (
            f"{self.base_url}/api/v1/w/{self.workspace_id}"
            f"/assistant/conversations/{conversation_id}"
        )
        response = requests.get(url, headers=self._headers())
        return self._handle_response(response)["conversation"]
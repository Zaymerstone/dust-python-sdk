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

    def list_agents(self) -> list[dict]:
        """Возвращает список agent configurations в workspace."""
        url = f"{self.base_url}/api/v1/w/{self.workspace_id}/assistant/agent_configurations"
        response = requests.get(url, headers=self._headers())

        if response.status_code != 200:
            raise DustAPIError(
                f"Dust API вернул {response.status_code}: {response.text}"
            )
    

        return response.json()["agentConfigurations"]
    
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

        ⚠️ TODO: схема ответа реконструирована по документации и исходникам
        (front/types/assistant/conversation.ts), а не проверена на живом
        ответе (кредиты API исчерпаны). Свериться при первой возможности
        сделать реальный вызов.
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

        if response.status_code != 200:
            raise DustAPIError(
                f"Dust API вернул {response.status_code}: {response.text}"
            )

        return response.json()["conversation"]

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

        if response.status_code != 200:
            raise DustAPIError(
                f"Dust API вернул {response.status_code}: {response.text}"
            )

        return response.json()["spaces"]
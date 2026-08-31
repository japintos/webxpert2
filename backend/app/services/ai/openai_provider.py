from openai import OpenAI

from app.core.config import settings
from app.core.logging import logger
from app.services.ai.provider import AINotConfiguredError, AIProvider
from app.services.ai.sanitizer import sanitize_chat_messages


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = (api_key if api_key is not None else settings.OPENAI_API_KEY).strip()
        self._model = (model or settings.OPENAI_MODEL).strip() or settings.OPENAI_MODEL

    @property
    def name(self) -> str:
        return "openai"

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
    ) -> str:
        if not self._api_key:
            raise AINotConfiguredError("OPENAI_API_KEY no está configurada")

        client = OpenAI(api_key=self._api_key)
        sanitized = sanitize_chat_messages(messages)
        payload = [{"role": "system", "content": system_prompt}, *sanitized]
        logger.info("ai_request provider=openai model=%s messages=%s", self._model, len(sanitized))
        response = client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            max_tokens=420,
            messages=payload,
        )
        text = (response.choices[0].message.content or "").strip()
        logger.info("ai_response provider=openai chars=%s", len(text))
        return text

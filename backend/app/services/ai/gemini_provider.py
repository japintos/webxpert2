import httpx

from app.core.config import settings
from app.core.logging import logger
from app.services.ai.provider import AINotConfiguredError, AIProvider
from app.services.ai.sanitizer import sanitize_chat_messages

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = (api_key if api_key is not None else settings.GEMINI_API_KEY).strip()
        self._model = (model or settings.GEMINI_MODEL).strip() or settings.GEMINI_MODEL

    @property
    def name(self) -> str:
        return "gemini"

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
            raise AINotConfiguredError("GEMINI_API_KEY no está configurada")

        sanitized = sanitize_chat_messages(messages)
        contents = [
            {
                "role": "user" if item["role"] == "user" else "model",
                "parts": [{"text": item["content"]}],
            }
            for item in sanitized
        ]
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 420,
            },
        }
        url = GEMINI_URL.format(model=self._model)
        logger.info("ai_request provider=gemini model=%s messages=%s", self._model, len(sanitized))
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    url,
                    headers={
                        "x-goog-api-key": self._api_key,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as exc:
            logger.error("ai_response provider=gemini error=%s", type(exc).__name__)
            raise AINotConfiguredError("Gemini no respondió") from exc

        if response.status_code >= 400:
            detail = ""
            try:
                detail = str((response.json().get("error") or {}).get("message") or "")[:240]
            except ValueError:
                detail = ""
            logger.error("ai_response provider=gemini status=%s detail=%s", response.status_code, detail)
            raise AINotConfiguredError("Gemini rechazó la solicitud")

        data = response.json()
        text = _extract_text(data)
        logger.info("ai_response provider=gemini chars=%s", len(text))
        return text


def _extract_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = ((candidates[0].get("content") or {}).get("parts")) or []
    chunks = [str(part.get("text") or "") for part in parts]
    return "".join(chunks).strip()

from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.provider import AIProvider

PROVIDERS = ("openai", "gemini")

PROVIDER_LABELS = {
    "openai": "OpenAI",
    "gemini": "Google Gemini",
}


def normalize_provider(name: str | None) -> str:
    slug = (name or "openai").strip().lower()
    return slug if slug in PROVIDERS else "openai"


def get_ai_provider(name: str | None = None, model: str | None = None) -> AIProvider:
    """Devuelve el proveedor elegido en el panel. No acopla el engine a un vendor."""
    slug = normalize_provider(name)
    clean_model = (model or "").strip() or None
    if slug == "gemini":
        return GeminiProvider(model=clean_model)
    return OpenAIProvider(model=clean_model)

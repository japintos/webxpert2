from app.services.ai.factory import get_ai_provider, normalize_provider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider


def test_factory_defaults_to_openai():
    provider = get_ai_provider()
    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "openai"


def test_factory_selects_gemini():
    provider = get_ai_provider("gemini")
    assert isinstance(provider, GeminiProvider)
    assert provider.name == "gemini"


def test_unknown_provider_falls_back_to_openai():
    assert normalize_provider("otro") == "openai"
    assert isinstance(get_ai_provider("claude"), OpenAIProvider)

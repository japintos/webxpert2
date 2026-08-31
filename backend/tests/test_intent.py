from app.models.intent import Intent
from app.services.ai.intent_classifier import IntentClassifier


def _intent(slug: str, keywords: list[str], **kwargs) -> Intent:
    return Intent(slug=slug, name=slug, keywords=keywords, active=True, **kwargs)


def test_pricing_web_intent():
    intents = [
        _intent("pricing_web", ["cuanto sale", "precio", "pagina web", "web"], is_pricing=True, weight=1.2),
        _intent("human_agent", ["hablar con alguien"], requires_handoff=True, weight=1.5),
    ]
    match = IntentClassifier().classify("¿Cuánto sale una web?", intents, threshold=0.6)
    assert match is not None
    assert match.slug == "pricing_web"
    assert match.is_pricing


def test_ecommerce_intent():
    intents = [_intent("services_ecommerce", ["hacen tiendas", "tienda online", "ecommerce"], weight=1.2)]
    match = IntentClassifier().classify("¿Hacen tiendas online?", intents, threshold=0.5)
    assert match is not None
    assert match.slug == "services_ecommerce"


def test_human_agent_intent():
    intents = [_intent("human_agent", ["hablar con alguien", "asesor"], requires_handoff=True, weight=1.5)]
    match = IntentClassifier().classify("Quiero hablar con alguien", intents, threshold=0.6)
    assert match is not None
    assert match.requires_handoff


def test_low_confidence_returns_none():
    intents = [_intent("pricing_web", ["landing page corporativa premium"], is_pricing=True)]
    match = IntentClassifier().classify("hola", intents, threshold=0.6)
    assert match is None

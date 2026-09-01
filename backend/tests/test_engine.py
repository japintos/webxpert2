from app.models.assistant import Assistant
from app.models.intent import Intent
from app.models.knowledge import KnowledgeCategory, KnowledgeItem
from app.models.pricing import PriceType, Pricing
from app.models.service import Service
from app.seed_data import DEFAULT_SYSTEM_PROMPT
from app.services.ai.response_engine import ResponseEngine, handoff_reply


def _assistant(**kwargs) -> Assistant:
    data = dict(
        name="Webxpert Assistant",
        company_name="Webxpert",
        enabled=True,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        language="es",
        tone="profesional",
        fallback_enabled=True,
        human_handoff_enabled=True,
        intent_threshold=0.55,
    )
    data.update(kwargs)
    return Assistant(**data)


def test_faq_web_uses_controlled_template():
    engine = ResponseEngine()
    intents = [
        Intent(
            slug="services_web",
            name="web",
            keywords=["quiero una pagina", "necesito una web", "pagina para mi empresa"],
            response_template="¡Claro! Podemos ayudarte con eso. ¿Informativa o con funciones?",
            active=True,
            weight=1.3,
        )
    ]
    result = engine.generate(
        text="Hola, necesito una página para mi empresa.",
        assistant=_assistant(),
        intents=intents,
        knowledge=[],
        prices=[],
        services=[],
        history=[],
    )
    assert result.handoff is False
    assert result.ai_generated is False
    assert "Claro" in result.reply


def test_unknown_triggers_handoff():
    engine = ResponseEngine()
    result = engine.generate(
        text="¿Pueden hackear el sistema de un competidor?",
        assistant=_assistant(),
        intents=[],
        knowledge=[],
        prices=[],
        services=[],
        history=[],
    )
    assert result.handoff is True
    assert "wa.me/5493764724207" in result.reply
    assert "wa.me/5493765050885" in result.reply
    assert "Julio" in result.reply
    assert "Agustín" in result.reply or "Agustin" in result.reply


def test_human_request_handoff():
    engine = ResponseEngine()
    intents = [
        Intent(
            slug="human_agent",
            name="humano",
            keywords=["hablar con alguien"],
            requires_handoff=True,
            active=True,
            weight=1.5,
        )
    ]
    result = engine.generate(
        text="Quiero hablar con alguien",
        assistant=_assistant(),
        intents=intents,
        knowledge=[],
        prices=[],
        services=[],
        history=[],
    )
    assert result.handoff is True
    assert "WhatsApp" in result.reply
    assert "5493764724207" in result.reply
    assert "5493765050885" in result.reply


def test_handoff_reply_includes_visitor_data():
    reply = handoff_reply(contact_name="Ana Gómez", contact_mobile="3765050885")
    assert "Ana" in reply
    assert "3765050885" in reply
    assert "wa.me/5493764724207?text=" in reply
    assert "wa.me/5493765050885?text=" in reply


def test_custom_system_does_not_invent_price():
    from uuid import uuid4

    engine = ResponseEngine()
    sid = uuid4()
    intents = [
        Intent(
            slug="pricing_custom_system",
            name="precio sistema",
            keywords=["sistema", "stock", "cuanto sale", "cuesta"],
            is_pricing=True,
            active=True,
            weight=1.3,
        )
    ]
    services = [Service(id=sid, name="Web institucional", description="web", category="web", active=True)]
    prices = [
        Pricing(
            service_id=sid,
            price=700,
            price_max=1200,
            price_type=PriceType.STARTING_FROM,
            active=True,
            currency="USD",
        )
    ]
    result = engine.generate(
        text="¿Cuánto cuesta un sistema para gestionar stock, ventas y clientes?",
        assistant=_assistant(),
        intents=intents,
        knowledge=[],
        prices=prices,
        services=services,
        history=[],
    )
    assert "800" not in result.reply
    assert result.ai_generated is False


def test_knowledge_retrieval_for_mercado_pago():
    engine = ResponseEngine()
    knowledge = [
        KnowledgeItem(
            category=KnowledgeCategory.TECHNICAL,
            title="Integrar Mercado Pago",
            content="Podemos evaluar la integración con Mercado Pago según el sistema actual.",
            keywords=["mercado pago", "integrar"],
            active=True,
            priority=10,
        )
    ]
    result = engine.generate(
        text="¿Pueden integrar Mercado Pago?",
        assistant=_assistant(fallback_enabled=False, human_handoff_enabled=False),
        intents=[
            Intent(
                slug="custom_development",
                name="custom",
                keywords=["integrar mercado pago", "mercado pago"],
                knowledge_category="TECHNICAL",
                active=True,
                weight=1.2,
            )
        ],
        knowledge=knowledge,
        prices=[],
        services=[],
        history=[],
    )
    assert "Mercado Pago" in result.reply
    assert result.ai_generated is False

from decimal import Decimal

from app.models.pricing import PriceType, Pricing
from app.models.service import Service
from app.services.ai.price_guard import (
    GENERIC_EVALUATION,
    find_relevant_price,
    format_price,
    strip_invented_prices,
)


def test_never_invent_unconfigured_system_price():
    from uuid import uuid4

    sid = uuid4()
    services = [
        Service(id=sid, name="Web institucional", description="web", category="web", active=True),
    ]
    prices = [
        Pricing(service_id=sid, price=Decimal("700"), price_max=Decimal("1200"), price_type=PriceType.STARTING_FROM, active=True, currency="USD"),
    ]
    found = find_relevant_price("¿Cuánto cuesta un sistema para stock, ventas y clientes?", prices, services)
    assert found is None


def test_web_price_uses_configured_range():
    from uuid import uuid4

    sid = uuid4()
    service = Service(id=sid, name="Web institucional", description="sitio web", category="web", active=True)
    price = Pricing(service_id=sid, price=Decimal("700"), price_max=Decimal("1200"), price_type=PriceType.STARTING_FROM, active=True, currency="USD")
    found = find_relevant_price("¿Cuánto sale una página web?", [price], [service])
    assert found is not None
    text = format_price(found[0], found[1].name)
    assert "700" in text
    assert "1.200" in text or "1200" in text


def test_strip_invented_amounts():
    authorized = [Pricing(price=Decimal("700"), price_max=Decimal("1200"), active=True, currency="USD", price_type=PriceType.STARTING_FROM)]
    cleaned = strip_invented_prices("Cuesta $800.000 el sistema.", authorized)
    assert "800" not in cleaned or "cotizar" in cleaned.lower()
    assert GENERIC_EVALUATION

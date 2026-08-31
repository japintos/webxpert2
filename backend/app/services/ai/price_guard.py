import re
from decimal import Decimal

from app.models.pricing import PriceType, Pricing
from app.models.service import Service
from app.services.ai.intent_classifier import normalize_text

INVENTED_PRICE_RE = re.compile(
    r"(?:usd|u\$s|us\$|\$)\s*\d[\d.]{2,}|\d[\d.]{2,}\s*(?:usd|dolares|dólares)",
    re.IGNORECASE,
)

GENERIC_EVALUATION = (
    "Podemos desarrollar ese tipo de proyecto, pero el costo depende de las "
    "funcionalidades y del alcance. Si querés, te hago algunas preguntas para "
    "orientarte y después preparamos una cotización."
)


def format_price(item: Pricing, service_name: str | None = None) -> str:
    currency = item.currency or "USD"
    name = service_name or "este servicio"
    if item.price_type == PriceType.ON_REQUEST or item.price is None:
        extra = f" {item.description}" if item.description else ""
        return (
            f"Para {name} el valor se define según el alcance.{extra} "
            "Si querés, te oriento con algunas preguntas y armamos una cotización."
        ).strip()

    amount = _fmt(item.price, currency)
    if item.price_max is not None:
        amount = f"{_fmt(item.price, currency)} - {_fmt(item.price_max, currency)}"

    prefix = "desde " if item.price_type == PriceType.STARTING_FROM else ""
    note = (
        " Estos valores son estimativos y pueden ajustarse según alcance, "
        "prioridad y complejidad."
    )
    desc = f" {item.description}" if item.description else ""
    return f"Para {name}, el rango de referencia es {prefix}{amount}.{desc}{note}".strip()


def authorized_prices_block(prices: list[Pricing], services: list[Service]) -> str:
    by_id = {str(s.id): s for s in services}
    lines: list[str] = []
    for price in prices:
        if not price.active:
            continue
        service = by_id.get(str(price.service_id))
        if service and not service.active:
            continue
        name = service.name if service else "Servicio"
        lines.append(f"- {format_price(price, name)}")
    if not lines:
        return "No hay precios autorizados cargados. No inventes ningún número."
    return "PRECIOS AUTORIZADOS (única fuente válida):\n" + "\n".join(lines)


def find_relevant_price(
    query: str,
    prices: list[Pricing],
    services: list[Service],
) -> tuple[Pricing, Service] | None:
    normalized = normalize_text(query)
    best: tuple[int, Pricing, Service] | None = None
    for service in services:
        if not service.active:
            continue
        haystack = normalize_text(f"{service.name} {service.description} {service.category}")
        score = 0
        for token in haystack.split():
            if len(token) >= 4 and token in normalized:
                score += 1
        name = normalize_text(service.name)
        if name and name in normalized:
            score += 4
        if "ecommerce" in normalized or "e commerce" in normalized or "tienda" in normalized:
            if "commerce" in name or "tienda" in name or "e-commerce" in haystack:
                score += 4
        if any(w in normalized for w in ("web", "pagina", "página", "sitio", "institucional", "landing")):
            if any(w in name for w in ("web", "institucional", "landing", "sitio")):
                score += 3
        if any(w in normalized for w in ("sistema", "gestion", "gestión", "erp", "crm", "stock")):
            if any(w in name for w in ("sistema", "gestion", "medida", "empresarial")):
                score += 3
        if score <= 0:
            continue
        service_prices = [p for p in prices if p.active and p.service_id == service.id]
        if not service_prices:
            continue
        chosen = service_prices[0]
        if best is None or score > best[0]:
            best = (score, chosen, service)
    if not best:
        return None
    return best[1], best[2]


def strip_invented_prices(text: str, authorized: list[Pricing]) -> str:
    """Si el modelo menciona un monto que no está autorizado, se reemplaza."""
    authorized_numbers = set()
    for item in authorized:
        if item.price is not None:
            authorized_numbers.add(_plain_number(item.price))
        if item.price_max is not None:
            authorized_numbers.add(_plain_number(item.price_max))

    def replacer(match: re.Match) -> str:
        digits = re.sub(r"[^\d]", "", match.group(0))
        if digits in authorized_numbers:
            return match.group(0)
        return "un valor a cotizar según alcance"

    return INVENTED_PRICE_RE.sub(replacer, text)


def _fmt(value: Decimal | float, currency: str) -> str:
    number = f"{float(value):,.0f}".replace(",", ".")
    return f"{currency} {number}"


def _plain_number(value: Decimal | float) -> str:
    return str(int(float(value)))

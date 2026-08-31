from app.services.ai.intent_classifier import normalize_text

DEFAULT_RULES = {
    "general": 20,
    "specific": 50,
    "quote": 80,
    "hire": 90,
}

QUOTE_PHRASES = (
    "presupuesto",
    "cotizacion",
    "cotización",
    "cotizar",
    "cuanto sale",
    "cuánto sale",
    "cuanto cuesta",
    "cuánto cuesta",
    "precio",
    "necesito que me coticen",
)

HIRE_PHRASES = (
    "quiero contratar",
    "como puedo contratar",
    "cómo puedo contratar",
    "arrancar el proyecto",
    "empezar el proyecto",
    "quiero que lo hagan",
    "los contrato",
)

SPECIFIC_PHRASES = (
    "tienda online",
    "ecommerce",
    "e-commerce",
    "sistema",
    "reservas",
    "stock",
    "crm",
    "erp",
    "integrar",
    "mercado pago",
    "aplicacion",
    "aplicación",
    "app",
    "saas",
)

INTEREST_MAP = (
    (("tienda", "ecommerce", "e-commerce", "catalogo", "catálogo"), "E-commerce"),
    (("sistema", "stock", "gestion", "gestión", "crm", "erp"), "Sistema web personalizado"),
    (("app", "aplicacion", "aplicación", "movil", "móvil"), "Aplicaciones empresariales"),
    (("ia", "inteligencia", "chatbot", "asistente"), "IA"),
    (("automat", "integr"), "Automatizaciones"),
    (("landing",), "Web institucional"),
    (("web", "pagina", "página", "sitio"), "Web institucional"),
)


class LeadDetector:
    def detect(self, text: str, rules: dict | None = None) -> tuple[int, str | None]:
        cfg = {**DEFAULT_RULES, **(rules or {})}
        normalized = normalize_text(text)
        score = int(cfg["general"])
        if any(normalize_text(p) in normalized for p in SPECIFIC_PHRASES):
            score = max(score, int(cfg["specific"]))
        if any(normalize_text(p) in normalized for p in QUOTE_PHRASES):
            score = max(score, int(cfg["quote"]))
        if any(normalize_text(p) in normalized for p in HIRE_PHRASES):
            score = max(score, int(cfg["hire"]))
        return min(score, 100), self._interest(normalized)

    def _interest(self, normalized: str) -> str | None:
        for needles, label in INTEREST_MAP:
            if any(n in normalized for n in needles):
                return label
        return None

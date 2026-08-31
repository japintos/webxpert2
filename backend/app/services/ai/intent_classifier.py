import re
import unicodedata

from app.models.intent import Intent
from app.schemas.engine import IntentMatch


def normalize_text(value: str) -> str:
    value = value.lower().strip()
    value = "".join(
        ch for ch in unicodedata.normalize("NFD", value) if unicodedata.category(ch) != "Mn"
    )
    value = re.sub(r"[^\w\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


class IntentClassifier:
    """Clasificador por keywords. No usa LLM: es determinista y testeable."""

    def classify(self, text: str, intents: list[Intent], threshold: float = 0.6) -> IntentMatch | None:
        if not text.strip() or not intents:
            return None

        normalized = normalize_text(text)
        tokens = set(normalized.split())
        best: tuple[float, Intent] | None = None

        for intent in intents:
            if not intent.active:
                continue
            score = self._score(normalized, tokens, intent)
            if best is None or score > best[0]:
                best = (score, intent)

        if not best or best[0] < threshold:
            return None

        intent = best[1]
        return IntentMatch(
            slug=intent.slug,
            name=intent.name,
            confidence=round(min(best[0], 1.0), 3),
            requires_handoff=bool(intent.requires_handoff),
            is_pricing=bool(intent.is_pricing),
            response_template=intent.response_template,
            knowledge_category=intent.knowledge_category,
        )

    def _score(self, normalized: str, tokens: set[str], intent: Intent) -> float:
        keywords = [normalize_text(str(k)) for k in (intent.keywords or []) if str(k).strip()]
        if not keywords:
            return 0.0

        hits = 0.0
        for keyword in keywords:
            if " " in keyword:
                if keyword in normalized:
                    hits += 1.6
            elif keyword in tokens:
                hits += 1.0
        raw = hits / max(len(keywords) * 0.45, 1.0)
        return min(raw * float(intent.weight or 1.0), 1.0)

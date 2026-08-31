from app.models.knowledge import KnowledgeItem
from app.schemas.engine import KnowledgeHit
from app.services.ai.intent_classifier import normalize_text


class KnowledgeRetriever:
    """Búsqueda por keywords + coincidencia en título/contenido.

    Abstracción lista para reemplazar por embeddings/RAG sin cambiar el engine.
    """

    def search(
        self,
        query: str,
        items: list[KnowledgeItem],
        *,
        category: str | None = None,
        limit: int = 4,
    ) -> list[KnowledgeHit]:
        normalized = normalize_text(query)
        tokens = set(normalized.split())
        scored: list[KnowledgeHit] = []

        for item in items:
            if not item.active:
                continue
            if category and item.category.value != category:
                continue
            score = self._score(normalized, tokens, item)
            if score <= 0:
                continue
            scored.append(
                KnowledgeHit(
                    id=str(item.id),
                    category=item.category.value,
                    title=item.title,
                    content=item.content,
                    score=score,
                )
            )

        scored.sort(key=lambda hit: (hit.score, next(
            (i.priority for i in items if str(i.id) == hit.id), 0
        )), reverse=True)
        return scored[:limit]

    def _score(self, normalized: str, tokens: set[str], item: KnowledgeItem) -> float:
        score = 0.0
        title = normalize_text(item.title)
        content = normalize_text(item.content)
        keywords = [normalize_text(str(k)) for k in (item.keywords or []) if str(k).strip()]

        for keyword in keywords:
            if " " in keyword and keyword in normalized:
                score += 2.5
            elif keyword in tokens:
                score += 1.8

        for token in tokens:
            if len(token) < 3:
                continue
            if token in title:
                score += 0.8
            elif token in content:
                score += 0.25

        if title and title in normalized:
            score += 2.0
        return score

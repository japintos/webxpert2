from app.models.message import Message, MessageDirection

HISTORY_WINDOW = 10
SUMMARIZE_AFTER = 16


class ConversationSummarizer:
    """Fase 1: ventana de mensajes. Fase 2: resumen LLM si el historial crece."""

    def build_history(self, messages: list[Message], limit: int = HISTORY_WINDOW) -> list[dict[str, str]]:
        recent = [m for m in messages if m.message_type == "text"][-limit:]
        history: list[dict[str, str]] = []
        for item in recent:
            role = "user" if item.direction == MessageDirection.INBOUND else "assistant"
            history.append({"role": role, "content": item.content[:1500]})
        return history

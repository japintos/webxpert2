from difflib import SequenceMatcher
from urllib.parse import quote

from app.core.logging import logger
from app.models.assistant import Assistant
from app.models.intent import Intent
from app.models.knowledge import KnowledgeItem
from app.models.message import Message, MessageDirection
from app.models.pricing import Pricing
from app.models.service import Service
from app.schemas.engine import EngineResult, IntentMatch, KnowledgeHit
from app.services.ai.intent_classifier import IntentClassifier, normalize_text
from app.services.ai.factory import get_ai_provider
from app.services.ai.knowledge_retriever import KnowledgeRetriever
from app.services.ai.lead_detector import LeadDetector
from app.services.ai.price_guard import (
    GENERIC_EVALUATION,
    authorized_prices_block,
    find_relevant_price,
    format_price,
    strip_invented_prices,
)
from app.services.ai.provider import AINotConfiguredError, AIProvider
from app.services.ai.summarizer import ConversationSummarizer

WHATSAPP_AGENTS = (
    ("Julio Pintos", "5493764724207"),
    ("Agustín Burgos", "5493765050885"),
)


def handoff_reply(*, contact_name: str | None = None, contact_mobile: str | None = None) -> str:
    full_name = (contact_name or "").strip()
    phone = (contact_mobile or "").strip()
    lines = [
        "Perfecto. Podés continuar ahora mismo por WhatsApp con un especialista de Webxpert.",
        "Elegí con quién querés hablar (se abre la app):",
        "",
    ]
    for agent_name, number in WHATSAPP_AGENTS:
        first = agent_name.split()[0]
        parts = [f"Hola {first}, te contacto desde el chat de Webxpert."]
        if full_name:
            parts.append(f"Soy {full_name}.")
        if phone:
            parts.append(f"Mi teléfono es {phone}.")
        url = f"https://wa.me/{number}?text={quote(' '.join(parts))}"
        lines.append(f"- [WhatsApp de {agent_name}]({url})")
    return "\n".join(lines)


HANDOFF_REPLY = handoff_reply()

FALLBACK_REPLY = (
    "No quiero darte información incorrecta sobre eso. "
    "Puedo derivarte con un especialista de Webxpert para resolverlo bien. ¿Te parece?"
)

HUMAN_PHRASES = (
    "hablar con alguien",
    "hablar con una persona",
    "asesor",
    "humano",
    "operador",
    "agente",
    "llamar",
)

RESTATE_PHRASES = (
    "decime de nuevo",
    "decime otra vez",
    "repetime",
    "repeti",
    "repite",
    "podes repetir",
    "podes repetirme",
    "explicame de nuevo",
    "no te entendi",
)

FOLLOWUP_QUESTIONS = (
    "¿Querés que te oriente con el siguiente paso?",
    "Si me contás un poco más el alcance, te preciso mejor.",
    "¿Lo vemos por el lado del presupuesto, los plazos o las funciones?",
    "¿Hay alguna funcionalidad puntual que te importe más?",
)

DUPLICATE_RATIO = 0.92


def previous_outbound_texts(history: list[Message]) -> list[str]:
    texts: list[str] = []
    for item in history:
        if getattr(item, "message_type", "text") not in (None, "text"):
            continue
        direction = item.direction
        if direction != MessageDirection.OUTBOUND and str(direction) != MessageDirection.OUTBOUND.value:
            continue
        content = (item.content or "").strip()
        if content:
            texts.append(content)
    return texts


def replies_are_equivalent(left: str, right: str) -> bool:
    a = normalize_text(left)
    b = normalize_text(right)
    if not a or not b:
        return False
    if a == b:
        return True
    return SequenceMatcher(None, a, b).ratio() >= DUPLICATE_RATIO


def is_duplicate_reply(reply: str, history: list[Message]) -> bool:
    return any(replies_are_equivalent(reply, previous) for previous in previous_outbound_texts(history))


def user_asks_restatement(text: str) -> bool:
    normalized = normalize_text(text)
    return any(normalize_text(phrase) in normalized for phrase in RESTATE_PHRASES)


def vary_authorized_reply(reply: str, history: list[Message]) -> str:
    base = reply.rstrip()
    for followup in FOLLOWUP_QUESTIONS:
        candidate = f"{base}\n\n{followup}"
        if not is_duplicate_reply(candidate, history):
            return candidate
    return f"{base}\n\n¿Hay algo más del proyecto que quieras contarme?"


class ResponseEngine:
    def __init__(
        self,
        classifier: IntentClassifier | None = None,
        retriever: KnowledgeRetriever | None = None,
        lead_detector: LeadDetector | None = None,
        summarizer: ConversationSummarizer | None = None,
        provider: AIProvider | None = None,
    ) -> None:
        self.classifier = classifier or IntentClassifier()
        self.retriever = retriever or KnowledgeRetriever()
        self.lead_detector = lead_detector or LeadDetector()
        self.summarizer = summarizer or ConversationSummarizer()
        self.provider = provider

    def generate(
        self,
        *,
        text: str,
        assistant: Assistant,
        intents: list[Intent],
        knowledge: list[KnowledgeItem],
        prices: list[Pricing],
        services: list[Service],
        history: list[Message],
        contact_name: str | None = None,
        contact_mobile: str | None = None,
    ) -> EngineResult:
        lead_score, interest = self.lead_detector.detect(text)
        match = self.classifier.classify(text, intents, threshold=assistant.intent_threshold)
        wants_human = self._wants_human(text, match)

        logger.info(
            "intent_detected slug=%s confidence=%s",
            match.slug if match else None,
            match.confidence if match else 0,
        )

        if wants_human and assistant.human_handoff_enabled:
            logger.info("human_handoff reason=user_or_intent")
            return EngineResult(
                reply=handoff_reply(contact_name=contact_name, contact_mobile=contact_mobile),
                intent=match.slug if match else "human_agent",
                confidence=match.confidence if match else 1.0,
                ai_generated=False,
                handoff=True,
                lead_score=max(lead_score, 80),
                service_interest=interest,
            )

        hits = self.retriever.search(
            text,
            knowledge,
            category=match.knowledge_category if match else None,
        )
        logger.info("knowledge_retrieved hits=%s", len(hits))

        result: EngineResult | None = None
        if match and match.is_pricing:
            result = self._pricing_reply(text, match, prices, services, lead_score, interest)
        elif match and match.response_template:
            result = EngineResult(
                reply=match.response_template.strip(),
                intent=match.slug,
                confidence=match.confidence,
                ai_generated=False,
                handoff=False,
                lead_score=lead_score,
                service_interest=interest,
            )
        elif match and hits:
            result = EngineResult(
                reply=hits[0].content,
                intent=match.slug,
                confidence=match.confidence,
                ai_generated=False,
                handoff=False,
                lead_score=lead_score,
                service_interest=interest,
            )
        elif assistant.fallback_enabled and (hits or match):
            try:
                reply = self._llm_reply(text, assistant, hits, prices, services, history)
                reply = strip_invented_prices(reply, prices)
                result = EngineResult(
                    reply=reply,
                    intent=match.slug if match else "llm_fallback",
                    confidence=match.confidence if match else 0.4,
                    ai_generated=True,
                    handoff=False,
                    lead_score=lead_score,
                    service_interest=interest,
                )
            except AINotConfiguredError:
                if hits:
                    result = EngineResult(
                        reply=hits[0].content,
                        intent=match.slug if match else "knowledge",
                        confidence=match.confidence if match else 0.45,
                        ai_generated=False,
                        handoff=False,
                        lead_score=lead_score,
                        service_interest=interest,
                    )

        if result is None:
            if assistant.human_handoff_enabled:
                logger.info("human_handoff reason=unknown")
                return EngineResult(
                    reply=handoff_reply(contact_name=contact_name, contact_mobile=contact_mobile),
                    intent=match.slug if match else "unknown",
                    confidence=match.confidence if match else 0.0,
                    ai_generated=False,
                    handoff=True,
                    lead_score=lead_score,
                    service_interest=interest,
                )
            return EngineResult(
                reply=FALLBACK_REPLY,
                intent="unknown",
                confidence=0.0,
                ai_generated=False,
                handoff=False,
                lead_score=lead_score,
                service_interest=interest,
            )

        return self._avoid_repeat(
            result,
            text=text,
            assistant=assistant,
            match=match,
            hits=hits,
            prices=prices,
            services=services,
            history=history,
        )

    def _pricing_reply(
        self,
        text: str,
        match: IntentMatch,
        prices: list[Pricing],
        services: list[Service],
        lead_score: int,
        interest: str | None,
    ) -> EngineResult:
        found = find_relevant_price(text, prices, services)
        if found:
            price, service = found
            reply = format_price(price, service.name)
            if match.response_template:
                reply = f"{match.response_template}\n\n{reply}"
        else:
            reply = GENERIC_EVALUATION
        return EngineResult(
            reply=reply,
            intent=match.slug,
            confidence=match.confidence,
            ai_generated=False,
            handoff=False,
            lead_score=max(lead_score, 80),
            service_interest=interest or (found[1].name if found else None),
        )

    def _knowledge_snippet(
        self, text: str, knowledge: list[KnowledgeItem], category: str | None
    ) -> list[KnowledgeHit]:
        return self.retriever.search(text, knowledge, category=category, limit=1)

    def _avoid_repeat(
        self,
        result: EngineResult,
        *,
        text: str,
        assistant: Assistant,
        match: IntentMatch | None,
        hits: list[KnowledgeHit],
        prices: list[Pricing],
        services: list[Service],
        history: list[Message],
    ) -> EngineResult:
        if result.handoff or "wa.me/" in result.reply.lower():
            return result
        if user_asks_restatement(text):
            return result
        if not is_duplicate_reply(result.reply, history):
            return result

        if not (match and match.is_pricing):
            for hit in hits:
                if not is_duplicate_reply(hit.content, history):
                    logger.info("duplicate_reply_avoided strategy=knowledge")
                    return result.model_copy(update={"reply": hit.content, "ai_generated": False})

        if assistant.fallback_enabled:
            try:
                reply = self._llm_reply(
                    text,
                    assistant,
                    hits,
                    prices,
                    services,
                    history,
                    temperature=0.45,
                    extra_instruction=self._no_repeat_instruction(history),
                )
                reply = strip_invented_prices(reply, prices)
                if reply.strip() and not is_duplicate_reply(reply, history):
                    logger.info("duplicate_reply_avoided strategy=llm")
                    return result.model_copy(update={"reply": reply, "ai_generated": True})
            except AINotConfiguredError:
                pass

        logger.info("duplicate_reply_avoided strategy=vary")
        return result.model_copy(update={"reply": vary_authorized_reply(result.reply, history)})

    def _no_repeat_instruction(self, history: list[Message]) -> str:
        previous = previous_outbound_texts(history)[-8:]
        if not previous:
            return ""
        listed = "\n---\n".join(previous)
        return (
            "En esta conversación YA enviaste las respuestas de abajo. "
            "Está prohibido copiarlas o mandar un texto casi idéntico. "
            "Reformulá con información autorizada, profundizá o hacé una pregunta útil. "
            "Si mencionás precios, usá exactamente los números autorizados; no inventes otros.\n\n"
            f"RESPUESTAS PREVIAS (no copiar):\n{listed}"
        )

    def _llm_reply(
        self,
        text: str,
        assistant: Assistant,
        hits: list[KnowledgeHit],
        prices: list[Pricing],
        services: list[Service],
        history: list[Message],
        *,
        temperature: float = 0.25,
        extra_instruction: str = "",
    ) -> str:
        knowledge_block = "\n\n".join(f"### {h.title}\n{h.content}" for h in hits) or "Sin información adicional."
        prices_block = authorized_prices_block(prices, services)
        extra = f"\n\n{extra_instruction}" if extra_instruction else ""
        system = (
            f"{assistant.system_prompt}\n\n"
            "Usá ÚNICAMENTE la información autorizada de abajo. "
            "Si no alcanza, reconocelo y ofrecé derivar a un especialista. "
            "Nunca inventes precios, plazos ni funcionalidades."
            f"{extra}\n\n"
            f"CONOCIMIENTO AUTORIZADO:\n{knowledge_block}\n\n"
            f"{prices_block}"
        )
        messages = self.summarizer.build_history(history)
        messages.append({"role": "user", "content": text})
        provider = self.provider or get_ai_provider(assistant.llm_provider, assistant.llm_model)
        return provider.generate(system_prompt=system, messages=messages, temperature=temperature)

    def _wants_human(self, text: str, match: IntentMatch | None) -> bool:
        if match and (match.requires_handoff or match.slug == "human_agent"):
            return True
        normalized = normalize_text(text)
        return any(normalize_text(p) in normalized for p in HUMAN_PHRASES)

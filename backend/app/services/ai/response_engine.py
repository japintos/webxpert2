from app.core.logging import logger
from app.models.assistant import Assistant
from app.models.intent import Intent
from app.models.knowledge import KnowledgeItem
from app.models.message import Message
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

HANDOFF_REPLY = (
    "Para este caso específico prefiero que uno de nuestros especialistas lo revise. "
    "Si querés, derivo la conversación a nuestro equipo."
)

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
                reply=HANDOFF_REPLY,
                intent=match.slug if match else "human_agent",
                confidence=match.confidence if match else 1.0,
                ai_generated=False,
                handoff=True,
                lead_score=max(lead_score, 80),
                service_interest=interest,
            )

        if match and match.is_pricing:
            return self._pricing_reply(text, match, prices, services, lead_score, interest)

        if match and match.response_template:
            return EngineResult(
                reply=match.response_template.strip(),
                intent=match.slug,
                confidence=match.confidence,
                ai_generated=False,
                handoff=False,
                lead_score=lead_score,
                service_interest=interest,
            )

        hits = self.retriever.search(
            text,
            knowledge,
            category=match.knowledge_category if match else None,
        )
        logger.info("knowledge_retrieved hits=%s", len(hits))

        if match and hits:
            reply = hits[0].content
            return EngineResult(
                reply=reply,
                intent=match.slug,
                confidence=match.confidence,
                ai_generated=False,
                handoff=False,
                lead_score=lead_score,
                service_interest=interest,
            )

        if assistant.fallback_enabled and (hits or match):
            try:
                reply = self._llm_reply(text, assistant, hits, prices, services, history)
                reply = strip_invented_prices(reply, prices)
                return EngineResult(
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
                    return EngineResult(
                        reply=hits[0].content,
                        intent=match.slug if match else "knowledge",
                        confidence=match.confidence if match else 0.45,
                        ai_generated=False,
                        handoff=False,
                        lead_score=lead_score,
                        service_interest=interest,
                    )

        if assistant.human_handoff_enabled:
            logger.info("human_handoff reason=unknown")
            return EngineResult(
                reply=HANDOFF_REPLY,
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

    def _llm_reply(
        self,
        text: str,
        assistant: Assistant,
        hits: list[KnowledgeHit],
        prices: list[Pricing],
        services: list[Service],
        history: list[Message],
    ) -> str:
        knowledge_block = "\n\n".join(f"### {h.title}\n{h.content}" for h in hits) or "Sin información adicional."
        prices_block = authorized_prices_block(prices, services)
        system = (
            f"{assistant.system_prompt}\n\n"
            "Usá ÚNICAMENTE la información autorizada de abajo. "
            "Si no alcanza, reconocelo y ofrecé derivar a un especialista. "
            "Nunca inventes precios, plazos ni funcionalidades.\n\n"
            f"CONOCIMIENTO AUTORIZADO:\n{knowledge_block}\n\n"
            f"{prices_block}"
        )
        messages = self.summarizer.build_history(history)
        messages.append({"role": "user", "content": text})
        provider = self.provider or get_ai_provider(assistant.llm_provider, assistant.llm_model)
        return provider.generate(system_prompt=system, messages=messages, temperature=0.25)

    def _wants_human(self, text: str, match: IntentMatch | None) -> bool:
        if match and (match.requires_handoff or match.slug == "human_agent"):
            return True
        normalized = normalize_text(text)
        return any(normalize_text(p) in normalized for p in HUMAN_PHRASES)

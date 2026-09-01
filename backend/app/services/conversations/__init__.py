from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.logging import logger
from app.models.assistant import Assistant
from app.models.contact import Contact
from app.models.conversation import Conversation, ConversationStatus
from app.models.intent import Intent
from app.models.knowledge import KnowledgeItem
from app.models.lead import Lead, LeadStatus
from app.models.message import Message, MessageDirection
from app.models.pricing import Pricing
from app.models.service import Service
from app.models.tenant import Tenant
from app.schemas.engine import EngineResult
from app.services.ai.response_engine import ResponseEngine

WELCOME_AFTER_INTAKE = (
    "Gracias, {first_name}. Ya tengo tus datos. "
    "Contame qué necesitás: una web, un e-commerce, un sistema o una idea a medida."
)


class ContactRequiredError(Exception):
    pass


class MessageProcessor:
    def __init__(
        self,
        db: Session,
        engine: ResponseEngine | None = None,
    ) -> None:
        self.db = db
        self.engine = engine or ResponseEngine()

    def process_inbound(
        self,
        *,
        phone: str,
        text: str,
        name: str | None = None,
        last_name: str | None = None,
        mobile: str | None = None,
        external_id: str | None = None,
        tenant_slug: str = "webxpert",
        channel: str = "web",
        require_profile: bool = False,
    ) -> tuple[Conversation, Message, Message | None, EngineResult | None]:
        logger.info("incoming_message channel=%s", channel)
        tenant = self._tenant(tenant_slug)
        assistant = self._assistant(tenant.id)
        contact = self._contact(tenant.id, phone, name, last_name=last_name, mobile=mobile)
        if require_profile and not self._contact_ready(contact):
            raise ContactRequiredError()
        conversation = self._open_conversation(tenant.id, contact.id, assistant.id, channel)

        if external_id:
            existing = self.db.scalar(select(Message).where(Message.external_id == external_id))
            if existing:
                return conversation, existing, None, None

        inbound = Message(
            conversation_id=conversation.id,
            tenant_id=tenant.id,
            direction=MessageDirection.INBOUND,
            sender="contact",
            content=text[:4000],
            message_type="text",
            external_id=external_id,
        )
        self.db.add(inbound)
        conversation.last_message_at = datetime.now(timezone.utc)
        self.db.flush()

        if not assistant.enabled or not conversation.bot_enabled:
            self.db.commit()
            self.db.refresh(conversation)
            return conversation, inbound, None, None

        result = self.engine.generate(
            text=text,
            assistant=assistant,
            intents=list(self.db.scalars(select(Intent).where(Intent.tenant_id == tenant.id))),
            knowledge=list(self.db.scalars(select(KnowledgeItem).where(KnowledgeItem.tenant_id == tenant.id))),
            prices=list(self.db.scalars(select(Pricing).where(Pricing.tenant_id == tenant.id))),
            services=list(self.db.scalars(select(Service).where(Service.tenant_id == tenant.id))),
            history=list(
                self.db.scalars(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at)
                )
            ),
            contact_name=contact.name,
            contact_mobile=contact.mobile,
        )

        inbound.intent = result.intent
        inbound.confidence = result.confidence
        self._upsert_lead(tenant.id, contact.id, conversation.id, result)

        if result.handoff:
            conversation.status = ConversationStatus.WAITING_HUMAN
            conversation.bot_enabled = False
            logger.info("human_handoff conversation=%s", conversation.id)

        outbound = Message(
            conversation_id=conversation.id,
            tenant_id=tenant.id,
            direction=MessageDirection.OUTBOUND,
            sender="assistant",
            content=result.reply,
            message_type="text",
            intent=result.intent,
            confidence=result.confidence,
            ai_generated=result.ai_generated,
        )
        self.db.add(outbound)
        conversation.last_message_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(conversation)
        self.db.refresh(inbound)
        self.db.refresh(outbound)

        return conversation, inbound, outbound, result

    def register_intake(
        self,
        *,
        phone: str,
        first_name: str,
        last_name: str,
        mobile: str,
        tenant_slug: str = "webxpert",
        channel: str = "web",
    ) -> tuple[Conversation, Message]:
        tenant = self._tenant(tenant_slug)
        assistant = self._assistant(tenant.id)
        full_name = f"{first_name} {last_name}".strip()
        contact = self._contact(
            tenant.id,
            phone,
            full_name,
            last_name=last_name,
            mobile=mobile,
        )
        conversation = self._open_conversation(tenant.id, contact.id, assistant.id, channel)
        outbound = Message(
            conversation_id=conversation.id,
            tenant_id=tenant.id,
            direction=MessageDirection.OUTBOUND,
            sender="assistant",
            content=WELCOME_AFTER_INTAKE.format(first_name=first_name),
            message_type="text",
            ai_generated=False,
        )
        self.db.add(outbound)
        conversation.last_message_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(conversation)
        self.db.refresh(outbound)
        return conversation, outbound

    def send_human_reply(self, conversation: Conversation, content: str, user_id: UUID | None) -> Message:
        outbound = Message(
            conversation_id=conversation.id,
            tenant_id=conversation.tenant_id,
            direction=MessageDirection.OUTBOUND,
            sender="human",
            content=content[:4000],
            message_type="text",
            ai_generated=False,
        )
        self.db.add(outbound)
        conversation.last_message_at = datetime.now(timezone.utc)
        if user_id:
            conversation.assigned_to = user_id
            if conversation.status == ConversationStatus.WAITING_HUMAN:
                conversation.status = ConversationStatus.HUMAN
                conversation.bot_enabled = False
        self.db.commit()
        self.db.refresh(outbound)
        return outbound

    def _tenant(self, slug: str) -> Tenant:
        tenant = self.db.scalar(select(Tenant).where(Tenant.slug == slug))
        if not tenant:
            raise RuntimeError("Tenant Webxpert no encontrado. Ejecutá el seed.")
        return tenant

    def _assistant(self, tenant_id: UUID) -> Assistant:
        assistant = self.db.scalar(select(Assistant).where(Assistant.tenant_id == tenant_id))
        if not assistant:
            raise RuntimeError("Assistant no encontrado. Ejecutá el seed.")
        return assistant

    def _contact(
        self,
        tenant_id: UUID,
        phone: str,
        name: str | None,
        last_name: str | None = None,
        mobile: str | None = None,
    ) -> Contact:
        contact = self.db.scalar(
            select(Contact).where(Contact.tenant_id == tenant_id, Contact.phone == phone)
        )
        if contact:
            if name:
                contact.name = name
            if last_name:
                contact.last_name = last_name
            if mobile:
                contact.mobile = mobile
            return contact
        contact = Contact(
            tenant_id=tenant_id,
            phone=phone,
            name=name or None,
            last_name=last_name or None,
            mobile=mobile or None,
        )
        self.db.add(contact)
        self.db.flush()
        return contact

    def _contact_ready(self, contact: Contact) -> bool:
        return bool((contact.name or "").strip() and (contact.last_name or "").strip() and (contact.mobile or "").strip())

    def _open_conversation(
        self, tenant_id: UUID, contact_id: UUID, assistant_id: UUID, channel: str = "web"
    ) -> Conversation:
        conversation = self.db.scalar(
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.contact_id == contact_id,
                Conversation.status != ConversationStatus.CLOSED,
            )
            .order_by(Conversation.last_message_at.desc())
        )
        if conversation:
            return conversation
        conversation = Conversation(
            tenant_id=tenant_id,
            contact_id=contact_id,
            assistant_id=assistant_id,
            status=ConversationStatus.BOT,
            channel=channel or "web",
            bot_enabled=True,
        )
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def _upsert_lead(
        self, tenant_id: UUID, contact_id: UUID, conversation_id: UUID, result: EngineResult
    ) -> None:
        if result.lead_score < 50 and not result.handoff:
            return
        lead = self.db.scalar(select(Lead).where(Lead.conversation_id == conversation_id))
        status = LeadStatus.QUALIFIED if result.lead_score >= 80 else LeadStatus.NEW
        if lead:
            lead.score = max(lead.score, result.lead_score)
            if result.service_interest:
                lead.service_interest = result.service_interest
            if lead.score >= 80 and lead.status == LeadStatus.NEW:
                lead.status = LeadStatus.QUALIFIED
            logger.info("lead_detected id=%s score=%s", lead.id, lead.score)
            return
        lead = Lead(
            tenant_id=tenant_id,
            contact_id=contact_id,
            conversation_id=conversation_id,
            status=status,
            score=result.lead_score,
            service_interest=result.service_interest,
        )
        self.db.add(lead)
        logger.info("lead_detected new score=%s", result.lead_score)


def conversation_with_contact(db: Session, conversation_id: UUID) -> Conversation | None:
    return db.scalar(
        select(Conversation)
        .options(joinedload(Conversation.contact), joinedload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )

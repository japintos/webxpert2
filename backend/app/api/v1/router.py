from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import apply_updates, get_current_user, get_db
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password
from app.models.assistant import Assistant
from app.models.contact import Contact
from app.models.conversation import Conversation, ConversationStatus
from app.models.knowledge import KnowledgeCategory, KnowledgeItem
from app.models.lead import Lead, LeadStatus
from app.models.message import Message
from app.models.pricing import PriceType, Pricing
from app.models.service import Service
from app.models.user import User
from app.schemas import (
    AIStatus,
    AssistantOut,
    AssistantUpdate,
    ContactOut,
    ConversationDetailOut,
    ConversationOut,
    ConversationUpdate,
    DashboardStats,
    KnowledgeCreate,
    KnowledgeOut,
    KnowledgeUpdate,
    LeadCreate,
    LeadOut,
    LeadUpdate,
    LoginRequest,
    MessageCreate,
    MessageOut,
    PricingCreate,
    PricingOut,
    PricingUpdate,
    ServiceCreate,
    ServiceOut,
    ServiceUpdate,
    SimulateInbound,
    TokenResponse,
    UserOut,
)
from app.services.ai.factory import PROVIDER_LABELS, PROVIDERS, normalize_provider
from app.services.conversations import MessageProcessor

router = APIRouter()


def _knowledge_out(item: KnowledgeItem) -> KnowledgeOut:
    return KnowledgeOut.model_validate(item).model_copy(update={"category": item.category.value})


def _pricing_out(item: Pricing) -> PricingOut:
    return PricingOut(
        id=item.id,
        service_id=item.service_id,
        price=float(item.price) if item.price is not None else None,
        price_max=float(item.price_max) if item.price_max is not None else None,
        currency=item.currency,
        price_type=item.price_type.value,
        description=item.description,
        active=item.active,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _conversation_out(item: Conversation, last_message: str | None = None, lead_score: int | None = None) -> ConversationOut:
    return ConversationOut(
        id=item.id,
        contact_id=item.contact_id,
        assistant_id=item.assistant_id,
        status=item.status.value,
        channel=item.channel,
        bot_enabled=item.bot_enabled,
        assigned_to=item.assigned_to,
        started_at=item.started_at,
        last_message_at=item.last_message_at,
        contact=ContactOut.model_validate(item.contact) if item.contact else None,
        last_message=last_message,
        lead_score=lead_score,
        needs_human=item.status == ConversationStatus.WAITING_HUMAN,
    )


@router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_access_token(user_id=user.id, email=user.email, tenant_id=user.tenant_id)
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    tenant_id = user.tenant_id
    conversations_today = db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == tenant_id, Conversation.started_at >= start
        )
    ) or 0
    new_leads = db.scalar(
        select(func.count(Lead.id)).where(Lead.tenant_id == tenant_id, Lead.status == LeadStatus.NEW)
    ) or 0
    qualified_leads = db.scalar(
        select(func.count(Lead.id)).where(Lead.tenant_id == tenant_id, Lead.status == LeadStatus.QUALIFIED)
    ) or 0
    ai_handled = db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == tenant_id, Conversation.status == ConversationStatus.BOT
        )
    ) or 0
    handed_off = db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == tenant_id,
            Conversation.status.in_([ConversationStatus.WAITING_HUMAN, ConversationStatus.HUMAN]),
        )
    ) or 0
    return DashboardStats(
        conversations_today=conversations_today,
        new_leads=new_leads,
        qualified_leads=qualified_leads,
        ai_handled=ai_handled,
        handed_off=handed_off,
    )


@router.get("/assistant", response_model=AssistantOut)
def get_assistant(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    assistant = db.scalar(select(Assistant).where(Assistant.tenant_id == user.tenant_id))
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant no encontrado")
    return assistant


@router.patch("/assistant", response_model=AssistantOut)
def patch_assistant(
    payload: AssistantUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    assistant = db.scalar(select(Assistant).where(Assistant.tenant_id == user.tenant_id))
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant no encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "llm_provider" in data and data["llm_provider"] is not None:
        data["llm_provider"] = normalize_provider(data["llm_provider"])
    if "llm_model" in data:
        assistant.llm_model = (data.pop("llm_model") or "").strip() or None
    apply_updates(assistant, data)
    db.commit()
    db.refresh(assistant)
    return assistant


@router.get("/ai/status", response_model=AIStatus)
def ai_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    assistant = db.scalar(select(Assistant).where(Assistant.tenant_id == user.tenant_id))
    return AIStatus(
        active_provider=normalize_provider(assistant.llm_provider if assistant else "openai"),
        providers=[
            {
                "id": "openai",
                "label": PROVIDER_LABELS["openai"],
                "configured": settings.openai_configured,
                "default_model": settings.OPENAI_MODEL,
            },
            {
                "id": "gemini",
                "label": PROVIDER_LABELS["gemini"],
                "configured": settings.gemini_configured,
                "default_model": settings.GEMINI_MODEL,
            },
        ],
    )


@router.get("/knowledge", response_model=list[KnowledgeOut])
def list_knowledge(
    q: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(KnowledgeItem).where(KnowledgeItem.tenant_id == user.tenant_id)
    if category:
        stmt = stmt.where(KnowledgeItem.category == KnowledgeCategory(category))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(KnowledgeItem.title.ilike(like) | KnowledgeItem.content.ilike(like))
    stmt = stmt.order_by(KnowledgeItem.priority.desc(), KnowledgeItem.updated_at.desc())
    return [_knowledge_out(item) for item in db.scalars(stmt)]


@router.post("/knowledge", response_model=KnowledgeOut, status_code=201)
def create_knowledge(
    payload: KnowledgeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        category = KnowledgeCategory(payload.category)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Categoría inválida") from exc
    item = KnowledgeItem(
        tenant_id=user.tenant_id,
        category=category,
        title=payload.title,
        content=payload.content,
        keywords=payload.keywords,
        active=payload.active,
        priority=payload.priority,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _knowledge_out(item)


@router.patch("/knowledge/{item_id}", response_model=KnowledgeOut)
def patch_knowledge(
    item_id: UUID,
    payload: KnowledgeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(KnowledgeItem, item_id)
    if not item or item.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="No encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "category" in data and data["category"] is not None:
        try:
            data["category"] = KnowledgeCategory(data["category"])
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Categoría inválida") from exc
    apply_updates(item, data)
    db.commit()
    db.refresh(item)
    return _knowledge_out(item)


@router.delete("/knowledge/{item_id}", status_code=204)
def delete_knowledge(
    item_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    item = db.get(KnowledgeItem, item_id)
    if not item or item.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()


@router.get("/services", response_model=list[ServiceOut])
def list_services(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.scalars(select(Service).where(Service.tenant_id == user.tenant_id)))


@router.post("/services", response_model=ServiceOut, status_code=201)
def create_service(
    payload: ServiceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    item = Service(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/services/{item_id}", response_model=ServiceOut)
def patch_service(
    item_id: UUID,
    payload: ServiceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Service, item_id)
    if not item or item.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="No encontrado")
    apply_updates(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/services/{item_id}", status_code=204)
def delete_service(item_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Service, item_id)
    if not item or item.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()


@router.get("/pricing", response_model=list[PricingOut])
def list_pricing(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.scalars(select(Pricing).where(Pricing.tenant_id == user.tenant_id))
    return [_pricing_out(item) for item in items]


@router.post("/pricing", response_model=PricingOut, status_code=201)
def create_pricing(
    payload: PricingCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    service = db.get(Service, payload.service_id)
    if not service or service.tenant_id != user.tenant_id:
        raise HTTPException(status_code=422, detail="Servicio inválido")
    try:
        price_type = PriceType(payload.price_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Tipo de precio inválido") from exc
    item = Pricing(
        tenant_id=user.tenant_id,
        service_id=payload.service_id,
        price=payload.price,
        price_max=payload.price_max,
        currency=payload.currency,
        price_type=price_type,
        description=payload.description,
        active=payload.active,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _pricing_out(item)


@router.patch("/pricing/{item_id}", response_model=PricingOut)
def patch_pricing(
    item_id: UUID,
    payload: PricingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Pricing, item_id)
    if not item or item.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="No encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "price_type" in data and data["price_type"] is not None:
        data["price_type"] = PriceType(data["price_type"])
    apply_updates(item, data)
    db.commit()
    db.refresh(item)
    return _pricing_out(item)


@router.delete("/pricing/{item_id}", status_code=204)
def delete_pricing(item_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Pricing, item_id)
    if not item or item.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()


@router.get("/contacts", response_model=list[ContactOut])
def list_contacts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.scalars(select(Contact).where(Contact.tenant_id == user.tenant_id)))


@router.get("/leads", response_model=list[LeadOut])
def list_leads(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.scalars(
        select(Lead)
        .options(joinedload(Lead.contact))
        .where(Lead.tenant_id == user.tenant_id)
        .order_by(Lead.created_at.desc())
    ).unique()
    return [
        LeadOut(
            id=item.id,
            contact_id=item.contact_id,
            conversation_id=item.conversation_id,
            status=item.status.value,
            score=item.score,
            service_interest=item.service_interest,
            notes=item.notes,
            created_at=item.created_at,
            updated_at=item.updated_at,
            contact=ContactOut.model_validate(item.contact) if item.contact else None,
        )
        for item in items
    ]


@router.post("/leads", response_model=LeadOut, status_code=201)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = Lead(
        tenant_id=user.tenant_id,
        contact_id=payload.contact_id,
        conversation_id=payload.conversation_id,
        status=LeadStatus(payload.status),
        score=payload.score,
        service_interest=payload.service_interest,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return LeadOut(
        id=item.id,
        contact_id=item.contact_id,
        conversation_id=item.conversation_id,
        status=item.status.value,
        score=item.score,
        service_interest=item.service_interest,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.patch("/leads/{item_id}", response_model=LeadOut)
def patch_lead(
    item_id: UUID,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Lead, item_id)
    if not item or item.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="No encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        data["status"] = LeadStatus(data["status"])
    apply_updates(item, data)
    db.commit()
    db.refresh(item)
    return LeadOut(
        id=item.id,
        contact_id=item.contact_id,
        conversation_id=item.conversation_id,
        status=item.status.value,
        score=item.score,
        service_interest=item.service_interest,
        notes=item.notes,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = list(
        db.scalars(
            select(Conversation)
            .options(joinedload(Conversation.contact))
            .where(Conversation.tenant_id == user.tenant_id)
            .order_by(Conversation.last_message_at.desc())
        ).unique()
    )
    result: list[ConversationOut] = []
    for item in items:
        last = db.scalar(
            select(Message)
            .where(Message.conversation_id == item.id)
            .order_by(Message.created_at.desc())
        )
        lead = db.scalar(select(Lead).where(Lead.conversation_id == item.id))
        result.append(_conversation_out(item, last.content if last else None, lead.score if lead else None))
    return result


@router.get("/conversations/{item_id}", response_model=ConversationDetailOut)
def get_conversation(item_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.scalar(
        select(Conversation)
        .options(joinedload(Conversation.contact), joinedload(Conversation.messages))
        .where(Conversation.id == item_id, Conversation.tenant_id == user.tenant_id)
    )
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    lead = db.scalar(select(Lead).where(Lead.conversation_id == item.id))
    last = item.messages[-1].content if item.messages else None
    base = _conversation_out(item, last, lead.score if lead else None)
    return ConversationDetailOut(
        **base.model_dump(),
        messages=[
            MessageOut(
                id=m.id,
                conversation_id=m.conversation_id,
                direction=m.direction.value,
                sender=m.sender,
                content=m.content,
                message_type=m.message_type,
                intent=m.intent,
                confidence=m.confidence,
                ai_generated=m.ai_generated,
                created_at=m.created_at,
            )
            for m in item.messages
        ],
    )


@router.patch("/conversations/{item_id}", response_model=ConversationOut)
def patch_conversation(
    item_id: UUID,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Conversation, item_id)
    if not item or item.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="No encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        data["status"] = ConversationStatus(data["status"])
        if data["status"] == ConversationStatus.HUMAN:
            data["bot_enabled"] = False
            data["assigned_to"] = user.id
        if data["status"] == ConversationStatus.BOT:
            data["bot_enabled"] = True
    apply_updates(item, data)
    db.commit()
    db.refresh(item)
    item.contact = db.get(Contact, item.contact_id)
    return _conversation_out(item)


@router.post("/conversations/{item_id}/messages", response_model=MessageOut, status_code=201)
def post_human_message(
    item_id: UUID,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Conversation, item_id)
    if not item or item.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="No encontrado")
    message = MessageProcessor(db).send_human_reply(item, payload.content, user.id)
    return MessageOut(
        id=message.id,
        conversation_id=message.conversation_id,
        direction=message.direction.value,
        sender=message.sender,
        content=message.content,
        message_type=message.message_type,
        intent=message.intent,
        confidence=message.confidence,
        ai_generated=message.ai_generated,
        created_at=message.created_at,
    )


@router.post("/simulate/inbound")
def simulate_inbound(
    payload: SimulateInbound,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    processor = MessageProcessor(db)
    conversation, inbound, outbound, result = processor.process_inbound(
        phone=payload.phone,
        text=payload.text,
        name=payload.name,
        channel="web",
    )
    return {
        "conversation_id": str(conversation.id),
        "inbound_id": str(inbound.id),
        "outbound": outbound.content if outbound else None,
        "intent": result.intent if result else inbound.intent,
        "confidence": result.confidence if result else inbound.confidence,
        "handoff": result.handoff if result else False,
        "lead_score": result.lead_score if result else None,
        "bot_enabled": conversation.bot_enabled,
        "status": conversation.status.value,
    }

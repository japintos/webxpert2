from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.core.security import create_visitor_token, decode_visitor_token
from app.db.session import get_db
from app.models.conversation import Conversation, ConversationStatus
from app.models.message import Message
from app.schemas import ChatSendRequest, MessageOut
from app.services.conversations import ContactRequiredError, MessageProcessor

router = APIRouter()


def _visitor_phone(visitor_id: str) -> str:
    clean = visitor_id.strip()
    if len(clean) < 8 or len(clean) > 48:
        raise HTTPException(status_code=422, detail="Visitante inválido")
    if any(ch in clean for ch in (" ", "/", "\\", "\n")):
        raise HTTPException(status_code=422, detail="Visitante inválido")
    return f"web:{clean}"


def _normalize_mobile(raw: str) -> str:
    cleaned = "".join(ch for ch in raw.strip() if ch.isdigit() or ch == "+")
    if len(cleaned) < 8 or len(cleaned) > 20:
        raise HTTPException(status_code=422, detail="Teléfono inválido")
    return cleaned


def _message_out(message: Message) -> dict:
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
    ).model_dump(mode="json")


def _load_from_token(db: Session, token: str) -> Conversation:
    try:
        payload = decode_visitor_token(token)
        conversation_id = UUID(str(payload["cid"]))
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Sesión de chat inválida") from exc
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conversation


def _visible_messages(db: Session, conversation: Conversation) -> list[Message]:
    if conversation.status == ConversationStatus.CLOSED:
        return []
    return list(
        db.scalars(select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at))
    )


def _chat_payload(*, visitor_id: str, conversation: Conversation, messages: list[Message], handoff: bool = False) -> dict:
    return {
        "visitor_id": visitor_id,
        "visitor_token": create_visitor_token(visitor_id=visitor_id, conversation_id=conversation.id),
        "conversation_id": str(conversation.id),
        "status": conversation.status.value,
        "bot_enabled": conversation.bot_enabled,
        "handoff": handoff,
        "messages": [_message_out(item) for item in messages],
    }


@router.post("/chat/messages")
@limiter.limit("30/minute")
def send_chat_message(request: Request, payload: ChatSendRequest, db: Session = Depends(get_db)):
    visitor_id = payload.visitor_id.strip()
    processor = MessageProcessor(db)
    phone = _visitor_phone(visitor_id)

    if payload.intake:
        conversation, _outbound = processor.register_intake(
            phone=phone,
            first_name=(payload.first_name or "").strip(),
            last_name=(payload.last_name or "").strip(),
            mobile=_normalize_mobile(payload.contact_phone or ""),
            channel="web",
        )
        return _chat_payload(
            visitor_id=visitor_id,
            conversation=conversation,
            messages=_visible_messages(db, conversation),
        )

    try:
        conversation, _inbound, _outbound, result = processor.process_inbound(
            phone=phone,
            text=payload.text.strip(),
            name=" ".join(
                part for part in ((payload.first_name or "").strip(), (payload.last_name or "").strip()) if part
            )
            or (payload.name or "").strip()
            or None,
            last_name=(payload.last_name or "").strip() or None,
            mobile=_normalize_mobile(payload.contact_phone) if payload.contact_phone else None,
            channel="web",
            require_profile=True,
        )
    except ContactRequiredError as exc:
        raise HTTPException(
            status_code=422,
            detail="Para empezar, necesitamos tu nombre, apellido y teléfono.",
        ) from exc

    return _chat_payload(
        visitor_id=visitor_id,
        conversation=conversation,
        messages=_visible_messages(db, conversation),
        handoff=bool(result.handoff) if result else False,
    )


@router.get("/chat/messages")
@limiter.limit("60/minute")
def list_chat_messages(
    request: Request,
    visitor_token: str = Query(...),
    db: Session = Depends(get_db),
):
    conversation = _load_from_token(db, visitor_token)
    messages = _visible_messages(db, conversation)
    return {
        "conversation_id": str(conversation.id),
        "status": conversation.status.value,
        "bot_enabled": conversation.bot_enabled,
        "messages": [_message_out(item) for item in messages],
    }

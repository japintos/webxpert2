from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.core.security import create_visitor_token, decode_visitor_token
from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas import ChatSendRequest, MessageOut
from app.services.conversations import MessageProcessor

router = APIRouter()


def _visitor_phone(visitor_id: str) -> str:
    clean = visitor_id.strip()
    if len(clean) < 8 or len(clean) > 48:
        raise HTTPException(status_code=422, detail="Visitante inválido")
    if any(ch in clean for ch in (" ", "/", "\\", "\n")):
        raise HTTPException(status_code=422, detail="Visitante inválido")
    return f"web:{clean}"


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


@router.post("/chat/messages")
@limiter.limit("30/minute")
def send_chat_message(request: Request, payload: ChatSendRequest, db: Session = Depends(get_db)):
    visitor_id = payload.visitor_id.strip()
    processor = MessageProcessor(db)
    conversation, _inbound, _outbound, result = processor.process_inbound(
        phone=_visitor_phone(visitor_id),
        text=payload.text.strip(),
        name=(payload.name or "Visitante web").strip(),
        channel="web",
    )

    token = create_visitor_token(visitor_id=visitor_id, conversation_id=conversation.id)
    messages = list(
        db.scalars(select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at))
    )
    return {
        "visitor_id": visitor_id,
        "visitor_token": token,
        "conversation_id": str(conversation.id),
        "status": conversation.status.value,
        "bot_enabled": conversation.bot_enabled,
        "handoff": bool(result.handoff) if result else False,
        "messages": [_message_out(item) for item in messages],
    }


@router.get("/chat/messages")
@limiter.limit("60/minute")
def list_chat_messages(
    request: Request,
    visitor_token: str = Query(...),
    db: Session = Depends(get_db),
):
    conversation = _load_from_token(db, visitor_token)
    messages = list(
        db.scalars(select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at))
    )
    return {
        "conversation_id": str(conversation.id),
        "status": conversation.status.value,
        "bot_enabled": conversation.bot_enabled,
        "messages": [_message_out(item) for item in messages],
    }

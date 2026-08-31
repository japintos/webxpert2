import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ConversationStatus(str, enum.Enum):
    BOT = "BOT"
    WAITING_HUMAN = "WAITING_HUMAN"
    HUMAN = "HUMAN"
    CLOSED = "CLOSED"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    contact_id: Mapped[UUID] = mapped_column(ForeignKey("contacts.id"), index=True)
    assistant_id: Mapped[UUID] = mapped_column(ForeignKey("assistants.id"), index=True)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, native_enum=False),
        default=ConversationStatus.BOT,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(32), default="web")
    bot_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_to: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    contact = relationship("Contact", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    leads = relationship("Lead", back_populates="conversation")

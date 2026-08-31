from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Assistant(Base):
    __tablename__ = "assistants"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(160), default="Webxpert Assistant")
    company_name: Mapped[str] = mapped_column(String(160), default="Webxpert")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16), default="es")
    tone: Mapped[str] = mapped_column(String(255), default="Profesional, amable, claro, directo, natural, argentino")
    fallback_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    human_handoff_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    intent_threshold: Mapped[float] = mapped_column(Float, default=0.6)
    llm_provider: Mapped[str] = mapped_column(String(32), default="openai")
    llm_model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tenant = relationship("Tenant", back_populates="assistants")

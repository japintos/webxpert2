from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str
    tenant_id: UUID
    is_active: bool


class AssistantOut(ORMModel):
    id: UUID
    tenant_id: UUID
    name: str
    company_name: str
    enabled: bool
    system_prompt: str
    language: str
    tone: str
    fallback_enabled: bool
    human_handoff_enabled: bool
    intent_threshold: float
    llm_provider: str = "openai"
    llm_model: str | None = None
    created_at: datetime
    updated_at: datetime


class AssistantUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    company_name: str | None = Field(default=None, max_length=160)
    enabled: bool | None = None
    system_prompt: str | None = None
    language: str | None = Field(default=None, max_length=16)
    tone: str | None = Field(default=None, max_length=255)
    fallback_enabled: bool | None = None
    human_handoff_enabled: bool | None = None
    intent_threshold: float | None = Field(default=None, ge=0.1, le=0.99)
    llm_provider: str | None = Field(default=None, max_length=32)
    llm_model: str | None = Field(default=None, max_length=80)


class KnowledgeCreate(BaseModel):
    category: str
    title: str = Field(min_length=2, max_length=255)
    content: str = Field(min_length=2)
    keywords: list[str] = Field(default_factory=list)
    active: bool = True
    priority: int = 0


class KnowledgeUpdate(BaseModel):
    category: str | None = None
    title: str | None = Field(default=None, max_length=255)
    content: str | None = None
    keywords: list[str] | None = None
    active: bool | None = None
    priority: int | None = None


class KnowledgeOut(ORMModel):
    id: UUID
    category: str
    title: str
    content: str
    keywords: list
    active: bool
    priority: int
    created_at: datetime
    updated_at: datetime


class ServiceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str
    active: bool = True
    starting_price: str | None = None
    price_visible: bool = True
    category: str = "general"


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    description: str | None = None
    active: bool | None = None
    starting_price: str | None = None
    price_visible: bool | None = None
    category: str | None = None


class ServiceOut(ORMModel):
    id: UUID
    name: str
    description: str
    active: bool
    starting_price: str | None
    price_visible: bool
    category: str
    created_at: datetime
    updated_at: datetime


class PricingCreate(BaseModel):
    service_id: UUID
    price: float | None = None
    price_max: float | None = None
    currency: str = "USD"
    price_type: str = "STARTING_FROM"
    description: str | None = None
    active: bool = True


class PricingUpdate(BaseModel):
    service_id: UUID | None = None
    price: float | None = None
    price_max: float | None = None
    currency: str | None = None
    price_type: str | None = None
    description: str | None = None
    active: bool | None = None


class PricingOut(ORMModel):
    id: UUID
    service_id: UUID
    price: float | None
    price_max: float | None
    currency: str
    price_type: str
    description: str | None
    active: bool
    created_at: datetime
    updated_at: datetime


class ContactOut(ORMModel):
    id: UUID
    phone: str
    name: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime


class MessageOut(ORMModel):
    id: UUID
    conversation_id: UUID
    direction: str
    sender: str
    content: str
    message_type: str
    intent: str | None
    confidence: float | None
    ai_generated: bool
    created_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class ConversationOut(ORMModel):
    id: UUID
    contact_id: UUID
    assistant_id: UUID
    status: str
    channel: str
    bot_enabled: bool
    assigned_to: UUID | None
    started_at: datetime
    last_message_at: datetime
    contact: ContactOut | None = None
    last_message: str | None = None
    lead_score: int | None = None
    needs_human: bool = False


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = Field(default_factory=list)


class ConversationUpdate(BaseModel):
    status: str | None = None
    bot_enabled: bool | None = None
    assigned_to: UUID | None = None


class LeadOut(ORMModel):
    id: UUID
    contact_id: UUID
    conversation_id: UUID
    status: str
    score: int
    service_interest: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    contact: ContactOut | None = None


class LeadCreate(BaseModel):
    contact_id: UUID
    conversation_id: UUID
    status: str = "NEW"
    score: int = Field(default=0, ge=0, le=100)
    service_interest: str | None = None
    notes: str | None = None


class LeadUpdate(BaseModel):
    status: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    service_interest: str | None = None
    notes: str | None = None


class SimulateInbound(BaseModel):
    phone: str = Field(min_length=6, max_length=64)
    name: str | None = Field(default=None, max_length=160)
    text: str = Field(min_length=1, max_length=4000)


class ChatSendRequest(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=64)
    visitor_token: str | None = None
    name: str | None = Field(default=None, max_length=160)
    text: str = Field(min_length=1, max_length=4000)


class ChatHistoryQuery(BaseModel):
    visitor_token: str


class DashboardStats(BaseModel):
    conversations_today: int
    new_leads: int
    qualified_leads: int
    ai_handled: int
    handed_off: int


class AIProviderInfo(BaseModel):
    id: str
    label: str
    configured: bool
    default_model: str


class AIStatus(BaseModel):
    active_provider: str
    providers: list[AIProviderInfo]

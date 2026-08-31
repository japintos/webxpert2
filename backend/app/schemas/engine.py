from pydantic import BaseModel, Field


class IntentMatch(BaseModel):
    slug: str
    name: str
    confidence: float = Field(ge=0, le=1)
    requires_handoff: bool = False
    is_pricing: bool = False
    response_template: str | None = None
    knowledge_category: str | None = None


class KnowledgeHit(BaseModel):
    id: str
    category: str
    title: str
    content: str
    score: float


class EngineResult(BaseModel):
    reply: str
    intent: str | None = None
    confidence: float | None = None
    ai_generated: bool = False
    handoff: bool = False
    lead_score: int = 0
    service_interest: str | None = None

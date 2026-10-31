from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Recommendation(StrEnum):
    APPROVE = "approve"
    REVIEW = "review"
    REJECT = "reject"


class AssessmentStatus(StrEnum):
    AUTO_APPROVED = "auto_approved"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProcurementRequest(BaseModel):
    requester: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=2, max_length=100)
    vendor: str = Field(min_length=2, max_length=150)
    amount_eur: float = Field(gt=0, le=10_000_000)
    description: str = Field(min_length=10, max_length=2_000)
    data_classification: DataClassification = DataClassification.INTERNAL
    contains_personal_data: bool = False
    single_source: bool = False
    urgent: bool = False

    @field_validator("requester", "department", "vendor", "description")
    @classmethod
    def normalise_text(cls, value: str) -> str:
        return " ".join(value.strip().split())


class PolicyEvidence(BaseModel):
    source: str
    section: str
    excerpt: str
    relevance: float = Field(ge=0, le=1)


class AgentStep(BaseModel):
    agent: str
    summary: str
    flags: list[str] = Field(default_factory=list)
    duration_ms: float = Field(ge=0)


class Assessment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    request: ProcurementRequest
    status: AssessmentStatus
    risk_level: RiskLevel
    recommendation: Recommendation
    approval_route: list[str]
    reasons: list[str]
    executive_summary: str
    policy_evidence: list[PolicyEvidence]
    agent_trace: list[AgentStep]
    model_mode: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None
    reviewer: str | None = None
    review_note: str | None = None


class ReviewDecision(BaseModel):
    approved: bool
    reviewer: str = Field(min_length=2, max_length=100)
    note: str = Field(min_length=3, max_length=1_000)

    @field_validator("reviewer", "note")
    @classmethod
    def normalise_text(cls, value: str) -> str:
        return " ".join(value.strip().split())


class HealthResponse(BaseModel):
    status: str
    ai_provider: str

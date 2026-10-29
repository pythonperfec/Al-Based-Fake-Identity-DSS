from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

CheckName = Literal[
    "ocr", "mrz_checksum", "expiry", "date_consistency",
    "format", "watchlist", "tamper", "face"
]
CheckState = Literal["passed", "flagged", "not_performed", "could_not_verify"]
ScreeningStatus = Literal["queued", "processing", "completed", "incomplete", "failed"]
RiskLevel = Literal["low", "review_required", "high", "incomplete"]
FindingSeverity = Literal["low", "medium", "high"]
FindingType = Literal[
    "MRZ_CHECKSUM_MISMATCH", "EXPIRED_DOCUMENT", "DATE_INCONSISTENCY",
    "INVALID_FORMAT", "WATCHLIST_MATCH", "ELA_REGION_ANOMALY",
    "METADATA_SOFTWARE_TAG", "NOISE_INCONSISTENCY"
]
ReviewDecision = Literal["confirmed", "overridden", "escalated"]
DocumentType = Literal["passport", "national_id"]
AuditAction = Literal[
    "SCREENING_SUBMITTED", "INSPECTION_COMPLETED", "IMAGE_VIEWED",
    "FINDINGS_VIEWED", "HUMAN_REVIEW_RECORDED"
]


class ErrorEnvelope(BaseModel):
    error: str
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "screening-api"
    version: str = "0.1.0"
    timestamp: datetime


class CheckItem(BaseModel):
    name: CheckName
    state: CheckState
    detail: str


class FindingResponse(BaseModel):
    finding_id: str
    type: FindingType
    severity: FindingSeverity
    reason: str
    source: str
    evidence_ref: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FindingsListResponse(BaseModel):
    screening_id: str
    findings: List[FindingResponse]


class ReviewCreate(BaseModel):
    decision: ReviewDecision
    notes: str = Field(..., min_length=10)


class ReviewResponse(BaseModel):
    review_id: str
    screening_id: str
    decision: ReviewDecision
    notes: str
    reviewed_by: str
    reviewed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScreeningCreateResponse(BaseModel):
    screening_id: str
    status: ScreeningStatus
    document_type: DocumentType
    created_at: datetime


class ScreeningSummary(BaseModel):
    screening_id: str
    status: ScreeningStatus
    risk_level: Optional[RiskLevel] = None
    risk_score: Optional[float] = None
    requires_human_review: bool = False
    document_type: DocumentType
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScreeningsListResponse(BaseModel):
    total: int
    items: List[ScreeningSummary]


class ScreeningDetail(BaseModel):
    screening_id: str
    status: ScreeningStatus
    risk_level: Optional[RiskLevel] = None
    risk_score: Optional[float] = None
    requires_human_review: bool = False
    document_type: DocumentType
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    checks: List[CheckItem] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    review: Optional[ReviewResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventResponse(BaseModel):
    event_id: str
    timestamp: datetime
    actor: str
    action: AuditAction
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class CaseAuditResponse(BaseModel):
    case_id: str
    events: List[AuditEventResponse]


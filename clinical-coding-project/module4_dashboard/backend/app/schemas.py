"""
Pydantic schemas for the Human-in-the-Loop Dashboard and Evaluation API.
Fully typed to match both the frontend contract (Design Medical Coding Dashboard)
and the paper evaluation contracts (docs/interfaces.md).
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- Paper baseline interface schemas (docs/interfaces.md) ---

class CodeResult(BaseModel):
    code: str
    probability: float
    verification_status: str  # accepted | rejected | needs_review
    reject_reason: Optional[str] = None
    evidence_span: str


class DocumentReview(BaseModel):
    document_id: str
    results: List[CodeResult]


class ReviewAction(BaseModel):
    document_id: str
    code: str
    human_action: str  # confirmed | overturned | added
    review_time_seconds: float = 0.0


# --- Frontend Dashboard API Schemas (types.ts) ---

class UserSchema(BaseModel):
    id: str
    name: str
    email: str
    role: str  # "Medical Coder" | "Administrator" | "Physician"
    active: bool = True


class LoginRequest(BaseModel):
    username: str
    password: str
    role: str = "Medical Coder"


class LoginResponse(BaseModel):
    token: str
    user: UserSchema


class AttentionSpan(BaseModel):
    startIdx: int
    endIdx: int
    weight: float


class PredictedCode(BaseModel):
    id: str
    code: str
    description: str
    confidence: int  # 0-100
    verificationStatus: str  # "VERIFIED" | "PARENT CODE" | "UNVERIFIED"
    attentionSpans: List[AttentionSpan] = []
    supportingEvidence: str
    rejectReason: Optional[str] = None
    userAction: Optional[str] = None  # "confirmed" | "overridden" | "rejected"
    userReason: Optional[str] = None
    overrideCode: Optional[str] = None
    overrideReason: Optional[str] = None


class SubmittedCode(BaseModel):
    code: str
    action: str  # "confirmed" | "overridden"
    replacesCode: Optional[str] = None
    reason: Optional[str] = None


class CaseItem(BaseModel):
    id: str
    patientId: str
    submittedAt: str
    status: str  # "Processing" | "Pending Review" | "Completed"
    averageConfidence: int
    dischargeText: str
    words: List[str]
    predictedCodes: List[PredictedCode]
    submittedToBilling: Optional[bool] = False
    submittedCodes: Optional[List[SubmittedCode]] = None
    analysisSource: Optional[str] = None
    analysisSourceLabel: Optional[str] = None


class AnalyzeRequest(BaseModel):
    document_id: Optional[str] = None
    patient_id: Optional[str] = None
    text: str


class ConfirmRequest(BaseModel):
    coderName: str = "Medical Coder"


class RejectRequest(BaseModel):
    reason: str
    coderName: str = "Medical Coder"


class OverrideRequest(BaseModel):
    newCode: str
    reason: str
    coderName: str = "Medical Coder"


class SubmitRequest(BaseModel):
    coderName: str = "Medical Coder"


class AuditEntry(BaseModel):
    id: str
    timestamp: str
    coderName: str
    caseId: str
    action: str  # "Predicted" | "Confirmed" | "Overridden" | "Submitted"
    codeAffected: str
    oldValue: str
    newValue: str


class SystemSettings(BaseModel):
    auto_accept_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    review_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    model_name: str = "emilyalsentzer/Bio_ClinicalBERT (base encoder; no task checkpoint)"
    ontology_version: str = "ICD-10-CM 2026"
    sliding_window_size: int = 512
    sliding_stride: int = 256

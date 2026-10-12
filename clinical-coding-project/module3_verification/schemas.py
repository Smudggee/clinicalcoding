"""Data contracts for Module 3 (see docs/interfaces.md)."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class VerificationResult:
    code: str
    probability: float
    verification_status: str  # "accepted" | "rejected" | "needs_review"
    reject_reason: Optional[str]
    evidence_span: str

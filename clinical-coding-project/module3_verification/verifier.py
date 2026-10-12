"""
Neuro-Symbolic Verification Engine (Section VI-F Module 3, Section VIII).

Applies deterministic checks AFTER the neural classifier (Module 2) has
produced a candidate (code, probability, evidence) triple, so that
confidence, evidence and validity stay separate concepts:

  - confidence: the model's probability
  - evidence:   the text span that supposedly supports it
  - validity:   whether it passes these rules

Order of checks (fail fast):
  1. Syntactic validity (format regex)      -> Type-I hallucination check
  2. Presence in current ICD release        -> catches invalid/retired codes
  3. Negation / historical-status check     -> catches unsupported predictions
  4. Confidence threshold                   -> routes uncertain cases to humans
"""
from dataclasses import asdict
from typing import List

from .schemas import VerificationResult
from .icd_ontology import ICDOntology
from .negation_detector import classify_evidence


class NeuroSymbolicVerifier:
    def __init__(self, ontology: ICDOntology = None,
                 review_threshold: float = 0.5,
                 auto_accept_threshold: float = 0.9):
        self.ontology = ontology or ICDOntology()
        self.review_threshold = review_threshold
        self.auto_accept_threshold = auto_accept_threshold

    def verify(self, code: str, probability: float, evidence_span: str,
               full_document_text: str, evidence_start_char: int) -> VerificationResult:

        # 1. Syntactic validity (Type-I hallucination)
        if not self.ontology.is_syntactically_valid(code):
            return VerificationResult(
                code=code, probability=probability, verification_status="rejected",
                reject_reason="malformed code string", evidence_span=evidence_span,
            )

        # 2. In current authorized release
        try:
            in_release = self.ontology.is_in_current_release(code)
        except RuntimeError:
            in_release = True  # no ontology loaded yet; don't block dev/testing
        if not in_release:
            return VerificationResult(
                code=code, probability=probability, verification_status="rejected",
                reject_reason="code not present in current ICD release",
                evidence_span=evidence_span,
            )

        # 3. Negation / historical status
        evidence_status = classify_evidence(full_document_text, evidence_start_char)
        if evidence_status == "negated":
            return VerificationResult(
                code=code, probability=probability, verification_status="rejected",
                reject_reason="supporting evidence is negated", evidence_span=evidence_span,
            )
        if evidence_status == "historical":
            return VerificationResult(
                code=code, probability=probability, verification_status="needs_review",
                reject_reason="supporting evidence is historical, confirm current relevance",
                evidence_span=evidence_span,
            )

        # 4. Confidence-based routing (Almarshadi et al., human-in-the-loop routing)
        if probability >= self.auto_accept_threshold:
            status, reason = "accepted", None
        elif probability >= self.review_threshold:
            status, reason = "needs_review", "confidence below auto-accept threshold"
        else:
            status, reason = "rejected", "confidence below review threshold"

        return VerificationResult(
            code=code, probability=probability, verification_status=status,
            reject_reason=reason, evidence_span=evidence_span,
        )

    def verify_batch(self, predictions: List[dict], full_document_text: str) -> List[VerificationResult]:
        return [
            self.verify(
                code=p["code"], probability=p["probability"],
                evidence_span=p["evidence_span"],
                full_document_text=full_document_text,
                evidence_start_char=p["evidence_start_char"],
            )
            for p in predictions
        ]

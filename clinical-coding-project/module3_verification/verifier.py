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
import math
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
        if (
        isinstance(probability, bool)
        or not isinstance(probability, (int, float))
        or not math.isfinite(probability)
        or not 0.0 <= probability <= 1.0
    ):
                return VerificationResult(
            code=str(code),
            probability=probability,
            verification_status="rejected",
            reject_reason="probability must be a finite number between 0 and 1",
            evidence_span=str(evidence_span),
        )
            
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
            return VerificationResult(
                code=code,
                probability=probability,
                verification_status="needs_review",
                reject_reason="authorized ICD code list is unavailable",
                evidence_span=evidence_span,
            )

        
        # 3. Negation / historical status
        if (
            not isinstance(full_document_text, str)
            or not isinstance(evidence_start_char, int)
            or isinstance(evidence_start_char, bool)
            or not 0 <= evidence_start_char < len(full_document_text)
        ):
            return VerificationResult(
                code=code,
                probability=probability,
                verification_status="needs_review",
                reject_reason="invalid evidence text or character offset",
                evidence_span=evidence_span,
            )
        evidence_status = classify_evidence(full_document_text, evidence_start_char)
        if (
            not isinstance(evidence_span, str)
            or not evidence_span.strip()
            or full_document_text[
                evidence_start_char:
                evidence_start_char + len(evidence_span)
            ] != evidence_span
        ):
            return VerificationResult(
                code=code,
                probability=probability,
                verification_status="needs_review",
                reject_reason="evidence span does not match document text",
                evidence_span=str(evidence_span),
            )
        
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

    
    
    def verify_batch(
        self,
        predictions: List[dict],
        full_document_text: str,
    ) -> List[VerificationResult]:
        """Verify each prediction independently so one bad record does not stop the batch."""
        results = []

        required_fields = {
            "code",
            "probability",
            "evidence_span",
            "evidence_start_char",
        }

        for prediction in predictions:
            # Reject malformed records without crashing the batch.
            if not isinstance(prediction, dict):
                results.append(
                    VerificationResult(
                        code="",
                        probability=0.0,
                        verification_status="rejected",
                        reject_reason="prediction must be a dictionary",
                        evidence_span="",
                    )
                )
                continue

            missing_fields = required_fields - prediction.keys()

            if missing_fields:
                results.append(
                    VerificationResult(
                        code=str(prediction.get("code", "")),
                        probability=prediction.get("probability", 0.0),
                        verification_status="rejected",
                        reject_reason=(
                            "missing fields: "
                            + ", ".join(sorted(missing_fields))
                        ),
                        evidence_span=str(
                            prediction.get("evidence_span", "")
                        ),
                    )
                )
                continue

            try:
                result = self.verify(
                    code=prediction["code"],
                    probability=prediction["probability"],
                    evidence_span=prediction["evidence_span"],
                    full_document_text=full_document_text,
                    evidence_start_char=prediction["evidence_start_char"],
                )
            except (TypeError, ValueError, IndexError) as exc:
                result = VerificationResult(
                    code=str(prediction.get("code", "")),
                    probability=prediction.get("probability", 0.0),
                    verification_status="rejected",
                    reject_reason=f"invalid prediction data: {exc}",
                    evidence_span=str(
                        prediction.get("evidence_span", "")
                    ),
                )

            results.append(result)

        return results

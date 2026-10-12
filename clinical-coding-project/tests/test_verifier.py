from module3_verification.verifier import NeuroSymbolicVerifier
from module3_verification.negation_detector import classify_evidence

TEXT = (
    "There was no evidence of pneumonia on chest imaging. "
    "The patient has a history of diabetes mellitus, well controlled with metformin. "
    "Blood cultures were drawn and the patient was diagnosed with sepsis on admission."
)


def test_classify_evidence_detects_negation():
    idx = TEXT.find("pneumonia")
    assert classify_evidence(TEXT, idx) == "negated"


def test_classify_evidence_detects_historical():
    idx = TEXT.find("diabetes mellitus")
    assert classify_evidence(TEXT, idx) == "historical"


def test_classify_evidence_defaults_to_active():
    idx = TEXT.find("sepsis")
    assert classify_evidence(TEXT, idx) == "active"


def test_verifier_rejects_malformed_code():
    verifier = NeuroSymbolicVerifier()
    result = verifier.verify(
        code="NOTACODE", probability=0.9, evidence_span="sepsis",
        full_document_text=TEXT, evidence_start_char=TEXT.find("sepsis"),
    )
    assert result.verification_status == "rejected"
    assert "malformed" in result.reject_reason


def test_verifier_rejects_negated_evidence():
    verifier = NeuroSymbolicVerifier()
    idx = TEXT.find("pneumonia")
    result = verifier.verify(
        code="J18.9", probability=0.9, evidence_span="pneumonia",
        full_document_text=TEXT, evidence_start_char=idx,
    )
    assert result.verification_status == "rejected"
    assert result.reject_reason == "supporting evidence is negated"


def test_verifier_accepts_high_confidence_active_evidence():
    verifier = NeuroSymbolicVerifier(auto_accept_threshold=0.9)
    idx = TEXT.find("sepsis")
    result = verifier.verify(
        code="A41.9", probability=0.95, evidence_span="sepsis",
        full_document_text=TEXT, evidence_start_char=idx,
    )
    assert result.verification_status == "accepted"


def test_verifier_routes_low_confidence_to_review():
    verifier = NeuroSymbolicVerifier(review_threshold=0.3, auto_accept_threshold=0.9)
    idx = TEXT.find("sepsis")
    result = verifier.verify(
        code="A41.9", probability=0.5, evidence_span="sepsis",
        full_document_text=TEXT, evidence_start_char=idx,
    )
    assert result.verification_status == "needs_review"

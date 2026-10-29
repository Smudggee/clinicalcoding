from module3_verification.verifier import NeuroSymbolicVerifier
from module3_verification.negation_detector import classify_evidence
import os
from module3_verification.icd_ontology import ICDOntology
from module3_verification.verifier import NeuroSymbolicVerifier
TEST_CODE_LIST = os.path.join(
    os.path.dirname(__file__),
    "..",
    "module3_verification",
    "valid_codes_sample.txt",
)

TEST_ONTOLOGY = ICDOntology(
    code_list_path=TEST_CODE_LIST,
    authoritative=True,  # Test-only: never use this setting for production.
)

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
    verifier = verifier = NeuroSymbolicVerifier(ontology=TEST_ONTOLOGY)
    idx = TEXT.find("pneumonia")
    result = verifier.verify(
        code="J18.9", probability=0.9, evidence_span="pneumonia",
        full_document_text=TEXT, evidence_start_char=idx,
    )
    assert result.verification_status == "rejected"
    assert result.reject_reason == "supporting evidence is negated"


def test_verifier_accepts_high_confidence_active_evidence():
    verifier = NeuroSymbolicVerifier(
    ontology=TEST_ONTOLOGY,
    auto_accept_threshold=0.9,
)
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
def test_missing_icd_list_routes_to_review():
    class MissingOntology:
        def is_syntactically_valid(self, code):
            return True

        def is_in_current_release(self, code):
            raise RuntimeError("No ICD code list loaded")

    verifier = NeuroSymbolicVerifier(ontology=MissingOntology())

    result = verifier.verify(
        code="A41.9",
        probability=0.95,
        evidence_span="sepsis",
        full_document_text=TEXT,
        evidence_start_char=TEXT.find("sepsis"),
    )

    assert result.verification_status == "needs_review"
    assert result.reject_reason == "authorized ICD code list is unavailable"


def test_verifier_rejects_probability_above_one():
    verifier = NeuroSymbolicVerifier()

    result = verifier.verify(
        code="A41.9",
        probability=1.5,
        evidence_span="sepsis",
        full_document_text=TEXT,
        evidence_start_char=TEXT.find("sepsis"),
    )

    assert result.verification_status == "rejected"
    assert result.reject_reason == "probability must be a finite number between 0 and 1"

def test_verify_batch_handles_multiple_predictions():
    verifier =  NeuroSymbolicVerifier(ontology=TEST_ONTOLOGY)

    predictions = [
        {
            "code": "A41.9",
            "probability": 0.95,
            "evidence_span": "sepsis",
            "evidence_start_char": TEXT.find("sepsis"),
        },
        {
            "code": "NOTACODE",
            "probability": 0.8,
            "evidence_span": "sepsis",
            "evidence_start_char": TEXT.find("sepsis"),
        },
    ]

    results = verifier.verify_batch(predictions, TEXT)

    assert len(results) == 2
    assert results[0].verification_status == "accepted"
    assert results[1].verification_status == "rejected"

def test_verify_batch_continues_after_missing_field():
    verifier  = NeuroSymbolicVerifier(ontology=TEST_ONTOLOGY)

    predictions = [
        {
            "code": "A41.9",
            "probability": 0.95,
            "evidence_span": "sepsis",
            "evidence_start_char": TEXT.find("sepsis"),
        },
        {
            "code": "A41.9",
            "probability": 0.95,
            "evidence_span": "sepsis",
        },
    ]

    results = verifier.verify_batch(predictions, TEXT)

    assert len(results) == 2
    assert results[0].verification_status == "accepted"
    assert results[1].verification_status == "rejected"
    assert "missing fields" in results[1].reject_reason

import math


def test_verifier_rejects_nan_probability():
    verifier = NeuroSymbolicVerifier()

    result = verifier.verify(
        code="A41.9",
        probability=float("nan"),
        evidence_span="sepsis",
        full_document_text=TEXT,
        evidence_start_char=TEXT.find("sepsis"),
    )

    assert result.verification_status == "rejected"
    assert result.reject_reason == (
        "probability must be a finite number between 0 and 1"
    )


def test_verifier_rejects_infinite_probability():
    verifier = NeuroSymbolicVerifier()

    result = verifier.verify(
        code="A41.9",
        probability=float("inf"),
        evidence_span="sepsis",
        full_document_text=TEXT,
        evidence_start_char=TEXT.find("sepsis"),
    )

    assert result.verification_status == "rejected"
    assert result.reject_reason == (
        "probability must be a finite number between 0 and 1"
    )


def test_verifier_rejects_boolean_probability():
    verifier = NeuroSymbolicVerifier()

    result = verifier.verify(
        code="A41.9",
        probability=True,
        evidence_span="sepsis",
        full_document_text=TEXT,
        evidence_start_char=TEXT.find("sepsis"),
    )

    assert result.verification_status == "rejected"
    assert result.reject_reason == (
        "probability must be a finite number between 0 and 1"
    )


def test_verifier_routes_invalid_evidence_offset_to_review():
    verifier = NeuroSymbolicVerifier(ontology=TEST_ONTOLOGY)

    result = verifier.verify(
        code="A41.9",
        probability=0.95,
        evidence_span="sepsis",
        full_document_text=TEXT,
        evidence_start_char=len(TEXT) + 10,
    )

    assert result.verification_status == "needs_review"
    assert result.reject_reason == "invalid evidence text or character offset"


def test_verifier_routes_negative_evidence_offset_to_review():
    verifier = NeuroSymbolicVerifier(ontology=TEST_ONTOLOGY)

    result = verifier.verify(
        code="A41.9",
        probability=0.95,
        evidence_span="sepsis",
        full_document_text=TEXT,
        evidence_start_char=-1,
    )

    assert result.verification_status == "needs_review"
    assert result.reject_reason == "invalid evidence text or character offset"

def test_verifier_rejects_mismatched_evidence_span_for_review():
    verifier = NeuroSymbolicVerifier(ontology=TEST_ONTOLOGY)

    result = verifier.verify(
        code="A41.9",
        probability=0.95,
        evidence_span="pneumonia",
        full_document_text=TEXT,
        evidence_start_char=TEXT.find("sepsis"),
    )

    assert result.verification_status == "needs_review"
    assert result.reject_reason == (
        "evidence span does not match document text"
    )


def test_verifier_routes_empty_evidence_span_to_review():
    verifier = NeuroSymbolicVerifier(ontology=TEST_ONTOLOGY)

    result = verifier.verify(
        code="A41.9",
        probability=0.95,
        evidence_span="",
        full_document_text=TEXT,
        evidence_start_char=TEXT.find("sepsis"),
    )

    assert result.verification_status == "needs_review"
    assert result.reject_reason == (
        "evidence span does not match document text"
    )

def test_verify_batch_handles_invalid_probability_type():
    verifier = NeuroSymbolicVerifier(ontology=TEST_ONTOLOGY)

    predictions = [
        {
            "code": "A41.9",
            "probability": 0.95,
            "evidence_span": "sepsis",
            "evidence_start_char": TEXT.find("sepsis"),
        },
        {
            "code": "A41.9",
            "probability": "high",
            "evidence_span": "sepsis",
            "evidence_start_char": TEXT.find("sepsis"),
        },
    ]

    results = verifier.verify_batch(predictions, TEXT)

    assert len(results) == 2
    assert results[0].verification_status == "accepted"
    assert results[1].verification_status == "rejected"


def test_verify_batch_handles_invalid_offset_type():
    verifier = NeuroSymbolicVerifier(ontology=TEST_ONTOLOGY)

    predictions = [
        {
            "code": "A41.9",
            "probability": 0.95,
            "evidence_span": "sepsis",
            "evidence_start_char": "invalid",
        },
        {
            "code": "A41.9",
            "probability": 0.95,
            "evidence_span": "sepsis",
            "evidence_start_char": TEXT.find("sepsis"),
        },
    ]

    results = verifier.verify_batch(predictions, TEXT)

    assert len(results) == 2
    assert results[0].verification_status == "needs_review"
    assert results[1].verification_status == "accepted"

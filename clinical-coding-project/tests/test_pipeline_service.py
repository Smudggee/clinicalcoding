from types import SimpleNamespace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from module4_dashboard.backend.app.pipeline_service import ClinicalCodingPipeline
from module2_classifier.schemas import ClassifiedDocument, Prediction


_TEST_RUNTIME_DIR = Path(__file__).resolve().parent / ".test_runtime"
_TEST_RUNTIME_DIR.mkdir(exist_ok=True)


class _Chunker:
    def chunk(self, document_id, text):
        return SimpleNamespace(document_id=document_id, windows=[SimpleNamespace(text=text)])


class _Verifier:
    def verify(self, **kwargs):
        return SimpleNamespace(
            verification_status="accepted",
            reject_reason=None,
        )


def test_analysis_marks_keyword_candidates_as_rule_based_demo():
    pipeline = object.__new__(ClinicalCodingPipeline)
    pipeline.chunker = _Chunker()
    pipeline.verifier = _Verifier()
    pipeline.candidate_provider = None

    result = pipeline.analyze_document("case-1", "Patient diagnosed with sepsis.")

    assert result["analysisSource"] == "rule_based_demo"
    assert "not BioClinicalBERT" in result["analysisSourceLabel"]
    assert result["predictedCodes"]
    submitted_at = datetime.fromisoformat(result["submittedAt"].replace("Z", "+00:00"))
    assert submitted_at.tzinfo is not None
    assert abs((datetime.now(timezone.utc) - submitted_at).total_seconds()) < 5


def test_module2_contract_predictions_are_sent_to_verifier():
    text = "Assessment: sepsis present."
    evidence_start = text.index("sepsis")
    seen_by_verifier = []

    class _RecordingVerifier:
        def verify(self, **kwargs):
            seen_by_verifier.append(kwargs)
            return SimpleNamespace(verification_status="needs_review", reject_reason="review")

    def classifier_provider(ingested):
        assert ingested.document_id == "case-2"
        return ClassifiedDocument(
            document_id=ingested.document_id,
            predictions=[Prediction(
                code="A41.9",
                probability=0.62,
                window_id=0,
                evidence_span="sepsis",
                evidence_start_char=evidence_start,
                evidence_end_char=evidence_start + len("sepsis"),
            )],
        )

    pipeline = object.__new__(ClinicalCodingPipeline)
    pipeline.chunker = _Chunker()
    pipeline.verifier = _RecordingVerifier()
    pipeline.candidate_provider = classifier_provider

    result = pipeline.analyze_document("case-2", text)

    assert result["analysisSource"] == "module2_classifier"
    assert result["predictedCodes"][0]["code"] == "A41.9"
    assert seen_by_verifier[0]["probability"] == 0.62
    assert seen_by_verifier[0]["evidence_start_char"] == evidence_start


def test_checkpoint_engine_status_and_output_are_reported(monkeypatch):
    checkpoint = _TEST_RUNTIME_DIR / f"classifier-{uuid4().hex}.pt"
    checkpoint.write_bytes(b"test marker")
    calls = []

    class _Engine:
        model = SimpleNamespace(model_name="test-encoder")

        def predict(self, **kwargs):
            calls.append(kwargs)
            return ClassifiedDocument(
                document_id=kwargs["document_id"],
                predictions=[Prediction(
                    code="A41.9",
                    probability=0.62,
                    window_id=0,
                    evidence_span="sepsis",
                    evidence_start_char=0,
                    evidence_end_char=6,
                )],
            )

    try:
        monkeypatch.setattr("module4_dashboard.backend.app.pipeline_service.SlidingWindowChunker", lambda **_: _Chunker())
        pipeline = ClinicalCodingPipeline(
            classifier_checkpoint_path=str(checkpoint),
            inference_engine_factory=lambda **_: _Engine(),
        )
        pipeline.verifier = _Verifier()
        result = pipeline.analyze_document("case-engine", "Assessment: sepsis present.")
        assert pipeline.classifier_status == "ready"
        assert "test-encoder" in result["analysisSourceLabel"]
        assert result["analysisSource"] == "module2_classifier"
        assert calls[0]["full_text"] == "Assessment: sepsis present."
    finally:
        checkpoint.unlink(missing_ok=True)


def test_checkpoint_initialization_failure_is_not_reported_as_demo(monkeypatch):
    checkpoint = _TEST_RUNTIME_DIR / f"invalid-classifier-{uuid4().hex}.pt"
    checkpoint.write_bytes(b"test marker")
    try:
        pipeline = ClinicalCodingPipeline(
            classifier_checkpoint_path=str(checkpoint),
            inference_engine_factory=lambda **_: (_ for _ in ()).throw(RuntimeError("bad checkpoint")),
        )
        assert pipeline.classifier_status == "load_failed"
        with pytest.raises(RuntimeError, match="bad checkpoint"):
            pipeline.analyze_document("case-bad-engine", "Assessment: sepsis present.")
    finally:
        checkpoint.unlink(missing_ok=True)

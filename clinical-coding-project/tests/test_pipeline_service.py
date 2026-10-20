from types import SimpleNamespace
from datetime import datetime, timezone

from module4_dashboard.backend.app.pipeline_service import ClinicalCodingPipeline
from module2_classifier.schemas import ClassifiedDocument, Prediction


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

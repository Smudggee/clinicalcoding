"""
End-to-end smoke test of Modules 1 and 3 (Module 2 is mocked, since a real
BioClinicalBERT forward pass needs the model downloaded). Run with:

    python -m module1_ingestion.pipeline_demo

This shows the group how the modules chain together per docs/interfaces.md,
without requiring GPU/model weights, so everyone can verify wiring on day one.
"""
import os

from module1_ingestion.preprocessing import normalize
from module1_ingestion.sliding_window import SlidingWindowChunker
from module3_verification.verifier import NeuroSymbolicVerifier


def mock_classify(document_text: str):
    """Stand-in for Module 2: pretend the classifier found two candidate codes."""
    sepsis_idx = document_text.find("sepsis, unspecified organism")
    diabetes_idx = document_text.find("type 2 diabetes mellitus")
    return [
        {
            "code": "A41.9", "probability": 0.91, "window_id": 0,
            "evidence_span": "sepsis, unspecified organism",
            "evidence_start_char": sepsis_idx, "evidence_end_char": sepsis_idx + 29,
        },
        {
            "code": "E11.9", "probability": 0.42, "window_id": 0,
            "evidence_span": "type 2 diabetes mellitus",
            "evidence_start_char": diabetes_idx, "evidence_end_char": diabetes_idx + 24,
        },
    ]


def main():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_note.txt")
    with open(sample_path) as f:
        raw_text = f.read()

    text = normalize(raw_text)

    # Module 1: chunk into windows (falls back to whitespace tokenizer if
    # transformers/model download isn't available in this environment)
    chunker = SlidingWindowChunker()
    ingested = chunker.chunk(document_id="demo-001", text=text)
    print(f"Module 1: produced {len(ingested.windows)} window(s)")

    # Module 2 (mocked): candidate codes with evidence spans
    predictions = mock_classify(text)
    print(f"Module 2 (mocked): {len(predictions)} candidate code(s)")

    # Module 3: verify each candidate
    verifier = NeuroSymbolicVerifier(review_threshold=0.5, auto_accept_threshold=0.9)
    results = verifier.verify_batch(predictions, full_document_text=text)

    print("\nModule 3 verification results:")
    for r in results:
        print(f"  {r.code:8s} p={r.probability:.2f}  status={r.verification_status:12s} "
              f"reason={r.reject_reason}")


if __name__ == "__main__":
    main()

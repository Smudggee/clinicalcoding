import sys
from module2_classifier.inference import ClinicalInferenceEngine

def main():
    print("=" * 70)
    print("ACCS Module 2 - Live Clinical Inference Test")
    print("=" * 70)

    checkpoint = "module2_classifier/checkpoints/best_model.pt"
    engine = ClinicalInferenceEngine(checkpoint_path=checkpoint)

    sample_note = (
        "Patient is a 64-year-old male presenting to the emergency department "
        "with acute crushing retrosternal chest pain radiating to the left jaw. "
        "ECG shows acute ST-elevation myocardial infarction (STEMI) of anterior wall. "
        "Past medical history is notable for long-standing essential primary hypertension "
        "and type 2 diabetes mellitus without chronic complications. "
        "Patient was initiated on dual antiplatelet therapy and transferred for cardiac catheterization."
    )

    print("\n[Input Clinical Note]:")
    print(sample_note)
    print("\n[Running Sliding-Window Inference & Max-Pooling]...")

    result = engine.predict(sample_note, document_id="DOC_LIVE_TEST_101", threshold=0.15)

    print("\n[Inference Output]:")
    print(f"Document ID: {result.document_id}")
    print(f"Total Diagnoses Detected: {len(result.predictions)}")
    print("-" * 70)
    for p in result.predictions:
        print(f"ICD-10 Code    : {p.code}")
        print(f"Confidence     : {p.probability:.4f} ({p.probability * 100:.1f}%)")
        print(f"Evidence Span  : \"{p.evidence_span}\"")
        print(f"Char Span      : ({p.evidence_start_char}, {p.evidence_end_char})")
        print("-" * 70)

if __name__ == "__main__":
    main()

"""
Rule-based demo pipeline bridging Modules 1 and 3 for the HITL Dashboard.

Executes:
1. Module 1: Text normalization and sliding-window chunking (512 token window, 256 stride).
2. Demo candidate generation using ICD10_KNOWLEDGE_BASE keyword matching (not Module 2 inference).
3. Module 3: Neuro-symbolic verification (syntactic regex, release check, NegEx negation detector,
             historical condition routing, confidence thresholding).
4. Attention span computation matching the frontend word-level heatmap requirements.
"""
import os
import re
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any, Callable, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from module1_ingestion.preprocessing import normalize, split_sections
from module1_ingestion.sliding_window import SlidingWindowChunker, aggregate_max
from module1_ingestion.schemas import IngestedDocument
from module2_classifier.schemas import ClassifiedDocument
from module3_verification.verifier import NeuroSymbolicVerifier
from module3_verification.icd_ontology import ICDOntology
from module3_verification.negation_detector import classify_evidence


# Knowledge base of ICD-10-CM codes, descriptions, and clinical concept patterns
ICD10_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "A41.9": {
        "description": "Sepsis, unspecified organism",
        "primary_terms": ["sepsis", "sepsis, unspecified organism", "septicemia"],
        "supporting_terms": ["fever", "hypotension", "blood cultures", "fluid resuscitation", "antibiotics", "infection"],
        "base_confidence": 0.93,
    },
    "J18.9": {
        "description": "Pneumonia, unspecified organism",
        "primary_terms": ["pneumonia", "community-acquired pneumonia", "consolidation"],
        "supporting_terms": ["cough", "sputum", "chest radiograph", "infiltrate", "dyspnea", "antibiotic", "breath sounds"],
        "base_confidence": 0.91,
    },
    "E11.9": {
        "description": "Type 2 diabetes mellitus without complications",
        "primary_terms": ["type 2 diabetes", "type 2 diabetes mellitus", "t2dm"],
        "supporting_terms": ["metformin", "hba1c", "blood glucose", "diet", "glucose"],
        "base_confidence": 0.88,
    },
    "E11.65": {
        "description": "Type 2 diabetes mellitus with hyperglycemia",
        "primary_terms": ["infection-induced hyperglycemia", "hyperglycemia", "poorly controlled type 2 diabetes"],
        "supporting_terms": ["insulin", "sliding scale", "blood glucose", "glucose", "hba1c"],
        "base_confidence": 0.86,
    },
    "I10": {
        "description": "Essential (primary) hypertension",
        "primary_terms": ["essential hypertension", "hypertension", "high blood pressure"],
        "supporting_terms": ["lisinopril", "amlodipine", "ramipril", "blood pressure", "antihypertensive"],
        "base_confidence": 0.92,
    },
    "J44.1": {
        "description": "Chronic obstructive pulmonary disease with (acute) exacerbation",
        "primary_terms": ["copd exacerbation", "acute exacerbation", "copd with exacerbation", "acute copd exacerbation"],
        "supporting_terms": ["breathlessness", "inhalers", "bronchodilators", "corticosteroids", "sputum", "spirometry"],
        "base_confidence": 0.89,
    },
    "J44.9": {
        "description": "Chronic obstructive pulmonary disease, unspecified",
        "primary_terms": ["chronic obstructive pulmonary disease", "copd"],
        "supporting_terms": ["inhalers", "wheezing", "dyspnea", "smoking"],
        "base_confidence": 0.84,
    },
    "N18.3": {
        "description": "Chronic kidney disease, stage 3 (moderate)",
        "primary_terms": ["chronic kidney disease stage 3", "ckd stage 3", "chronic kidney disease, stage 3"],
        "supporting_terms": ["egfr", "creatinine", "renal", "kidney", "renal diet"],
        "base_confidence": 0.87,
    },
    "N18.9": {
        "description": "Chronic kidney disease, unspecified",
        "primary_terms": ["chronic kidney disease", "ckd", "renal disease"],
        "supporting_terms": ["creatinine", "egfr", "nephrology"],
        "base_confidence": 0.79,
    },
    "J96.01": {
        "description": "Acute respiratory failure with hypoxia",
        "primary_terms": ["respiratory failure", "hypoxia", "acute respiratory failure"],
        "supporting_terms": ["oxygen", "o2", "saturation", "liters", "intubation"],
        "base_confidence": 0.85,
    },
    "N39.0": {
        "description": "Urinary tract infection, site not specified",
        "primary_terms": ["urinary tract infection", "uti"],
        "supporting_terms": ["dysuria", "urine culture", "pyuria", "leukocyte esterase"],
        "base_confidence": 0.90,
    },
    "I50.9": {
        "description": "Heart failure, unspecified",
        "primary_terms": ["heart failure", "congestive heart failure", "chf"],
        "supporting_terms": ["edema", "bnp", "ejection fraction", "furosemide", "orthopnea"],
        "base_confidence": 0.88,
    },
    "K21.9": {
        "description": "Gastro-esophageal reflux disease without esophagitis",
        "primary_terms": ["gastro-esophageal reflux", "gerd", "acid reflux"],
        "supporting_terms": ["omeprazole", "pantoprazole", "heartburn"],
        "base_confidence": 0.82,
    },
    "Z87.891": {
        "description": "Personal history of other specified conditions",
        "primary_terms": ["history of copd", "personal history of copd", "previous copd diagnosis", "prior copd"],
        "supporting_terms": ["history", "previous", "prior", "admissions"],
        "base_confidence": 0.83,
    },
}


def tokenize_words(text: str) -> List[str]:
    """Tokenize text into words preserving whitespace split matching frontend regex."""
    return [t for t in re.split(r"(\s+)", text) if t.strip()]


class ClinicalCodingPipeline:
    def __init__(self, review_threshold: float = 0.50, auto_accept_threshold: float = 0.85,
                 candidate_provider: Optional[Callable[[IngestedDocument], ClassifiedDocument]] = None):
        self.chunker = SlidingWindowChunker(window_size=512, stride=256)
        self.candidate_provider = candidate_provider
        self.ontology = ICDOntology()
        self.review_threshold = review_threshold
        self.auto_accept_threshold = auto_accept_threshold
        self.verifier = NeuroSymbolicVerifier(
            ontology=self.ontology,
            review_threshold=review_threshold,
            auto_accept_threshold=auto_accept_threshold,
        )

        self.inference_engine = None
        self.classifier_initialization_error = None
        checkpoint_path = os.environ.get(
            "ACCS_CLASSIFIER_CHECKPOINT",
            os.path.join(PROJECT_ROOT, "module2_classifier", "checkpoints", "best_model.pt"),
        )
        if self.candidate_provider is None and os.path.exists(checkpoint_path):
            try:
                from module2_classifier.inference import ClinicalInferenceEngine
                self.inference_engine = ClinicalInferenceEngine(checkpoint_path=checkpoint_path)
                print(f"[Pipeline] Loaded Module 2 classifier from {checkpoint_path}")
            except Exception as e:
                self.classifier_initialization_error = str(e)
                print(f"[Pipeline] Classifier checkpoint is present but could not be loaded: {e}")

    def update_thresholds(self, review_threshold: float, auto_accept_threshold: float):
        self.review_threshold = review_threshold
        self.auto_accept_threshold = auto_accept_threshold
        self.verifier.review_threshold = review_threshold
        self.verifier.auto_accept_threshold = auto_accept_threshold

    def analyze_document(self, document_id: str, raw_text: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes ingestion -> rule-based demo candidate matching -> verification.
        Candidate confidence values are hand-authored demo scores, not model outputs.
        """
        normalized_text = normalize(raw_text)
        ingested = self.chunker.chunk(document_id=document_id, text=normalized_text)
        words = tokenize_words(normalized_text)
        candidate_provider = getattr(self, "candidate_provider", None)
        inference_engine = getattr(self, "inference_engine", None)
        classifier_initialization_error = getattr(self, "classifier_initialization_error", None)

        # Prefer an explicitly supplied Module 2 provider, then a configured
        # checkpoint. Use keyword matching only when no classifier is available.
        if candidate_provider is not None:
            classified = candidate_provider(ingested)
            analysis_source_label = "Module 2 classifier provider output; model/checkpoint determined by provider"
        elif inference_engine is not None:
            classified = inference_engine.predict(
                text_or_windows=ingested.windows,
                document_id=document_id,
                threshold=0.15,
                full_text=normalized_text,
            )
            analysis_source_label = "Module 2 classifier checkpoint inference"
        elif classifier_initialization_error is not None:
            raise RuntimeError(
                "Classifier checkpoint was found but could not be loaded: "
                f"{classifier_initialization_error}"
            )
        else:
            candidate_predictions = self._generate_rule_based_candidates(normalized_text, ingested)
            analysis_source = "rule_based_demo"
            analysis_source_label = "Rule-based demo predictions (keyword matching; not BioClinicalBERT)"

        if candidate_provider is not None or inference_engine is not None:
            if classified.document_id != document_id:
                raise ValueError("Classifier returned predictions for a different document.")
            candidate_predictions = [
                {
                    "code": pred.code,
                    "description": ICD10_KNOWLEDGE_BASE.get(pred.code, {}).get("description", pred.code),
                    "probability": pred.probability,
                    "evidence_span": pred.evidence_span,
                    "evidence_start_char": pred.evidence_start_char,
                    "supporting_terms": [],
                    "primary_terms": [],
                }
                for pred in classified.predictions
            ]
            analysis_source = "module2_classifier"

        # 2. Module 3 Neuro-symbolic verification
        predicted_codes = []
        code_counter = 1
        for pred in candidate_predictions:
            v_res = self.verifier.verify(
                code=pred["code"],
                probability=pred["probability"],
                evidence_span=pred["evidence_span"],
                full_document_text=normalized_text,
                evidence_start_char=pred["evidence_start_char"],
            )

            # Map verification status to dashboard frontend taxonomy
            if v_res.verification_status == "accepted":
                frontend_status = "VERIFIED"
            elif v_res.reject_reason and "historical" in v_res.reject_reason:
                frontend_status = "PARENT CODE"
            else:
                frontend_status = "UNVERIFIED"

            # 3. Compute attention spans matching words: string[]
            attention_spans = self._compute_attention_spans(
                words=words,
                primary_terms=pred["primary_terms"],
                supporting_terms=pred["supporting_terms"],
                evidence_start_char=pred["evidence_start_char"],
                normalized_text=normalized_text,
            )

            predicted_codes.append({
                "id": f"c-{document_id}-{code_counter}",
                "code": pred["code"],
                "description": pred["description"],
                "confidence": int(round(pred["probability"] * 100)),
                "verificationStatus": frontend_status,
                "attentionSpans": attention_spans,
                "supportingEvidence": pred["evidence_span"],
                "rejectReason": v_res.reject_reason,
            })
            code_counter += 1

        # Calculate average confidence
        avg_conf = int(sum(c["confidence"] for c in predicted_codes) / len(predicted_codes)) if predicted_codes else 0

        return {
            "id": document_id,
            "analysisSource": analysis_source,
            "analysisSourceLabel": analysis_source_label,
            "patientId": patient_id or f"P-{abs(hash(document_id)) % 9000 + 1000}",
            "submittedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "Pending Review" if any(c["verificationStatus"] != "VERIFIED" for c in predicted_codes) else "Completed",
            "averageConfidence": avg_conf,
            "dischargeText": normalized_text,
            "words": words,
            "predictedCodes": predicted_codes,
            "submittedToBilling": False,
        }

    @staticmethod
    def _generate_rule_based_candidates(normalized_text: str, ingested: IngestedDocument) -> List[Dict[str, Any]]:
        """Generate illustrative candidates from the local keyword table; not model inference."""
        candidate_predictions = []
        for code, info in ICD10_KNOWLEDGE_BASE.items():
            match_found = False
            best_evidence = ""
            best_start_char = -1

            for term in info["primary_terms"]:
                pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
                match = pattern.search(normalized_text)
                if match:
                    match_found = True
                    best_start_char = match.start()
                    span_start = max(0, best_start_char - 40)
                    span_end = min(len(normalized_text), match.end() + 60)
                    best_evidence = normalized_text[span_start:span_end].replace("\n", " ").strip()
                    break

            if not match_found:
                continue

            window_scores = []
            for win in ingested.windows:
                win_score = 0.0
                if any(re.search(rf"\b{re.escape(term)}\b", win.text, re.IGNORECASE) for term in info["primary_terms"]):
                    win_score = info["base_confidence"]
                    sup_hits = sum(
                        1 for term in info["supporting_terms"]
                        if re.search(rf"\b{re.escape(term)}\b", win.text, re.IGNORECASE)
                    )
                    win_score = min(0.98, win_score + sup_hits * 0.02)
                window_scores.append(win_score)

            probability = aggregate_max(window_scores) if window_scores else info["base_confidence"]
            if probability == 0.0:
                probability = info["base_confidence"]
            candidate_predictions.append({
                "code": code,
                "description": info["description"],
                "probability": round(probability, 3),
                "evidence_span": best_evidence,
                "evidence_start_char": best_start_char,
                "supporting_terms": info["supporting_terms"],
                "primary_terms": info["primary_terms"],
            })
        return candidate_predictions

    def _compute_attention_spans(self, words: List[str], primary_terms: List[str],
                                 supporting_terms: List[str], evidence_start_char: int,
                                 normalized_text: str) -> List[Dict[str, Any]]:
        """Finds word indices corresponding to primary & supporting terms and builds attention spans."""
        spans = []
        for i, word in enumerate(words):
            clean_w = re.sub(r"[^\w]", "", word.lower())
            if not clean_w:
                continue

            # High weight for primary terms
            if any(clean_w in pt.lower() for pt in primary_terms):
                spans.append({"startIdx": i, "endIdx": i + 1, "weight": 0.95})
            # Medium weight for supporting clinical context
            elif any(clean_w in st.lower() for st in supporting_terms):
                spans.append({"startIdx": i, "endIdx": i + 1, "weight": 0.65})

        return spans

"""
Inference engine for Module 2.
Takes raw clinical notes or windowed chunks from Module 1, runs the classifier,
performs max-pooling aggregation per Eq. (1): p(c|D) = max_k p_k(c),
localizes evidence spans with character-level source offsets, and outputs
ClassifiedDocument adhering to docs/interfaces.md.
"""
import os
import sys
import re
import json
import argparse
from typing import List, Dict, Union, Optional, Tuple

import torch
from transformers import AutoTokenizer

# Ensure project root is in sys.path for direct script execution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from .model import BioClinicalBERTClassifier
    from .schemas import Prediction, ClassifiedDocument
except (ImportError, ValueError):
    from module2_classifier.model import BioClinicalBERTClassifier
    from module2_classifier.schemas import Prediction, ClassifiedDocument

from module1_ingestion.sliding_window import SlidingWindowChunker, aggregate_max


# Knowledge mapping of ICD-10 codes to clinical search terms / phrases
# Ordered from most specific to least specific for each code.
ICD_EVIDENCE_MAP: Dict[str, List[str]] = {
    "A41.9": [
        "sepsis, unspecified organism", "severe sepsis", "septic shock",
        "septicemia", "sepsis", "bacteremia", "blood cultures positive"
    ],
    "J18.9": [
        "pneumonia, unspecified organism", "community-acquired pneumonia",
        "bacterial pneumonia", "aspiration pneumonia", "pneumonia",
        "consolidation", "lung infiltrate", "infiltrate"
    ],
    "E11.9": [
        "type 2 diabetes mellitus without complications", "type 2 diabetes mellitus",
        "type 2 diabetes", "t2dm", "diabetes mellitus", "diabetes",
        "non-insulin-dependent diabetes"
    ],
    "E11.65": [
        "type 2 diabetes mellitus with hyperglycemia", "infection-induced hyperglycemia",
        "diabetic ketoacidosis", "hyperglycemia", "poorly controlled type 2 diabetes",
        "poorly controlled diabetes"
    ],
    "I10": [
        "essential (primary) hypertension", "essential hypertension",
        "primary hypertension", "hypertension", "high blood pressure", "htn"
    ],
    "J44.1": [
        "chronic obstructive pulmonary disease with (acute) exacerbation",
        "acute exacerbation of copd", "copd exacerbation", "acute copd exacerbation",
        "copd with exacerbation", "copd with acute exacerbation"
    ],
    "J44.9": [
        "chronic obstructive pulmonary disease, unspecified",
        "chronic obstructive pulmonary disease", "copd", "chronic bronchitis",
        "emphysema"
    ],
    "N18.3": [
        "chronic kidney disease, stage 3 (moderate)", "chronic kidney disease, stage 3",
        "chronic kidney disease stage 3", "ckd stage 3", "stage 3 ckd", "ckd 3"
    ],
    "N18.9": [
        "chronic kidney disease, unspecified", "chronic kidney disease",
        "ckd", "chronic renal disease", "renal disease", "renal insufficiency",
        "kidney failure", "renal failure"
    ],
    "J96.01": [
        "acute respiratory failure with hypoxia", "acute respiratory failure with hypoxemia",
        "acute hypoxemic respiratory failure", "acute respiratory failure",
        "respiratory failure", "hypoxia"
    ],
    "N39.0": [
        "urinary tract infection, site not specified", "urinary tract infection",
        "uti", "pyuria", "cystitis"
    ],
    "I50.9": [
        "heart failure, unspecified", "congestive heart failure",
        "acute decompensated heart failure", "heart failure", "chf"
    ],
    "K21.9": [
        "gastro-esophageal reflux disease without esophagitis",
        "gastro-esophageal reflux disease", "gastroesophageal reflux disease",
        "gerd", "acid reflux"
    ],
    "Z87.891": [
        "personal history of nicotine dependence", "history of tobacco use",
        "personal history of tobacco", "history of smoking", "tobacco use",
        "former smoker", "history of copd"
    ],
}


def _get_field(win, field_name: str, default=None):
    if isinstance(win, dict):
        return win.get(field_name, default)
    return getattr(win, field_name, default)


def _extract_sentence_context(full_text: str, match_start: int, match_end: int) -> str:
    """
    Extracts the surrounding sentence or clause context around a match
    to provide meaningful clinical context for verifier and human review.
    """
    # Find preceding sentence boundary or start of text
    prev_period = full_text.rfind(".", 0, match_start)
    prev_newline = full_text.rfind("\n", 0, match_start)
    start_bound = max(0, prev_period + 1, prev_newline + 1)

    # Find following sentence boundary or end of text
    next_period = full_text.find(".", match_end)
    next_newline = full_text.find("\n", match_end)
    end_candidates = [pos for pos in (next_period, next_newline) if pos != -1]
    if end_candidates:
        end_bound = min(end_candidates) + 1
    else:
        end_bound = len(full_text)

    snippet = full_text[start_bound:end_bound].replace("\n", " ").strip()
    # Bound length to reasonable readable window if note has missing periods
    if len(snippet) > 200 or len(snippet) < 5:
        c_start = max(0, match_start - 60)
        c_end = min(len(full_text), match_end + 60)
        snippet = full_text[c_start:c_end].replace("\n", " ").strip()

    return snippet


class ClinicalInferenceEngine:
    """
    Production-ready inference pipeline for multi-label ICD-10 prediction.
    Implements sliding-window inference, max-pooling aggregation, and
    character-accurate evidence localization adhering to docs/interfaces.md.
    """
    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        model: Optional[BioClinicalBERTClassifier] = None,
        label_map: Optional[Dict[str, int]] = None,
        device: Optional[str] = None,
        tokenizer_name: str = "emilyalsentzer/Bio_ClinicalBERT"
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        if model is not None and label_map is not None:
            self.model = model.to(self.device)
            self.label_map = label_map
        elif checkpoint_path and os.path.exists(checkpoint_path):
            self.model, self.label_map = BioClinicalBERTClassifier.load_checkpoint(checkpoint_path, device=self.device)
        else:
            raise ValueError("Must provide either an instantiated (model, label_map) or a valid checkpoint_path.")

        self.id_to_label = {v: k for k, v in self.label_map.items()}
        self.model.eval()

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        except Exception:
            self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

        self.chunker = SlidingWindowChunker(window_size=512, stride=256)

    @torch.no_grad()
    def predict(
        self,
        text_or_windows: Union[str, List[Dict]],
        document_id: str = "doc_query",
        threshold: float = 0.30,
        top_k: Optional[int] = None,
        full_text: Optional[str] = None
    ) -> ClassifiedDocument:
        """
        Runs sliding-window inference and aggregates to document-level predictions.
        Produces character-accurate evidence_start_char and evidence_end_char offsets
        in the full source document so Module 3 Verifier can check negation and history.
        """
        # Chunk text if raw string is provided
        if isinstance(text_or_windows, str):
            raw_text = text_or_windows
            ingested = self.chunker.chunk(document_id=document_id, text=text_or_windows)
            windows = ingested.windows
        else:
            windows = text_or_windows
            if full_text is not None:
                raw_text = full_text
            else:
                raw_text = " ".join([_get_field(w, "text", "") for w in windows])

        if not windows:
            return ClassifiedDocument(document_id=document_id, predictions=[])

        # Run model on each window
        # window_predictions: list of (w_idx, win, probs)
        window_predictions = []
        for w_idx, win in enumerate(windows):
            w_text = _get_field(win, "text", "")
            enc = self.tokenizer(
                w_text,
                truncation=True,
                padding="max_length",
                max_length=512,
                return_tensors="pt"
            ).to(self.device)

            probs = self.model.predict_proba(enc["input_ids"], enc["attention_mask"]).squeeze(0)
            window_predictions.append((w_idx, win, probs.cpu()))

        # Document-level aggregation: p(c|D) = max_k p_k(c)
        num_labels = len(self.label_map)
        doc_probs = torch.zeros(num_labels)
        best_window_for_code = {}

        for c_idx in range(num_labels):
            code_scores = [w_probs[c_idx].item() for _, _, w_probs in window_predictions]
            max_score = aggregate_max(code_scores)
            doc_probs[c_idx] = max_score

            best_w_idx = max(range(len(code_scores)), key=lambda i: code_scores[i])
            best_window_for_code[c_idx] = best_w_idx

        # Filter candidate codes meeting threshold
        candidate_predictions: List[Prediction] = []
        ranked_indices = torch.argsort(doc_probs, descending=True).tolist()

        for c_idx in ranked_indices:
            prob = doc_probs[c_idx].item()
            if prob < threshold and (top_k is None or len(candidate_predictions) >= top_k):
                continue

            code_str = self.id_to_label.get(c_idx, f"UNKNOWN_{c_idx}")
            best_w_idx = best_window_for_code[c_idx]
            best_win = windows[best_w_idx]
            win_text = _get_field(best_win, "text", "")

            # -------------------------------------------------------------
            # Character-Accurate Evidence Localization for Verifier Contract
            # -------------------------------------------------------------
            # Determine start char of the best window in the source document
            win_start_in_doc = raw_text.find(win_text) if win_text else 0
            if win_start_in_doc == -1:
                win_start_in_doc = 0

            matched_start = -1
            matched_end = -1
            matched_term = None

            candidate_terms = ICD_EVIDENCE_MAP.get(code_str, [code_str.lower()])

            # Search within the winning window first
            for term in candidate_terms:
                pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
                m = pattern.search(win_text)
                if m:
                    matched_start = win_start_in_doc + m.start()
                    matched_end = win_start_in_doc + m.end()
                    matched_term = term
                    break

            # If not in the winning window, search across the full document
            if matched_start == -1:
                for term in candidate_terms:
                    pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
                    m = pattern.search(raw_text)
                    if m:
                        matched_start = m.start()
                        matched_end = m.end()
                        matched_term = term
                        break

            # Fallback if no specific term matched: use window starting boundary
            if matched_start == -1:
                matched_start = max(0, win_start_in_doc)
                matched_end = min(len(raw_text), matched_start + min(len(win_text), 80))
                evidence_snippet = raw_text[matched_start:matched_end].replace("\n", " ").strip()
            else:
                # Extract surrounding sentence/clause context for evidence span
                evidence_snippet = _extract_sentence_context(raw_text, matched_start, matched_end)

            candidate_predictions.append(
                Prediction(
                    code=code_str,
                    probability=round(prob, 4),
                    window_id=best_w_idx,
                    evidence_span=evidence_snippet,
                    evidence_start_char=matched_start,
                    evidence_end_char=matched_end
                )
            )

            if top_k and len(candidate_predictions) >= top_k:
                break

        return ClassifiedDocument(
            document_id=document_id,
            predictions=candidate_predictions
        )


def main():
    parser = argparse.ArgumentParser(description="Run Clinical Coding Inference")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to best_model.pt")
    parser.add_argument("--text", type=str, default="Patient admitted with severe sepsis and pneumonia. Blood cultures positive.")
    parser.add_argument("--threshold", type=float, default=0.25)
    args = parser.parse_args()

    engine = ClinicalInferenceEngine(checkpoint_path=args.checkpoint)
    result = engine.predict(text_or_windows=args.text, threshold=args.threshold)

    print(f"\nDocument ID: {result.document_id}")
    print(f"Predicted ICD Codes ({len(result.predictions)}):")
    for p in result.predictions:
        print(f" - {p.code} (p={p.probability:.3f}): '{p.evidence_span}' [{p.evidence_start_char}:{p.evidence_end_char}]")


if __name__ == "__main__":
    main()

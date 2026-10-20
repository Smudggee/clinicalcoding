"""
Inference engine for Module 2.
Takes raw clinical notes or windowed chunks from Module 1, runs the classifier,
performs max-pooling aggregation per Eq. (1): p(c|D) = max_k p_k(c),
localizes evidence spans, and outputs ClassifiedDocument adhering to docs/interfaces.md.
"""
import os
import json
import argparse
from typing import List, Dict, Union, Optional, Tuple

import torch
from transformers import AutoTokenizer

from .model import BioClinicalBERTClassifier
from .schemas import Prediction, ClassifiedDocument
from module1_ingestion.sliding_window import SlidingWindowChunker, aggregate_max


class ClinicalInferenceEngine:
    """
    Production-ready inference pipeline for multi-label ICD-10 prediction.
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
        top_k: Optional[int] = None
    ) -> ClassifiedDocument:
        """
        Runs sliding-window inference and aggregates to document-level predictions.
        """
        # Chunk text if raw string is provided
        if isinstance(text_or_windows, str):
            ingested = self.chunker.chunk(document_id=document_id, text=text_or_windows)
            windows = ingested.windows
            raw_text = text_or_windows
        else:
            windows = text_or_windows
        def _get_field(win, field_name, default):
            if isinstance(win, dict):
                return win.get(field_name, default)
            return getattr(win, field_name, default)

        raw_text = " ".join([_get_field(w, "text", "") for w in windows])

        if not windows:
            return ClassifiedDocument(document_id=document_id, predictions=[])

        # Run model on each window
        # window_probs: list of tensors of shape (num_labels,)
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
            start_offset = _get_field(best_win, "start_token_offset", 0)
            end_offset = _get_field(best_win, "end_token_offset", len(win_text))

            # Extract representative evidence snippet
            evidence_snippet = win_text[:160].replace("\n", " ").strip()

            candidate_predictions.append(
                Prediction(
                    code=code_str,
                    probability=round(prob, 4),
                    window_id=best_w_idx,
                    evidence_span=evidence_snippet,
                    evidence_start_char=start_offset,
                    evidence_end_char=end_offset
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
        print(f"  - [{p.code}] Prob: {p.probability:.4f} | Window: {p.window_id} | Evidence: {p.evidence_span[:60]}...")


if __name__ == "__main__":
    main()

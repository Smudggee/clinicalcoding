"""
Evaluation script for Person 2 (Transformer Model).
Computes Micro-F1, Macro-F1, Precision, Recall, and Precision@5 on the test split
and generates the Baseline Evaluation Report required by the deliverables.
"""
import os
import json
import argparse
from typing import Dict, List, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

from .model import BioClinicalBERTClassifier
from .dataset import ClinicalDataset
from evaluation.metrics import micro_macro_f1, precision_at_k


def run_evaluation(
    checkpoint_path: str,
    test_data_path: str,
    threshold: float = 0.50,
    output_report_path: Optional[str] = None
) -> Dict[str, float]:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading checkpoint from: {checkpoint_path}")
    model, label_map = BioClinicalBERTClassifier.load_checkpoint(checkpoint_path, device=device)
    model_name = getattr(model, "model_name", "emilyalsentzer/Bio_ClinicalBERT")

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    test_dataset = ClinicalDataset(
        data_source=test_data_path,
        tokenizer=tokenizer,
        label_map=label_map
    )
    test_loader = DataLoader(test_dataset, batch_size=2, shuffle=False)

    model.eval()
    all_preds = []
    all_targets = []
    all_probs = []

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            logits = model(input_ids, attention_mask=attention_mask)
            probs = torch.sigmoid(logits)

            preds = (probs >= threshold).long().cpu().numpy()
            targets = labels.long().cpu().numpy()

            all_preds.append(preds)
            all_targets.append(targets)
            all_probs.append(probs.cpu().numpy())

    y_pred = np.vstack(all_preds)
    y_true = np.vstack(all_targets)
    y_prob = np.vstack(all_probs)

    # 1. Micro and Macro metrics
    metrics = micro_macro_f1(y_true, y_pred)

    # 2. Precision@5
    id_to_label = {v: k for k, v in label_map.items()}
    p_at_5_scores = []
    for i in range(len(y_true)):
        top5_indices = np.argsort(y_prob[i])[::-1][:5]
        ranked_codes = [id_to_label[idx] for idx in top5_indices]
        gold_indices = np.where(y_true[i] == 1.0)[0]
        gold_codes = {id_to_label[idx] for idx in gold_indices}
        p_at_5_scores.append(precision_at_k(ranked_codes, gold_codes, k=5))

    metrics["precision_at_5"] = float(np.mean(p_at_5_scores)) if p_at_5_scores else 0.0
    metrics["test_samples"] = len(test_dataset)
    metrics["num_labels"] = len(label_map)
    metrics["decision_threshold"] = threshold

    # Print summary report
    print("\n" + "=" * 50)
    print("      BASELINE EVALUATION REPORT (PERSON 2)      ")
    print("=" * 50)
    print(f"Test Samples:       {metrics['test_samples']}")
    print(f"Target Labels:      {metrics['num_labels']} ICD-10 codes")
    print(f"Decision Threshold: {metrics['decision_threshold']}")
    print("-" * 50)
    print(f"Micro-F1:           {metrics['f1_micro']:.4f}")
    print(f"Micro-Precision:    {metrics['precision_micro']:.4f}")
    print(f"Micro-Recall:       {metrics['recall_micro']:.4f}")
    print(f"Macro-F1:           {metrics['f1_macro']:.4f}")
    print(f"Precision@5:        {metrics['precision_at_5']:.4f}")
    print("=" * 50)

    # Save to report file
    report_file = output_report_path or os.path.join(
        os.path.dirname(checkpoint_path), "baseline_evaluation_report.json"
    )
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Report saved to: {report_file}\n")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate BioClinicalBERT Classifier")
    parser.add_argument("--checkpoint", type=str, default="module2_classifier/checkpoints/best_model.pt", help="Path to best_model.pt")
    parser.add_argument("--test_data", type=str, default="data/test.csv", help="Path to test CSV/JSON")
    parser.add_argument("--threshold", type=float, default=0.40, help="Confidence threshold")
    parser.add_argument("--output_report", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    run_evaluation(
        checkpoint_path=args.checkpoint,
        test_data_path=args.test_data,
        threshold=args.threshold,
        output_report_path=args.output_report
    )


if __name__ == "__main__":
    main()

"""
Training and validation pipeline for the BioClinicalBERT multi-label classifier.
Implements BCEWithLogitsLoss / class_weighted_bce / FocalLoss, validation metrics computation,
and checkpoint saving.
"""
import os
import sys
import json
import argparse
from typing import Dict, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

# Ensure project root is in sys.path for direct script execution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from .model import BioClinicalBERTClassifier
    from .dataset import ClinicalDataset
    from .losses import FocalLoss, class_weighted_bce
except (ImportError, ValueError):
    from module2_classifier.model import BioClinicalBERTClassifier
    from module2_classifier.dataset import ClinicalDataset
    from module2_classifier.losses import FocalLoss, class_weighted_bce

from evaluation.metrics import micro_macro_f1


def get_default_tokenizer(model_name: str = "emilyalsentzer/Bio_ClinicalBERT"):
    try:
        return AutoTokenizer.from_pretrained(model_name)
    except Exception:
        # Fallback to standard bert-base-uncased if offline or model name is specialized
        return AutoTokenizer.from_pretrained("bert-base-uncased")


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    loss_fn: nn.Module,
    device: str
) -> float:
    """Runs one training epoch and returns mean loss."""
    model.train()
    total_loss = 0.0

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()
        logits = model(input_ids, attention_mask=attention_mask)
        loss = loss_fn(logits, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()

    return total_loss / max(len(dataloader), 1)


@torch.no_grad()
def evaluate_dataset(
    model: nn.Module,
    dataloader: DataLoader,
    loss_fn: nn.Module,
    device: str,
    threshold: float = 0.5
) -> Tuple[float, Dict[str, float]]:
    """Evaluates the model on validation/test data and returns loss and metrics."""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        logits = model(input_ids, attention_mask=attention_mask)
        loss = loss_fn(logits, labels)
        total_loss += loss.item()

        probs = torch.sigmoid(logits)
        preds = (probs >= threshold).long().cpu().numpy()
        targets = labels.long().cpu().numpy()

        all_preds.append(preds)
        all_targets.append(targets)

    mean_loss = total_loss / max(len(dataloader), 1)
    if all_preds:
        import numpy as np
        y_pred = np.vstack(all_preds)
        y_true = np.vstack(all_targets)
        metrics = micro_macro_f1(y_true, y_pred)
    else:
        metrics = {"f1_micro": 0.0, "f1_macro": 0.0, "precision_micro": 0.0, "recall_micro": 0.0}

    return mean_loss, metrics


def main():
    parser = argparse.ArgumentParser(description="Train BioClinicalBERT Multi-Label Classifier")
    parser.add_argument("--train_data", type=str, default="data/train.csv", help="Path to training CSV/JSON")
    parser.add_argument("--val_data", type=str, default="data/val.csv", help="Path to validation CSV/JSON")
    parser.add_argument("--label_map", type=str, default="data/label_map.json", help="Path to label_map.json")
    parser.add_argument("--save_dir", type=str, default="module2_classifier/checkpoints", help="Output directory")
    parser.add_argument("--model_name", type=str, default="emilyalsentzer/Bio_ClinicalBERT")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max_length", type=int, default=512)
    parser.add_argument("--use_focal_loss", action="store_true", help="Use Focal Loss instead of BCE")
    parser.add_argument("--use_weighted_bce", action="store_true", help="Use class_weighted_bce with pos_weight from training data")
    parser.add_argument("--loss_type", type=str, default=None, choices=["bce", "focal", "weighted_bce"],
                        help="Loss function: 'bce', 'focal', or 'weighted_bce'")
    parser.add_argument("--device", type=str, default=None, help="cpu or cuda")
    args = parser.parse_args()

    # Determine device
    if args.device:
        device = args.device
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Load label map
    with open(args.label_map, "r", encoding="utf-8") as f:
        label_map = json.load(f)
    num_labels = len(label_map)
    print(f"Loaded label map with {num_labels} ICD-10 codes.")

    # Initialize Tokenizer and Datasets
    tokenizer = get_default_tokenizer(args.model_name)
    train_dataset = ClinicalDataset(args.train_data, tokenizer=tokenizer, label_map=label_map, max_length=args.max_length)
    val_dataset = ClinicalDataset(args.val_data, tokenizer=tokenizer, label_map=label_map, max_length=args.max_length)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    print(f"Train samples: {len(train_dataset)} | Val samples: {len(val_dataset)}")

    # Initialize Model, Optimizer, Loss Function
    model = BioClinicalBERTClassifier(num_labels=num_labels, model_name=args.model_name).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    # Loss function selection
    if args.loss_type == "focal" or args.use_focal_loss:
        loss_fn = FocalLoss()
        loss_name = "FocalLoss"
    elif args.loss_type == "weighted_bce" or args.use_weighted_bce:
        pos_weight = train_dataset.get_pos_weights().to(device)
        loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        loss_name = "class_weighted_bce"
        print(f"Using class_weighted_bce with pos_weight: [{pos_weight.min():.2f}, {pos_weight.max():.2f}]")
    else:
        loss_fn = torch.nn.BCEWithLogitsLoss()
        loss_name = "BCEWithLogitsLoss"

    print(f"Loss function: {loss_name}")

    best_f1 = -1.0
    os.makedirs(args.save_dir, exist_ok=True)
    best_checkpoint_path = os.path.join(args.save_dir, "best_model.pt")

    print("\n--- Starting Training ---")
    for epoch in range(1, args.epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, loss_fn, device)
        val_loss, val_metrics = evaluate_dataset(model, val_loader, loss_fn, device)

        f1_micro = val_metrics.get("f1_micro", 0.0)
        f1_macro = val_metrics.get("f1_macro", 0.0)
        print(f"Epoch {epoch}/{args.epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Micro-F1: {f1_micro:.4f} | Val Macro-F1: {f1_macro:.4f}")

        # Save checkpoint on improvement
        if f1_micro >= best_f1:
            best_f1 = f1_micro
            config_dict = {
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "lr": args.lr,
                "model_name": args.model_name,
                "num_labels": num_labels,
                "loss_type": loss_name,
                "best_val_f1_micro": f1_micro,
                "best_val_loss": val_loss
            }
            model.save_checkpoint(best_checkpoint_path, label_map=label_map, config=config_dict)

            # Also save training config
            config_path = os.path.join(args.save_dir, "training_config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2)

    print(f"\nTraining completed! Best checkpoint saved to: {best_checkpoint_path}")


if __name__ == "__main__":
    main()

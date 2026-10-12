"""
Minimal training loop skeleton. Fill in data loading once Module 1's output
format is finalized. Implements the ablation order from Section VII-E:
  1. BioClinicalBERT + simple truncation (baseline)
  2. + sliding windows
  3. + class-weighted / focal loss
  4. + threshold calibration
  5. + neuro-symbolic verification (Module 3, not part of training)
"""
import argparse
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

from .model import BioClinicalBERTClassifier
from .losses import FocalLoss


def train_one_epoch(model, dataloader, optimizer, loss_fn, device):
    model.train()
    total_loss = 0.0
    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()
        logits = model(input_ids, attention_mask)
        loss = loss_fn(logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    return total_loss / max(len(dataloader), 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_labels", type=int, required=True)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--use_focal_loss", action="store_true")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
    model = BioClinicalBERTClassifier(num_labels=args.num_labels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    loss_fn = FocalLoss() if args.use_focal_loss else torch.nn.BCEWithLogitsLoss()

    # TODO: replace with real ClinicalWindowDataset once Module 1 produces windows
    print("Wire up a DataLoader here using dataset.ClinicalWindowDataset, then call:")
    print("  train_one_epoch(model, dataloader, optimizer, loss_fn, device)")


if __name__ == "__main__":
    main()

"""
BioClinicalBERT-based multi-label classifier (Section III-B, Module 2).

Encodes one window at a time; document-level scores are produced by
aggregating per-window probabilities (see module1_ingestion.sliding_window
.aggregate_max / aggregate_mean), per Eq. (1).
"""
from typing import List, Dict
import torch
import torch.nn as nn


class BioClinicalBERTClassifier(nn.Module):
    def __init__(self, num_labels: int,
                 model_name: str = "emilyalsentzer/Bio_ClinicalBERT",
                 dropout: float = 0.1):
        super().__init__()
        from transformers import AutoModel
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_labels)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_repr = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        cls_repr = self.dropout(cls_repr)
        return self.classifier(cls_repr)  # logits, shape (batch, num_labels)

    @torch.no_grad()
    def predict_window(self, tokenizer, window_text: str, device="cpu") -> Dict[str, float]:
        """Convenience method: window text -> {code_index: probability}."""
        self.eval()
        enc = tokenizer(window_text, truncation=True, max_length=512,
                         return_tensors="pt").to(device)
        logits = self.forward(enc["input_ids"], enc["attention_mask"])
        probs = torch.sigmoid(logits).squeeze(0)
        return {i: p.item() for i, p in enumerate(probs)}

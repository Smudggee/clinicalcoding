"""
BioClinicalBERT-based multi-label classifier (Section III-B, Module 2).

Encodes clinical text windows; document-level scores are produced by
aggregating per-window probabilities per Eq. (1): p(c|D) = max_k p_k(c).
Includes checkpoint saving, loading, and batch probability inference.
"""
import os
import json
from typing import List, Dict, Optional, Tuple, Union
import torch
import torch.nn as nn


class BioClinicalBERTClassifier(nn.Module):
    """
    Transformer-based multi-label ICD-10 classifier.
    Uses a pretrained biomedical encoder (default Bio_ClinicalBERT) with
    dropout and a linear classification projection layer.
    """
    def __init__(
        self,
        num_labels: int,
        model_name: str = "emilyalsentzer/Bio_ClinicalBERT",
        dropout: float = 0.1,
        hidden_size: Optional[int] = None
    ):
        super().__init__()
        self.num_labels = num_labels
        self.model_name = model_name

        from transformers import AutoModel
        self.encoder = AutoModel.from_pretrained(model_name)
        h_size = self.encoder.config.hidden_size

        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(h_size, num_labels)

    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Returns raw classification logits of shape (batch_size, num_labels).
        """
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        if hasattr(outputs, "last_hidden_state"):
            cls_repr = outputs.last_hidden_state[:, 0, :]
        elif hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
            cls_repr = outputs.pooler_output
        elif isinstance(outputs, (tuple, list)):
            cls_repr = outputs[0][:, 0, :]
        else:
            cls_repr = outputs[:, 0, :]

        cls_repr = self.dropout(cls_repr)
        logits = self.classifier(cls_repr)
        return logits

    @torch.no_grad()
    def predict_proba(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Returns sigmoid probabilities of shape (batch_size, num_labels).
        """
        self.eval()
        logits = self.forward(input_ids=input_ids, attention_mask=attention_mask)
        return torch.sigmoid(logits)

    def save_checkpoint(self, save_path: str, label_map: Optional[Dict[str, int]] = None, config: Optional[Dict] = None):
        """
        Saves model weights, label map, and hyperparameter configuration.
        """
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        checkpoint = {
            "model_state_dict": self.state_dict(),
            "num_labels": self.num_labels,
            "model_name": self.model_name,
            "label_map": label_map or {},
            "config": config or {}
        }
        torch.save(checkpoint, save_path)
        print(f"Model checkpoint saved successfully to: {save_path}")

    @classmethod
    def load_checkpoint(cls, checkpoint_path: str, device: str = "cpu") -> Tuple["BioClinicalBERTClassifier", Dict[str, int]]:
        """
        Loads a saved checkpoint and returns (model, label_map).
        """
        checkpoint = torch.load(checkpoint_path, map_location=device)
        num_labels = checkpoint.get("num_labels", len(checkpoint.get("label_map", {})))
        model_name = checkpoint.get("model_name", "emilyalsentzer/Bio_ClinicalBERT")

        model = cls(num_labels=num_labels, model_name=model_name)
        state_dict = checkpoint.get("model_state_dict")
        if not isinstance(state_dict, dict):
            raise ValueError("Checkpoint does not contain a model_state_dict.")
        model.load_state_dict(state_dict, strict=True)
        model.to(device)
        model.eval()

        label_map = checkpoint.get("label_map", {})
        if not isinstance(label_map, dict) or len(label_map) != num_labels:
            raise ValueError("Checkpoint label map does not match its classifier output size.")
        if sorted(label_map.values()) != list(range(num_labels)):
            raise ValueError("Checkpoint label indices must be contiguous from zero.")
        print(f"Loaded checkpoint from {checkpoint_path} with {num_labels} labels on {device}.")
        return model, label_map

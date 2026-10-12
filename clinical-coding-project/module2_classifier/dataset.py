"""
PyTorch Dataset for windowed clinical text + multi-hot ICD-10 label vectors.
Expects a label_map.json mapping code -> column index (build this from your
training split's label vocabulary, see evaluation/label_vocab.py once you
write it).
"""
import json
import torch
from torch.utils.data import Dataset


class ClinicalWindowDataset(Dataset):
    def __init__(self, examples, tokenizer, label_map_path: str, max_length: int = 512):
        """
        examples: list of dicts, each {"text": str, "codes": [str, ...]}
                  (one dict per window, already produced by Module 1)
        """
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length
        with open(label_map_path) as f:
            self.label_map = json.load(f)
        self.num_labels = len(self.label_map)

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        enc = self.tokenizer(
            ex["text"], truncation=True, padding="max_length",
            max_length=self.max_length, return_tensors="pt",
        )
        labels = torch.zeros(self.num_labels)
        for code in ex["codes"]:
            if code in self.label_map:
                labels[self.label_map[code]] = 1.0

        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": labels,
        }

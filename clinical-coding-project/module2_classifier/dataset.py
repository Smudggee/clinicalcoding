"""
PyTorch Dataset for clinical documents + multi-hot ICD-10 label vectors.
Supports loading from CSV, JSON, or in-memory lists, encoding ICD codes using
label_map.json, and generating PyTorch tensors for DataLoader.
"""
import os
import json
from typing import List, Dict, Union, Optional
import pandas as pd
import torch
from torch.utils.data import Dataset


class ClinicalDataset(Dataset):
    """
    Multi-label clinical text dataset.
    Loads clinical notes and produces tokenized tensors with multi-hot label targets.
    """
    def __init__(
        self,
        data_source: Union[str, pd.DataFrame, List[Dict]],
        tokenizer,
        label_map: Union[str, Dict[str, int]],
        max_length: int = 512,
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length

        # Load label map
        if isinstance(label_map, str):
            with open(label_map, "r", encoding="utf-8") as f:
                self.label_map: Dict[str, int] = json.load(f)
        else:
            self.label_map = label_map
        self.num_labels = len(self.label_map)
        self.id_to_label = {v: k for k, v in self.label_map.items()}

        # Load examples
        self.records: List[Dict] = []
        if isinstance(data_source, str):
            if data_source.endswith(".csv"):
                df = pd.read_csv(data_source)
                self.records = self._parse_dataframe(df)
            elif data_source.endswith(".json") or data_source.endswith(".jsonl"):
                with open(data_source, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.records = data if isinstance(data, list) else [data]
            else:
                raise ValueError(f"Unsupported file format: {data_source}")
        elif isinstance(data_source, pd.DataFrame):
            self.records = self._parse_dataframe(data_source)
        elif isinstance(data_source, list):
            self.records = data_source
        else:
            raise TypeError(f"Unsupported data_source type: {type(data_source)}")

    def _parse_dataframe(self, df: pd.DataFrame) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            text = str(row.get("text", ""))
            doc_id = str(row.get("document_id", f"doc_{len(records)}"))
            raw_codes = row.get("codes", "")
            if isinstance(raw_codes, str):
                # Supports semicolon, comma, or json array
                if raw_codes.startswith("[") and raw_codes.endswith("]"):
                    try:
                        codes = json.loads(raw_codes)
                    except Exception:
                        codes = [c.strip() for c in raw_codes.strip("[]").replace("'", "").split(",") if c.strip()]
                elif ";" in raw_codes:
                    codes = [c.strip() for c in raw_codes.split(";") if c.strip()]
                elif "," in raw_codes:
                    codes = [c.strip() for c in raw_codes.split(",") if c.strip()]
                else:
                    codes = [raw_codes.strip()] if raw_codes.strip() else []
            elif isinstance(raw_codes, (list, tuple)):
                codes = [str(c).strip() for c in raw_codes]
            else:
                codes = []

            records.append({
                "document_id": doc_id,
                "text": text,
                "codes": codes
            })
        return records

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.records[idx]
        text = item["text"]
        codes = item.get("codes", [])

        # Tokenize text
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )

        # Multi-hot vector
        labels = torch.zeros(self.num_labels, dtype=torch.float32)
        for code in codes:
            if code in self.label_map:
                labels[self.label_map[code]] = 1.0

        return {
            "document_id": item.get("document_id", f"doc_{idx}"),
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": labels
        }


# Backwards compatibility alias
ClinicalWindowDataset = ClinicalDataset

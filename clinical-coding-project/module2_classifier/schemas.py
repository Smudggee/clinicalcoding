"""Data contracts for Module 2 (see docs/interfaces.md)."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Prediction:
    code: str
    probability: float
    window_id: int
    evidence_span: str
    evidence_start_char: int
    evidence_end_char: int


@dataclass
class ClassifiedDocument:
    document_id: str
    predictions: List[Prediction] = field(default_factory=list)

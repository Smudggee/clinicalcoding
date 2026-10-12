"""Data contracts for Module 1 output (see docs/interfaces.md)."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Window:
    window_id: int
    text: str
    start_token_offset: int
    end_token_offset: int


@dataclass
class IngestedDocument:
    document_id: str
    windows: List[Window] = field(default_factory=list)

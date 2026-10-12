"""
Sliding-window chunking (Section III-C).

Window size 512 tokens, stride 256 tokens, so each new window starts in the
middle of the previous one -> border concepts appear in >=2 windows and are
less likely to be lost entirely.

Uses a HuggingFace tokenizer so token counts match what Module 2 (BERT-based
classifier) actually sees. Falls back to whitespace tokenization if
transformers isn't installed yet, so this module is independently runnable.
"""
from typing import List
from .schemas import Window, IngestedDocument

WINDOW_SIZE = 512
STRIDE = 256


def _get_tokenizer(model_name: str = "emilyalsentzer/Bio_ClinicalBERT"):
    try:
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(model_name)
    except Exception:
        return None


class SlidingWindowChunker:
    def __init__(self, window_size: int = WINDOW_SIZE, stride: int = STRIDE,
                 model_name: str = "emilyalsentzer/Bio_ClinicalBERT"):
        if stride >= window_size:
            raise ValueError("stride must be smaller than window_size to get overlap")
        self.window_size = window_size
        self.stride = stride
        self.tokenizer = _get_tokenizer(model_name)

    def chunk(self, document_id: str, text: str) -> IngestedDocument:
        if self.tokenizer is not None:
            return self._chunk_with_tokenizer(document_id, text)
        return self._chunk_with_whitespace(document_id, text)

    def _chunk_with_tokenizer(self, document_id: str, text: str) -> IngestedDocument:
        encoding = self.tokenizer(text, add_special_tokens=False,
                                   return_offsets_mapping=True)
        input_ids = encoding["input_ids"]
        offsets = encoding["offset_mapping"]

        windows = []
        start = 0
        window_id = 0
        n = len(input_ids)
        if n == 0:
            return IngestedDocument(document_id=document_id, windows=[])

        while start < n:
            end = min(start + self.window_size, n)
            token_slice = input_ids[start:end]
            window_text = self.tokenizer.decode(token_slice, skip_special_tokens=True)
            char_start = offsets[start][0] if start < len(offsets) else 0
            char_end = offsets[end - 1][1] if end - 1 < len(offsets) else len(text)
            windows.append(Window(
                window_id=window_id,
                text=window_text,
                start_token_offset=char_start,
                end_token_offset=char_end,
            ))
            window_id += 1
            if end == n:
                break
            start += self.stride

        return IngestedDocument(document_id=document_id, windows=windows)

    def _chunk_with_whitespace(self, document_id: str, text: str) -> IngestedDocument:
        """Fallback: approximate 'tokens' as whitespace-split words."""
        words = text.split()
        windows = []
        start = 0
        window_id = 0
        n = len(words)
        if n == 0:
            return IngestedDocument(document_id=document_id, windows=[])

        while start < n:
            end = min(start + self.window_size, n)
            window_text = " ".join(words[start:end])
            windows.append(Window(
                window_id=window_id,
                text=window_text,
                start_token_offset=start,
                end_token_offset=end,
            ))
            window_id += 1
            if end == n:
                break
            start += self.stride

        return IngestedDocument(document_id=document_id, windows=windows)


def aggregate_max(window_probs: List[float]) -> float:
    """Eq. (1): p(c|D) = max_k p_k(c). Emphasizes strong evidence in any window."""
    return max(window_probs) if window_probs else 0.0


def aggregate_mean(window_probs: List[float]) -> float:
    """More conservative alternative aggregation mentioned in Section III-C."""
    return sum(window_probs) / len(window_probs) if window_probs else 0.0


from typing import List

from .schemas import Window, IngestedDocument

WINDOW_SIZE = 512
STRIDE = 256


def _get_tokenizer(model_name="emilyalsentzer/Bio_ClinicalBERT"):
    """Load the clinical tokenizer, if available."""
    try:
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(model_name)
    except Exception:
        return None


def aggregate_max(probs):
    """Return the maximum probability across windows."""
    if not probs:
        raise ValueError("probs must not be empty")
    return max(probs)


def aggregate_mean(probs):
    """Return the mean probability across windows."""
    if not probs:
        raise ValueError("probs must not be empty")
    return sum(probs) / len(probs)


class SlidingWindowChunker:
    def __init__(
        self,
        window_size=WINDOW_SIZE,
        stride=STRIDE,
        model_name="emilyalsentzer/Bio_ClinicalBERT",
    ):
        if window_size <= 0:
            raise ValueError("window_size must be positive")

        if stride <= 0 or stride >= window_size:
            raise ValueError("stride must be positive and smaller than window_size")

        self.window_size = window_size
        self.stride = stride
        self.tokenizer = _get_tokenizer(model_name)

    def chunk(self, document_id, text):
        """Split text into overlapping windows.

        Malayalam text uses whitespace-based chunking to preserve its
        original characters. Other text uses the clinical tokenizer
        when it is available.
        """
        has_malayalam = any(
            "\u0D00" <= char <= "\u0D7F"
            for char in text
        )

        if has_malayalam or self.tokenizer is None:
            return self._chunk_with_whitespace(document_id, text)

        return self._chunk_with_tokenizer(document_id, text)

    def _chunk_with_tokenizer(self, document_id, text):
        """Create windows using tokenizer offsets while preserving source text."""
        encoding = self.tokenizer(
            text,
            add_special_tokens=False,
            return_offsets_mapping=True,
        )

        offsets = encoding["offset_mapping"]
        windows = []
        start = 0
        window_id = 0
        n = len(offsets)

        if n == 0:
            return IngestedDocument(
                document_id=document_id,
                windows=[],
            )

        while start < n:
            end = min(start + self.window_size, n)

            char_start = offsets[start][0]
            char_end = offsets[end - 1][1]
            window_text = text[char_start:char_end]

            windows.append(
                Window(
                    window_id=window_id,
                    text=window_text,
                    start_token_offset=start,
                    end_token_offset=end,
                )
            )

            window_id += 1

            if end == n:
                break

            start += self.stride

        return IngestedDocument(
            document_id=document_id,
            windows=windows,
        )

    def _chunk_with_whitespace(self, document_id, text):
        """Create overlapping windows using whitespace-separated words."""
        words = text.split()
        windows = []
        start = 0
        window_id = 0
        n = len(words)

        if n == 0:
            return IngestedDocument(
                document_id=document_id,
                windows=[],
            )

        while start < n:
            end = min(start + self.window_size, n)
            window_text = " ".join(words[start:end])

            windows.append(
                Window(
                    window_id=window_id,
                    text=window_text,
                    start_token_offset=start,
                    end_token_offset=end,
                )
            )

            window_id += 1

            if end == n:
                break

            start += self.stride

        return IngestedDocument(
            document_id=document_id,
            windows=windows,
        )

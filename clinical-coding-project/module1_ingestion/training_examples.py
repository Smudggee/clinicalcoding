
"""Convert Module 1 windows into Module 2 training examples."""

from module1_ingestion.sliding_window import SlidingWindowChunker


def make_training_examples(records, chunker=None):
    """
    Convert already-split document records into window-level examples.

    Each input record must contain:
        document_id: str
        text: str
        codes: list[str]

    Call this separately for train, validation, and test records.
    Patient-level splitting must happen before this function is called.
    """
    if chunker is None:
        chunker = SlidingWindowChunker()

    examples = []

    for record in records:
        if not record.get("document_id"):
            raise ValueError("Every record must have a document_id.")
        if "text" not in record or "codes" not in record:
            raise ValueError("Every record must contain text and codes.")

        document = chunker.chunk(
            document_id=record["document_id"],
            text=record["text"],
        )

        for window in document.windows:
            examples.append({
                "text": window.text,
                "codes": list(record["codes"]),
            })

    return examples

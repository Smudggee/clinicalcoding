
from module1_ingestion.sliding_window import SlidingWindowChunker


def test_sliding_window_creates_multiple_windows():
    text = "Patient has fever and cough. " * 600

    chunker = SlidingWindowChunker(
        window_size=512,
        stride=256
    )

    document = chunker.chunk("DOC001", text)

    assert document.document_id == "DOC001"
    assert len(document.windows) > 1


def test_window_offsets_are_valid():
    text = "Patient has fever and cough. " * 600

    chunker = SlidingWindowChunker(
        window_size=512,
        stride=256
    )

    document = chunker.chunk("DOC001", text)

    for window in document.windows:
        assert window.start_token_offset >= 0
        assert window.end_token_offset > window.start_token_offset

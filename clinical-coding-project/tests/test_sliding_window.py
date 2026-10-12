from module1_ingestion.sliding_window import SlidingWindowChunker, aggregate_max, aggregate_mean
from module1_ingestion.preprocessing import normalize, split_sections


def test_normalize_collapses_whitespace():
    raw = "line one\r\n\r\n\r\nline   two"
    result = normalize(raw)
    assert "\r" not in result
    assert "\n\n\n" not in result
    assert "line   two" not in result  # collapsed to single space


def test_split_sections_detects_headers():
    text = "DIAGNOSIS:\nSepsis\n\nHOSPITAL COURSE:\nImproved.\n"
    sections = split_sections(text)
    assert "DIAGNOSIS" in sections
    assert "HOSPITAL COURSE" in sections
    assert sections["DIAGNOSIS"] == "Sepsis"


def test_chunker_produces_overlapping_windows():
    chunker = SlidingWindowChunker(window_size=10, stride=5)
    text = " ".join(f"word{i}" for i in range(30))  # 30 "tokens" via whitespace fallback
    doc = chunker.chunk("doc-1", text)
    assert len(doc.windows) > 1
    # consecutive windows should overlap by (window_size - stride) words
    assert doc.windows[1].start_token_offset == doc.windows[0].start_token_offset + 5


def test_aggregate_max_and_mean():
    probs = [0.2, 0.9, 0.5]
    assert aggregate_max(probs) == 0.9
    assert abs(aggregate_mean(probs) - 0.5333333) < 1e-4

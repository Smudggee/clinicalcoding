
from pathlib import Path

from module1_ingestion.stt.malayalam_transcriber import transcribe_audio


AUDIO_FILE = Path("data/audio/Malayalam_test.m4a")


def test_malayalam_transcription_returns_expected_fields():
    result = transcribe_audio(AUDIO_FILE)

    assert isinstance(result, dict)
    assert {"text", "language", "language_probability"} <= result.keys()
    assert result["language"] == "ml"
    assert isinstance(result["text"], str)
    assert result["text"].strip()
    assert 0.0 <= result["language_probability"] <= 1.0

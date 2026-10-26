
import pytest

from module1_ingestion.stt.whisper_service import (
    WhisperTranscriptionService,
)


def test_missing_audio_file_raises_error():
    service = WhisperTranscriptionService(
        model_path="models/malayalam-whisper"
    )

    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        service.transcribe(
            "data/audio/does_not_exist.m4a",
            language="ml",
        )

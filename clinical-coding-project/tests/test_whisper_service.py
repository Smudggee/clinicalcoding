from pathlib import Path
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


def test_whisper_service_initialization_options():
    service_default = WhisperTranscriptionService()
    assert service_default.model_size == "large-v3"
    assert service_default.device == "cpu"
    assert service_default.backend == "faster-whisper"

    service_small = WhisperTranscriptionService(model_size="small", device="cpu")
    assert service_small.model_size == "small"

    service_alt = WhisperTranscriptionService(backend="alternative")
    assert service_alt.backend == "alternative"


def test_unsupported_backend_raises_error(tmp_path):
    dummy_file = tmp_path / "dummy.wav"
    dummy_file.write_text("dummy audio data")

    service = WhisperTranscriptionService(backend="unsupported_backend")
    with pytest.raises(ValueError, match="Unsupported transcription backend"):
        service.transcribe(dummy_file)

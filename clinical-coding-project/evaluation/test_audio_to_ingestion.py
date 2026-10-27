
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from module1_ingestion.stt.whisper_service import WhisperTranscriptionService
from module1_ingestion.preprocessing import normalize
from module1_ingestion.sliding_window import SlidingWindowChunker


def test_audio_to_ingestion():
    audio_path = ROOT / "data" / "audio" / "sample_01.m4a"

    assert audio_path.is_file(), f"Sample audio not found: {audio_path}"

    service = WhisperTranscriptionService(
        backend="alternative",
        device="cpu",
    )

    result = service.transcribe(audio_path, language="ml")

    assert result["transcript"].strip(), "Transcription is empty"

    normalized_text = normalize(result["transcript"])
    assert normalized_text.strip(), "Normalized text is empty"

    chunker = SlidingWindowChunker()
    ingested = chunker.chunk(
        document_id="audio-sample-001",
        text=normalized_text,
    )

    assert len(ingested.windows) > 0, "No ingestion windows generated"

    print("Transcript:", result["transcript"])
    print("Normalized text:", normalized_text)
    print("Number of windows:", len(ingested.windows))

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from module1_ingestion.stt.whisper_service import (
    WhisperTranscriptionService,
)

AUDIO_FILE = ROOT / "data" / "audio" / "sample_01.m4a"

service = WhisperTranscriptionService(
    backend="alternative",
    device="cpu",
)

result = service.transcribe(AUDIO_FILE, language="ml")

print("\n--- Integrated Alternative Model Test ---")
print("Language:", result["language"])
print("Transcript:", result["transcript"])
print("Segments:", result["segments"])
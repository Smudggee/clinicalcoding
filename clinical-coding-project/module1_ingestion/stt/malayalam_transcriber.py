
"""Malayalam speech transcription using a local faster-whisper model."""

from pathlib import Path

from faster_whisper import WhisperModel


MODEL_PATH = (
    Path(__file__).resolve().parents[3]
    / "models"
    / "malayalam-whisper"
)

_model = None


def get_model():
    """Load the model once and reuse it."""
    global _model

    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Malayalam Whisper model not found: {MODEL_PATH}"
            )

        _model = WhisperModel(
            str(MODEL_PATH),
            device="cpu",
            compute_type="int8",
        )

    return _model


def transcribe_audio(audio_path: str | Path) -> dict:
    """Transcribe an audio file and return a structured result."""
    audio_path = Path(audio_path)

    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = get_model()

    segments, info = model.transcribe(
        str(audio_path),
        language="ml",
        beam_size=5,
        vad_filter=False,
    )

    text = " ".join(segment.text.strip() for segment in segments).strip()

    return {
        "text": text,
        "language": info.language,
        "language_probability": info.language_probability,
    }

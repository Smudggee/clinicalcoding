
"""Local speech-to-text service using faster-whisper."""

from pathlib import Path

from faster_whisper import WhisperModel


class WhisperTranscriptionService:
    """Transcribe audio files locally using Whisper."""

    def __init__(self, model_size="small", device="cpu"):
        self.model_size = model_size
        self.device = device
        self.model = None

    def load_model(self):
        """Load the model only when transcription is requested."""
        if self.model is None:
            compute_type = "int8" if self.device == "cpu" else "float16"

            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=compute_type,
            )

        return self.model

    def transcribe(self, audio_path, language=None):
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to an audio file supported by faster-whisper.
            language: Optional language code, e.g. 'ml' for Malayalam
                      or 'en' for English. None enables language detection.

        Returns:
            A dictionary containing the detected language and transcript.
        """
        audio_path = Path(audio_path)

        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self.load_model()

        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            vad_filter=True,
        )

        segment_results = []
        for segment in segments:
            segment_results.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip(),
            })

        transcript = " ".join(
            segment["text"] for segment in segment_results
        ).strip()

        return {
            "audio_path": str(audio_path),
            "language": info.language,
            "language_probability": round(info.language_probability, 4),
            "transcript": transcript,
            "segments": segment_results,
        }


if __name__ == "__main__":
    print("Whisper transcription service is ready.")
    print("The model will download when the first transcription is requested.")


"""Local speech-to-text service supporting two Whisper backends."""

from pathlib import Path
import subprocess
import tempfile

from faster_whisper import WhisperModel
from transformers import pipeline


# Project root: clinical-coding-project/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

MALAYALAM_MODEL_PATH = (
    PROJECT_ROOT.parent / "models" / "malayalam-whisper"
)

ALTERNATIVE_MODEL_NAME = "sajilck/whisper-small-malayalam-v2"

# FFmpeg executable installed through WinGet on Windows.
FFMPEG_PATH = (
    Path.home()
    / "AppData"
    / "Local"
    / "Microsoft"
    / "WinGet"
    / "Packages"
    / "Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-9.0.2-full_build-shared"
    / "bin"
    / "ffmpeg.exe"
)


class WhisperTranscriptionService:
    """Transcribe audio using faster-whisper or Transformers."""

    def __init__(
        self,
        model_size="small",
        device="cpu",
        model_path=None,
        backend="faster-whisper",
        alternative_model_name=ALTERNATIVE_MODEL_NAME,
    ):
        self.model_size = model_size
        self.device = device
        self.model_path = (
            Path(model_path) if model_path else None
        )
        self.backend = backend
        self.alternative_model_name = alternative_model_name

        self.model = None
        self.alternative_model = None

    def load_alternative_model(self):
        """Load the alternative Malayalam model on demand."""
        if self.alternative_model is None:
            device_id = 0 if self.device == "cuda" else -1

            self.alternative_model = pipeline(
                "automatic-speech-recognition",
                model=self.alternative_model_name,
                device=device_id,
            )

        return self.alternative_model

    def load_model(self):
        """Load the existing faster-whisper model on demand."""
        if self.model is None:
            selected_model = (
                str(self.model_path)
                if self.model_path
                else self.model_size
            )

            if self.model_path and not self.model_path.exists():
                raise FileNotFoundError(
                    f"Model directory not found: {self.model_path}"
                )

            compute_type = (
                "int8" if self.device == "cpu" else "float16"
            )

            self.model = WhisperModel(
                selected_model,
                device=self.device,
                compute_type=compute_type,
            )

        return self.model

    def transcribe(self, audio_path, language=None):
        """Transcribe audio and return a consistent result structure."""
        audio_path = Path(audio_path)

        if not audio_path.is_file():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        # Alternative Malayalam Transformers backend.
        if self.backend == "alternative":
            alternative_model = self.load_alternative_model()

            if not FFMPEG_PATH.is_file():
                raise FileNotFoundError(
                    f"FFmpeg executable not found: {FFMPEG_PATH}"
                )

            # Convert audio to a temporary WAV file.
            with tempfile.TemporaryDirectory() as temp_dir:
                wav_path = Path(temp_dir) / "audio.wav"

                subprocess.run(
                    [
                        str(FFMPEG_PATH),
                        "-y",
                        "-i", str(audio_path),
                        "-ac", "1",
                        "-ar", "16000",
                        "-c:a", "pcm_s16le",
                        str(wav_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                generation_options = {
                    "task": "transcribe",
                }

                if language in (None, "ml", "malayalam"):
                    generation_options["language"] = "malayalam"
                else:
                    generation_options["language"] = language

                result = alternative_model(
                    str(wav_path),
                    generate_kwargs=generation_options,
                )

            transcript = result["text"].strip()

            return {
                "audio_path": str(audio_path),
                "language": language or "ml",
                "language_probability": None,
                "transcript": transcript,
                "segments": [
                    {
                        "start": None,
                        "end": None,
                        "text": transcript,
                    }
                ],
            }

        # Existing faster-whisper backend.
        elif self.backend == "faster-whisper":
            model = self.load_model()

            whisper_language = (
                "ml" if language == "malayalam" else language
            )

            segments, info = model.transcribe(
                str(audio_path),
                language=whisper_language,
                task="transcribe",
                beam_size=5,
                temperature=0.0,
                vad_filter=False,
                condition_on_previous_text=False,
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
                "language_probability": round(
                    info.language_probability, 4
                ),
                "transcript": transcript,
                "segments": segment_results,
            }

        else:
            raise ValueError(
                f"Unsupported transcription backend: {self.backend}"
            )


if __name__ == "__main__":
    print("Whisper transcription service is ready.")

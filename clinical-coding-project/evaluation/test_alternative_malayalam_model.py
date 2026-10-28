
from pathlib import Path
import subprocess

from transformers import pipeline

ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / "data" / "audio"
TEMP_DIR = ROOT / "evaluation" / "temp_wav"
MODEL_NAME = "sajilck/whisper-small-malayalam-v2"

FFMPEG = (
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

SAMPLES = [
    "sample_01.m4a",
    "sample_02.m4a",
    "sample_03.m4a",
    "sample_04.m4a",
    "sample_05.m4a",
]


def convert_to_wav(source, destination):
    """Convert audio to mono, 16 kHz WAV."""
    subprocess.run(
        [
            str(FFMPEG),
            "-y",
            "-i", str(source),
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            str(destination),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main():
    if not FFMPEG.is_file():
        raise FileNotFoundError(f"FFmpeg not found: {FFMPEG}")

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading alternative Malayalam model...")
    asr = pipeline(
        "automatic-speech-recognition",
        model=MODEL_NAME,
        device="cpu",
    )

    for filename in SAMPLES:
        source = AUDIO_DIR / filename
        wav_path = TEMP_DIR / f"{source.stem}.wav"

        if not source.is_file():
            print(f"\nMissing audio: {source}")
            continue

        print(f"\nConverting {filename} to WAV...")
        convert_to_wav(source, wav_path)

        print(f"Transcribing {filename}...")
        result = asr(
            str(wav_path),
            generate_kwargs={
                "language": "malayalam",
                "task": "transcribe",
                "max_new_tokens": 444,
            },
        )

        print("Prediction:", result["text"].strip())

    print("\nExperiment finished.")
    print(f"Temporary WAV files: {TEMP_DIR}")


if __name__ == "__main__":
    main()

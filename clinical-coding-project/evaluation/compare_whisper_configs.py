
from pathlib import Path
import csv

from faster_whisper import WhisperModel
from jiwer import wer, cer


ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / "data" / "audio"
MODEL_PATH = ROOT.parent / "models" / "malayalam-whisper"
OUTPUT_FILE = ROOT / "evaluation" / "whisper_config_comparison.csv"

SAMPLES = [
    ("sample_01.m4a", "രോഗിക്ക് മൂന്ന് ദിവസമായി പനിയും ചുമയും ഉണ്ട്."),
    ("sample_02.m4a", "എനിക്ക് ഇന്നലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്."),
    ("sample_03.m4a", "ഇന്ന് രാവിലെ ഞാൻ ആശുപത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു."),
    ("sample_04.m4a", "ഡോക്ടർ എന്റെ രക്തസമ്മർദ്ദം പരിശോധിച്ച് മരുന്ന് നിർദ്ദേശിച്ചു."),
    ("sample_05.m4a", "എനിക്ക് ഒ.പി.യിൽ രജിസ്റ്റർ ചെയ്യണം, ഡോക്ടറെ കാണാൻ ടോക്കൺ വേണം."),
]


def transcribe(model, audio_path, beam_size):
    segments, info = model.transcribe(
        str(audio_path),
        language="ml",
        task="transcribe",
        beam_size=beam_size,
        temperature=0.0,
        vad_filter=False,
        condition_on_previous_text=False,
    )
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return text


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model directory not found: {MODEL_PATH}")

    model = WhisperModel(
        str(MODEL_PATH),
        device="cpu",
        compute_type="int8",
    )

    rows = []

    for filename, reference in SAMPLES:
        audio_path = AUDIO_DIR / filename

        if not audio_path.is_file():
            print(f"Skipping missing file: {audio_path}")
            continue

        for config_name, beam_size in [
            ("baseline_beam5", 5),
            ("experiment_beam10", 10),
        ]:
            prediction = transcribe(model, audio_path, beam_size)

            row = {
                "sample": filename,
                "configuration": config_name,
                "beam_size": beam_size,
                "WER_percent": round(wer([reference], [prediction]) * 100, 2),
                "CER_percent": round(cer([reference], [prediction]) * 100, 2),
                "prediction": prediction,
            }
            rows.append(row)

            print(
                f"{filename} | {config_name} | "
                f"WER={row['WER_percent']:.2f}% | "
                f"CER={row['CER_percent']:.2f}%"
            )
            print(f"  Prediction: {prediction}")

    if not rows:
        raise RuntimeError("No audio samples were evaluated.")

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nComparison saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

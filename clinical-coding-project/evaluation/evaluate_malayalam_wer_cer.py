
import csv
from pathlib import Path

from jiwer import wer, cer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "evaluation" / "malayalam_evaluation.csv"

# Existing reference transcripts and Whisper predictions
SAMPLES = [
    {
        "sample": "sample_01",
        "reference": "രോഗിക്ക് മൂന്ന് ദിവസമായി പനിയും ചുമയും ഉണ്ട്.",
        "prediction": "രോഗിക്ക് മൂണ്ണ് ദിവസംമായി പനയും ചുമയും ഉണ്ട്.",
    },
    {
        "sample": "sample_02",
        "reference": "എനിക്ക് ഇന്നലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്.",
        "prediction": "എനിക്ക് ഇന്നിലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്.",
    },
    {
        "sample": "sample_03",
        "reference": "ഇന്ന് രാവിലെ ഞാൻ ആശുപത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു.",
        "prediction": "ഇന്ന് രാവിലെ ഞാൻ ആശുവത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു.",
    },
    {
        "sample": "sample_04",
        "reference": "ഡോക്ടർ എന്റെ രക്തസമ്മർദ്ദം പരിശോധിച്ച് മരുന്ന് നിർദ്ദേശിച്ചു.",
        "prediction": "ഡോക്ടർ എണ്ടെ രക്ത സമ്മർതം പരിഷോധിച്ച് മരിന്ന് നിർദ്ദേശിച്ചു.",
    },
    {
        "sample": "sample_05",
        "reference": "എനിക്ക് ഒ.പി.യിൽ രജിസ്റ്റർ ചെയ്യണം, ഡോക്ടറെ കാണാൻ ടോക്കൺ വേണം.",
        "prediction": "എനിക്ക് ഓപ്പിയിൽ റെജിസ്റ്റർ ചെയ്യണം. ഡോക്ടറെ കാണാൻ ടോക്കൻ വേണം.",
    },
]


def main():
    references = [item["reference"] for item in SAMPLES]
    predictions = [item["prediction"] for item in SAMPLES]

    rows = []

    for item in SAMPLES:
        sample_wer = wer([item["reference"]], [item["prediction"]])
        sample_cer = cer([item["reference"]], [item["prediction"]])

        rows.append({
            "sample": item["sample"],
            "WER_percent": round(sample_wer * 100, 2),
            "CER_percent": round(sample_cer * 100, 2),
        })

    overall_wer = wer(references, predictions)
    overall_cer = cer(references, predictions)

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["sample", "WER_percent", "CER_percent"],
        )
        writer.writeheader()
        writer.writerows(rows)

        writer.writerow({
            "sample": "OVERALL",
            "WER_percent": round(overall_wer * 100, 2),
            "CER_percent": round(overall_cer * 100, 2),
        })

    print("\nMalayalam Transcription Evaluation")
    print("-" * 45)

    for row in rows:
        print(
            f'{row["sample"]}: '
            f'WER={row["WER_percent"]:.2f}%, '
            f'CER={row["CER_percent"]:.2f}%'
        )

    print("-" * 45)
    print(f"Overall WER: {overall_wer * 100:.2f}%")
    print(f"Overall CER: {overall_cer * 100:.2f}%")
    print(f"\nResults saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

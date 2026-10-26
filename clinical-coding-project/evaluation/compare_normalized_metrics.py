
import csv
import re
import unicodedata
from pathlib import Path

from jiwer import wer, cer


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT / "evaluation" / "normalized_metrics_comparison.csv"

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


def normalize_for_evaluation(text):
    """Normalize Unicode and punctuation for a secondary comparison."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def main():
    rows = []

    for item in SAMPLES:
        reference = item["reference"]
        prediction = item["prediction"]

        normalized_reference = normalize_for_evaluation(reference)
        normalized_prediction = normalize_for_evaluation(prediction)

        rows.append({
            "sample": item["sample"],
            "original_WER_percent": round(
                wer([reference], [prediction]) * 100, 2
            ),
            "normalized_WER_percent": round(
                wer([normalized_reference], [normalized_prediction]) * 100, 2
            ),
            "original_CER_percent": round(
                cer([reference], [prediction]) * 100, 2
            ),
            "normalized_CER_percent": round(
                cer([normalized_reference], [normalized_prediction]) * 100, 2
            ),
        })

    references = [item["reference"] for item in SAMPLES]
    predictions = [item["prediction"] for item in SAMPLES]

    normalized_references = [
        normalize_for_evaluation(text) for text in references
    ]
    normalized_predictions = [
        normalize_for_evaluation(text) for text in predictions
    ]

    overall = {
        "sample": "OVERALL",
        "original_WER_percent": round(wer(references, predictions) * 100, 2),
        "normalized_WER_percent": round(
            wer(normalized_references, normalized_predictions) * 100, 2
        ),
        "original_CER_percent": round(cer(references, predictions) * 100, 2),
        "normalized_CER_percent": round(
            cer(normalized_references, normalized_predictions) * 100, 2
        ),
    }
    rows.append(overall)

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        print(row)

    print(f"\nResults saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

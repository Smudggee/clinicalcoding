
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT / "evaluation" / "transcription_error_analysis.csv"

SAMPLES = [
    {
        "sample": "sample_01",
        "reference": "രോഗിക്ക് മൂന്ന് ദിവസമായി പനിയും ചുമയും ഉണ്ട്.",
        "prediction": "രോഗിക്ക് മൂണ്ണ് ദിവസംമായി പനയും ചുമയും ഉണ്ട്.",
        "observation": "Spelling differences in number, duration and symptom words",
        "priority": "Review",
    },
    {
        "sample": "sample_02",
        "reference": "എനിക്ക് ഇന്നലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്.",
        "prediction": "എനിക്ക് ഇന്നിലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്.",
        "observation": "Spelling difference in the word for yesterday",
        "priority": "Low",
    },
    {
        "sample": "sample_03",
        "reference": "ഇന്ന് രാവിലെ ഞാൻ ആശുപത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു.",
        "prediction": "ഇന്ന് രാവിലെ ഞാൻ ആശുവത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു.",
        "observation": "Spelling difference in the hospital term",
        "priority": "Review",
    },
    {
        "sample": "sample_04",
        "reference": "ഡോക്ടർ എന്റെ രക്തസമ്മർദ്ദം പരിശോധിച്ച് മരുന്ന് നിർദ്ദേശിച്ചു.",
        "prediction": "ഡോക്ടർ എണ്ടെ രക്ത സമ്മർതം പരിഷോധിച്ച് മരിന്ന് നിർദ്ദേശിച്ചു.",
        "observation": "Multiple spelling differences and a word-boundary difference in medical text",
        "priority": "High",
    },
    {
        "sample": "sample_05",
        "reference": "എനിക്ക് ഒ.പി.യിൽ രജിസ്റ്റർ ചെയ്യണം, ഡോക്ടറെ കാണാൻ ടോക്കൺ വേണം.",
        "prediction": "എനിക്ക് ഓപ്പിയിൽ റെജിസ്റ്റർ ചെയ്യണം. ഡോക്ടറെ കാണാൻ ടോക്കൻ വേണം.",
        "observation": "Differences in abbreviation formatting and spelling",
        "priority": "Review",
    },
]


def main():
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "sample",
                "reference",
                "prediction",
                "observation",
                "priority",
            ],
        )
        writer.writeheader()
        writer.writerows(SAMPLES)

    print("Transcription error analysis")
    print("-" * 45)

    for item in SAMPLES:
        print(f"\n{item['sample']} — {item['priority']}")
        print(f"Reference:  {item['reference']}")
        print(f"Prediction: {item['prediction']}")
        print(f"Observation: {item['observation']}")

    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()


import csv
from pathlib import Path
from jiwer import wer, cer

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT / "evaluation" / "alternative_model_comparison.csv"

references = [
    "രോഗിക്ക് മൂന്ന് ദിവസമായി പനിയും ചുമയും ഉണ്ട്.",
    "എനിക്ക് ഇന്നലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്.",
    "ഇന്ന് രാവിലെ ഞാൻ ആശുപത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു.",
    "ഡോക്ടർ എന്റെ രക്തസമ്മർദ്ദം പരിശോധിച്ച് മരുന്ന് നിർദ്ദേശിച്ചു.",
    "എനിക്ക് ഒ.പി.യിൽ രജിസ്റ്റർ ചെയ്യണം, ഡോക്ടറെ കാണാൻ ടോക്കൺ വേണം.",
]

original_predictions = [
    "രോഗിക്ക് മൂണ്ണ് ദിവസംമായി പനയും ചുമയും ഉണ്ട്.",
    "എനിക്ക് ഇന്നിലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്.",
    "ഇന്ന് രാവിലെ ഞാൻ ആശുവത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു.",
    "ഡോക്ടർ എണ്ടെ രക്ത സമ്മർതം പരിഷോധിച്ച് മരിന്ന് നിർദ്ദേശിച്ചു.",
    "എനിക്ക് ഓപ്പിയിൽ റെജിസ്റ്റർ ചെയ്യണം. ഡോക്ടറെ കാണാൻ ടോക്കൻ വേണം.",
]

alternative_predictions = [
    "രോഗിക്ക് മൂന്ന് ദിവസമായി പനിയും ചുമയും ഉണ്ട്.",
    "എനിക്ക് ഇന്നലെ രാത്രി മുതല് ശക്തമായ തനവേദനയുണ്ട്",
    "ഇന്ന് രാവിലെ ഞാന് ആശുപത്രിയില് എത്തി ഡോക്ടറെ കണ്ടു",
    "ഡോക്ടർ എന്റെ രക്തസമ്മർദ്ദം പരിശോധിച്ച് മരുന്ന് നിർദ്ദേശിച്ചു.",
    "എനിക്ക് ഒപ്പിയിൽ രജിസ്റ്റർ ചെയ്യണം ഡോക്ടറെ കാണാൻ ടോക്കൺ വേണം.",
]

rows = []

for i, (ref, original, alternative) in enumerate(
    zip(references, original_predictions, alternative_predictions),
    start=1,
):
    rows.append({
        "sample": f"sample_{i:02d}",
        "original_WER": round(wer(ref, original) * 100, 2),
        "original_CER": round(cer(ref, original) * 100, 2),
        "alternative_WER": round(wer(ref, alternative) * 100, 2),
        "alternative_CER": round(cer(ref, alternative) * 100, 2),
        "reference": ref,
        "original_prediction": original,
        "alternative_prediction": alternative,
    })

# Corpus-level metrics across all five samples
reference_corpus = references
original_corpus = original_predictions
alternative_corpus = alternative_predictions

rows.append({
    "sample": "OVERALL",
    "original_WER": round(wer(reference_corpus, original_corpus) * 100, 2),
    "original_CER": round(cer(reference_corpus, original_corpus) * 100, 2),
    "alternative_WER": round(wer(reference_corpus, alternative_corpus) * 100, 2),
    "alternative_CER": round(cer(reference_corpus, alternative_corpus) * 100, 2),
    "reference": "",
    "original_prediction": "",
    "alternative_prediction": "",
})

with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

overall = rows[-1]

print("\nMODEL COMPARISON")
print("-" * 45)
print(f"Original model WER:    {overall['original_WER']}%")
print(f"Alternative model WER: {overall['alternative_WER']}%")
print(f"Original model CER:    {overall['original_CER']}%")
print(f"Alternative model CER: {overall['alternative_CER']}%")

print(f"\nResults saved to: {OUTPUT_FILE}")

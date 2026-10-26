
from jiwer import wer, cer

# Reference sentences and Whisper predictions
samples = [
    {
        "reference": "രോഗിക്ക് മൂന്ന് ദിവസമായി പനിയും ചുമയും ഉണ്ട്.",
        "prediction": "രോഗിക്ക് മൂണ്ണ് ദിവസംമായി പനയും ചുമയും ഉണ്ട്.",
    },
    {
        "reference": "എനിക്ക് ഇന്നലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്.",
        "prediction": "എനിക്ക് ഇന്നിലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്.",
    },
    {
        "reference": "ഇന്ന് രാവിലെ ഞാൻ ആശുപത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു.",
        "prediction": "ഇന്ന് രാവിലെ ഞാൻ ആശുവത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു.",
    },
    {
        "reference": "ഡോക്ടർ എന്റെ രക്തസമ്മർദ്ദം പരിശോധിച്ച് മരുന്ന് നിർദ്ദേശിച്ചു.",
        "prediction": "ഡോക്ടർ എണ്ടെ രക്ത സമ്മർതം പരിഷോധിച്ച് മരിന്ന് നിർദ്ദേശിച്ചു.",
    },
    {
        "reference": "എനിക്ക് ഒ.പി.യിൽ രജിസ്റ്റർ ചെയ്യണം, ഡോക്ടറെ കാണാൻ ടോക്കൺ വേണം.",
        "prediction": "എനിക്ക് ഓപ്പിയിൽ റെജിസ്റ്റർ ചെയ്യണം. ഡോക്ടറെ കാണാൻ ടോക്കൻ വേണം.",
    },
]

references = [sample["reference"] for sample in samples]
predictions = [sample["prediction"] for sample in samples]

print("INDIVIDUAL RESULTS")
print("-" * 40)

for i, sample in enumerate(samples, start=1):
    sample_wer = wer(sample["reference"], sample["prediction"])
    sample_cer = cer(sample["reference"], sample["prediction"])

    print(f"Sample {i}: WER = {sample_wer:.2%}, CER = {sample_cer:.2%}")

# Combined rates across all five samples
combined_wer = wer(references, predictions)
combined_cer = cer(references, predictions)

print("\nCOMBINED RESULTS")
print("-" * 40)
print(f"Total samples: {len(samples)}")
print(f"Combined WER: {combined_wer:.2%}")
print(f"Combined CER: {combined_cer:.2%}")
print(f"Word accuracy estimate (1 - WER): {(1 - combined_wer):.2%}")

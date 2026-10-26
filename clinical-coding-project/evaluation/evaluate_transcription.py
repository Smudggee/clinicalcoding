from jiwer import wer, cer
reference = "എനിക്ക് ഒ.പി.യിൽ രജിസ്റ്റർ ചെയ്യണം, ഡോക്ടറെ കാണാൻ ടോക്കൺ വേണം."
prediction = "എനിക്ക് ഓപ്പിയിൽ റെജിസ്റ്റർ ചെയ്യണം. ഡോക്ടറെ കാണാൻ ടോക്കൻ വേണം."

word_error_rate = wer(reference, prediction)
character_error_rate = cer(reference, prediction)

print("Reference:", reference)
print("Prediction:", prediction)
print(f"WER: {word_error_rate:.2%}")
print(f"CER: {character_error_rate:.2%}")
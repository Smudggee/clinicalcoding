
from preprocessing import normalize, split_sections

sample_text = """
HISTORY OF PRESENT ILLNESS:
Patient has fever.


DISCHARGE DIAGNOSIS:
Pneumonia.
"""

cleaned_text = normalize(sample_text)
print("CLEANED TEXT:")
print(cleaned_text)

sections = split_sections(cleaned_text)
print("\nSECTIONS:")
print(sections)
print("\nTEST WITHOUT HEADERS:")

plain_text = "Patient reports headache and nausea."
result = split_sections(normalize(plain_text))

print(result)
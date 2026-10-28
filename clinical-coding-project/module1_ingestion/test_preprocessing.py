
from module1_ingestion.preprocessing import normalize, split_sections


def test_normalize_collapses_whitespace():
    sample_text = "Patient has   fever.\n\n\nDischarge diagnosis: Pneumonia."
    cleaned_text = normalize(sample_text)

    assert isinstance(cleaned_text, str)
    assert "Patient has fever." in cleaned_text
    assert "\n\n\n" not in cleaned_text


def test_split_sections_detects_headers():
    sample_text = """
HISTORY OF PRESENT ILLNESS:
Patient has fever.

DISCHARGE DIAGNOSIS:
Pneumonia.
"""

    cleaned_text = normalize(sample_text)
    sections = split_sections(cleaned_text)

    assert sections
    assert isinstance(sections, (dict, list))


def test_split_sections_without_headers():
    plain_text = "Patient reports headache and nausea."
    result = split_sections(normalize(plain_text))

    assert result

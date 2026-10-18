
"""Build an ICD-code label map from training records only."""

import json
from collections import Counter
from pathlib import Path


def build_label_vocab(training_records, output_dir):
    """
    training_records: list of records containing a 'codes' list.
    output_dir: directory where label_map.json and class_frequencies.json
                will be saved.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frequencies = Counter()

    for record in training_records:
        for code in set(record["codes"]):
            frequencies[code] += 1

    # Deterministic mapping: codes are sorted alphabetically.
    label_map = {
        code: index
        for index, code in enumerate(sorted(frequencies))
    }

    with open(output_dir / "label_map.json", "w", encoding="utf-8") as f:
        json.dump(label_map, f, indent=2)

    with open(
        output_dir / "class_frequencies.json", "w", encoding="utf-8"
    ) as f:
        json.dump(dict(sorted(frequencies.items())), f, indent=2)

    return label_map, frequencies

if __name__ == "__main__":
    # Synthetic examples for software testing only.
    training_records = [
        {"text": "Synthetic note A", "codes": ["SYNTH_A", "SYNTH_B"]},
        {"text": "Synthetic note B", "codes": ["SYNTH_A"]},
        {"text": "Synthetic note C", "codes": ["SYNTH_B"]},
    ]

    output_dir = Path(__file__).parent / "test_output"

    label_map, frequencies = build_label_vocab(
        training_records, output_dir
    )

    print("Label map:", label_map)
    print("Class frequencies:", dict(frequencies))
    print("Output folder:", output_dir)

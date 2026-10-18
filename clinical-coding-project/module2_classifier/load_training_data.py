
"""Load prepared training records for Module 2."""

import json
from pathlib import Path

from module1_ingestion.training_examples import make_training_examples


def load_training_data(data_dir, split="train"):
    data_dir = Path(data_dir)

    split_path = data_dir / f"{split}.json"
    label_map_path = data_dir / "label_map.json"

    if not split_path.exists():
        raise FileNotFoundError(f"Dataset split not found: {split_path}")

    if not label_map_path.exists():
        raise FileNotFoundError(f"Label map not found: {label_map_path}")

    with open(split_path, encoding="utf-8") as f:
        records = json.load(f)

    with open(label_map_path, encoding="utf-8") as f:
        label_map = json.load(f)

    if not isinstance(records, list):
        raise ValueError("Dataset split must contain a list of records.")

    if not isinstance(label_map, dict) or not label_map:
        raise ValueError("Label map must be a non-empty dictionary.")

    # Prevent accidental use of our known synthetic test labels.
    synthetic_codes = {"SYNTH_A", "SYNTH_B"}
    if synthetic_codes.intersection(label_map):
        raise ValueError(
            "Synthetic test labels detected. Use a properly prepared "
            "clinical dataset before training."
        )

    examples = make_training_examples(records)

    print(f"Loaded split: {split}")
    print(f"Documents: {len(records)}")
    print(f"Window examples: {len(examples)}")
    print(f"Labels: {len(label_map)}")

    return examples, label_map


if __name__ == "__main__":
    from pathlib import Path

    project_root = Path(__file__).resolve().parent.parent
    test_dir = project_root / "evaluation" / "prepared_test_output"

    try:
        load_training_data(test_dir)
    except ValueError as exc:
        print("PASS: Safety check worked.")
        print(exc)

"""Prepare dataset splits and a training-only label map."""

import json
from pathlib import Path

from evaluation.split_dataset import split_records
from evaluation.label_vocab import build_label_vocab


def prepare_dataset(input_path, output_dir):
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path, encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise ValueError("Input JSON must contain a list of records.")

    
    train, validation, test = split_records(records)

    # Build the label map using training records only.
    label_map, frequencies = build_label_vocab(train, output_dir)

    # Detect labels that were not present in the training split.
    training_codes = set(label_map)

    for split_name, split_records_list in [
        ("Validation", validation),
        ("Test", test),
    ]:
        split_codes = {
            code
            for record in split_records_list
            for code in record["codes"]
        }

        unseen_codes = split_codes - training_codes

        if unseen_codes:
            print(
                f"WARNING: {split_name} contains codes absent "
                f"from training: {sorted(unseen_codes)}"
            )
        else:
            print(f"PASS: All {split_name.lower()} codes occur in training.")


    # Collect labels from each split.
    validation_codes = {
        code
        for record in validation
        for code in record["codes"]
    }

    test_codes = {
        code
        for record in test
        for code in record["codes"]
    }

    unseen_validation = sorted(validation_codes - training_codes)
    unseen_test = sorted(test_codes - training_codes)

    # Save a quality report for inspection.
    report = {
        "training_labels": sorted(training_codes),
        "validation_labels": sorted(validation_codes),
        "test_labels": sorted(test_codes),
        "unseen_validation_labels": unseen_validation,
        "unseen_test_labels": unseen_test,
        "synthetic_data": True,
    }

    report_path = output_dir / "dataset_quality_report.json"

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Dataset quality report saved to: {report_path}")

    splits = {
        "train.json": train,
        "validation.json": validation,
        "test.json": test,
    }

    for filename, split in splits.items():
        with open(output_dir / filename, "w", encoding="utf-8") as f:
            json.dump(split, f, indent=2)

    print(f"Total records: {len(records)}")
    print(f"Train: {len(train)}")
    print(f"Validation: {len(validation)}")
    print(f"Test: {len(test)}")
    print(f"Training labels: {len(label_map)}")
    print("Dataset preparation completed.")


if __name__ == "__main__":
    # Clearly synthetic data for testing the pipeline only.
    sample_records = [
        {
            "patient_id": f"P{i}",
            "document_id": f"DOC{i}",
            "text": f"Synthetic clinical note {i}",
            "codes": ["SYNTH_A" if i % 2 == 0 else "SYNTH_B"],
        }
        for i in range(1, 31)
    ]

    base_dir = Path(__file__).parent
    input_path = base_dir / "synthetic_records.json"
    output_dir = base_dir / "prepared_test_output"

    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(sample_records, f, indent=2)

    prepare_dataset(input_path, output_dir)

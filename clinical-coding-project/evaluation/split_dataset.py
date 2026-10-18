
"""Split records by patient to prevent data leakage."""

from sklearn.model_selection import GroupShuffleSplit


def split_records(records, test_size=0.2, val_size=0.1, random_state=42):
    """Validate records and split them into train, validation and test sets."""

    if not isinstance(records, list) or not records:
        raise ValueError("Records must be a non-empty list.")

    if not 0 < test_size < 1 or not 0 < val_size < 1:
        raise ValueError("Split sizes must be between 0 and 1.")

    if test_size + val_size >= 1:
        raise ValueError("test_size + val_size must be less than 1.")

    seen_records = set()
    patient_ids = set()

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index} must be a dictionary.")

        patient_id = record.get("patient_id")
        if not isinstance(patient_id, str) or not patient_id.strip():
            raise ValueError(
                f"Record {index} must have a non-empty patient_id."
            )

        text = record.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                f"Record {index} must have non-empty text."
            )

        codes = record.get("codes")
        if (
            not isinstance(codes, list)
            or not codes
            or any(not isinstance(code, str) or not code.strip()
                   for code in codes)
        ):
            raise ValueError(
                f"Record {index} must have a non-empty list of valid codes."
            )

        # Detect exact duplicate records.
        record_key = (
            patient_id.strip(),
            text.strip(),
            tuple(sorted(set(codes))),
        )
        if record_key in seen_records:
            raise ValueError(f"Duplicate record detected at index {index}.")

        seen_records.add(record_key)
        patient_ids.add(patient_id.strip())

    # Two stages of splitting require enough distinct patient groups.
    if len(patient_ids) < 3:
        raise ValueError(
            "At least 3 distinct patients are required for three splits."
        )

    groups = [r["patient_id"].strip() for r in records]

    first = GroupShuffleSplit(
        n_splits=1, test_size=test_size, random_state=random_state
    )
    train_val_idx, test_idx = next(first.split(records, groups=groups))

    train_val = [records[i] for i in train_val_idx]
    test = [records[i] for i in test_idx]

    relative_val_size = val_size / (1 - test_size)
    remaining_groups = [r["patient_id"].strip() for r in train_val]

    if len(set(remaining_groups)) < 2:
        raise ValueError(
            "Not enough patients remain to create train and validation sets."
        )

    second = GroupShuffleSplit(
        n_splits=1,
        test_size=relative_val_size,
        random_state=random_state,
    )
    train_idx, val_idx = next(
        second.split(train_val, groups=remaining_groups)
    )

    train = [train_val[i] for i in train_idx]
    validation = [train_val[i] for i in val_idx]

    if not train or not validation or not test:
        raise ValueError(
            "The selected split sizes produced an empty dataset split."
        )

    return train, validation, test


if __name__ == "__main__":
    # Synthetic records for software testing only.
    records = [
        {
            "patient_id": f"P{i}",
            "text": f"Synthetic note {i}",
            "codes": ["SYNTH_A" if i % 2 == 0 else "SYNTH_B"],
        }
        for i in range(1, 21)
    ]

    train, validation, test = split_records(records)

    for name, split in [
        ("Train", train),
        ("Validation", validation),
        ("Test", test),
    ]:
        print(f"{name}: {len(split)} records")

    train_ids = {r["patient_id"] for r in train}
    val_ids = {r["patient_id"] for r in validation}
    test_ids = {r["patient_id"] for r in test}

    assert train_ids.isdisjoint(val_ids)
    assert train_ids.isdisjoint(test_ids)
    assert val_ids.isdisjoint(test_ids)
    assert train and validation and test

    print("PASS: No patient appears in multiple splits.")
    print("PASS: All three splits are non-empty.")

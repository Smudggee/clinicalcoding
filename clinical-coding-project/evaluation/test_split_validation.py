
from evaluation.split_dataset import split_records


def check_rejected(name, records):
    try:
        split_records(records)
    except ValueError as exc:
        print(f"PASS: {name} rejected — {exc}")
    else:
        raise AssertionError(f"FAIL: {name} was not rejected")


def main():
    # Valid synthetic records: 10 distinct patients.
    valid_records = [
        {
            "patient_id": f"P{i}",
            "text": f"Synthetic clinical note {i}",
            "codes": ["SYNTH_A"],
        }
        for i in range(10)
    ]

    train, validation, test = split_records(valid_records)
    print("PASS: Valid records split successfully.")

    # Empty clinical note.
    bad = [dict(r) for r in valid_records]
    bad[0]["text"] = ""
    check_rejected("Empty note", bad)

    # Missing labels.
    bad = [dict(r) for r in valid_records]
    bad[0]["codes"] = []
    check_rejected("Empty codes", bad)

    # Duplicate record.
    bad = valid_records + [dict(valid_records[0])]
    check_rejected("Duplicate record", bad)

    # Missing patient identifier.
    bad = [dict(r) for r in valid_records]
    bad[0]["patient_id"] = ""
    check_rejected("Missing patient ID", bad)

    print("All validation tests passed.")


if __name__ == "__main__":
    main()

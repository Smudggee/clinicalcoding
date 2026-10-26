
import csv
import json
import sys
from pathlib import Path
from collections import Counter


def load_dataset(file_path):
    """Load a CSV or JSON dataset."""
    path = Path(file_path)

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return None

    try:
        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file, delimiter=",")
                print("DEBUG - Detected headers:", reader.fieldnames)
                return list(reader)

        elif path.suffix.lower() == ".json":
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                data = data.get("records", [data])

            if not isinstance(data, list):
                print("ERROR: JSON must contain a list of records.")
                return None

            return data

        else:
            print("ERROR: Please provide a .csv or .json file.")
            return None

    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error) as error:
        print(f"ERROR while reading dataset: {error}")
        return None


def inspect_dataset(file_path):
    """Inspect records for missing values, duplicates and labels."""
    records = load_dataset(file_path)

    if records is None:
        return

    print("\n========== DATASET INSPECTION ==========")
    print(f"File: {file_path}")
    print(f"Total records: {len(records)}")

    if not records:
        print("The dataset is empty.")
        return

    # Identify available columns.
    columns = sorted({
        column
        for record in records
        if isinstance(record, dict)
        for column in record
    })

    print("\nAvailable columns:")
    for column in columns:
        print(f"  - {column}")

    # Count missing values.
    print("\nMissing values by column:")
    for column in columns:
        missing = sum(
            1 for record in records
            if not isinstance(record, dict)
            or record.get(column) is None
            or str(record.get(column)).strip() == ""
        )
        print(f"  {column}: {missing}")

    # Count exact duplicate records.
    serialized = [
        json.dumps(record, sort_keys=True, ensure_ascii=False)
        for record in records
    ]
    duplicate_count = len(serialized) - len(set(serialized))
    print(f"\nDuplicate records: {duplicate_count}")

    # Detect a common patient ID column.
    patient_column = next(
        (
            name for name in (
                "patient_id", "subject_id", "patient", "subject"
            )
            if name in columns
        ),
        None
    )

    if patient_column:
        patient_ids = [
            str(record.get(patient_column)).strip()
            for record in records
            if isinstance(record, dict)
            and record.get(patient_column) is not None
            and str(record.get(patient_column)).strip() != ""
        ]

        print(f"Patient ID column: {patient_column}")
        print(f"Unique patients: {len(set(patient_ids))}")
    else:
        print("\nPatient ID column not detected.")
        print("Check the column names when the real dataset arrives.")

    # Detect a common ICD code or label column.
    label_column = next(
        (
            name for name in (
                "codes", "labels", "icd_codes", "icd_code", "code"
            )
            if name in columns
        ),
        None
    )

    if label_column:
        label_counts = Counter()

        for record in records:
            if not isinstance(record, dict):
                continue

            value = record.get(label_column)

            if value is None:
                continue

            # Support multiple codes separated by semicolons or pipes.
            for label in str(value).replace("|", ";").split(";"):
                label = label.strip()
                if label:
                    label_counts[label] += 1

        print(f"\nLabel/code frequency ({label_column}):")

        if label_counts:
            for label, count in label_counts.most_common(20):
                print(f"  {label}: {count}")
        else:
            print("No labels found.")
    else:
        print("\nNo common label/code column detected.")
        print("We can configure this after seeing the dataset schema.")

    print("\n========== INSPECTION COMPLETE ==========")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print(
            "  python evaluation/inspect_dataset.py "
            "<dataset.csv-or-json>"
        )
        sys.exit(1)

    inspect_dataset(sys.argv[1])

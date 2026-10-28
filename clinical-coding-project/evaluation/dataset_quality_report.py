
import csv
import json
import sys
from pathlib import Path
from collections import Counter


def generate_quality_report(file_path):
    path = Path(file_path)

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return

    if path.suffix.lower() != ".csv":
        print("ERROR: Please provide a CSV file.")
        return

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            records = list(reader)

    except (OSError, UnicodeError, csv.Error) as error:
        print(f"ERROR: Could not read dataset: {error}")
        return

    if not reader.fieldnames:
        print("ERROR: No column headers found.")
        return

    columns = reader.fieldnames

    if not records:
        print("ERROR: Dataset contains no records.")
        return

    missing_values = {
        column: sum(
            1 for record in records
            if record.get(column) is None
            or record.get(column).strip() == ""
        )
        for column in columns
    }

    duplicate_count = len(records) - len({
        json.dumps(record, sort_keys=True)
        for record in records
    })

    patient_column = next(
        (column for column in
         ["patient_id", "subject_id", "patient", "subject"]
         if column in columns),
        None
    )

    if patient_column:
        unique_patients = len({
            record[patient_column].strip()
            for record in records
            if record.get(patient_column)
            and record[patient_column].strip()
        })
    else:
        unique_patients = None

    label_column = next(
        (column for column in
         ["codes", "labels", "icd_codes", "icd_code", "code"]
         if column in columns),
        None
    )

    label_counts = Counter()

    if label_column:
        for record in records:
            value = record.get(label_column, "")
            if value:
                for label in value.replace("|", ";").split(";"):
                    label = label.strip()
                    if label:
                        label_counts[label] += 1

    report = {
        "dataset_file": path.name,
        "total_records": len(records),
        "columns": columns,
        "missing_values": missing_values,
        "duplicate_records": duplicate_count,
        "patient_id_column": patient_column,
        "unique_patients": unique_patients,
        "label_column": label_column,
        "label_frequency": dict(label_counts),
        "synthetic_data": True
    }

    print("\n========== DATASET QUALITY REPORT ==========")
    print(json.dumps(report, indent=4, ensure_ascii=False))
    print("\n========== REPORT COMPLETE ==========")

    output_path = path.parent / "dataset_quality_report.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python evaluation/dataset_quality_report.py "
            "<dataset.csv>"
        )
        sys.exit(1)

    generate_quality_report(sys.argv[1])

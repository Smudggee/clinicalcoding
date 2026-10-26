
import csv
import sys
from pathlib import Path


def check_patient_split(file_path):
    path = Path(file_path)

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        records = list(reader)

    required_columns = {"patient_id", "split"}

    if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
        print("ERROR: CSV must contain these columns:")
        print("patient_id,split")
        print("\nExample:")
        print("patient_id,split")
        print("P001,train")
        print("P002,validation")
        print("P003,test")
        return

    patient_splits = {}

    for record in records:
        patient_id = record["patient_id"].strip()
        split = record["split"].strip().lower()

        if not patient_id or not split:
            print("ERROR: Missing patient ID or split value.")
            return

        if split not in {"train", "validation", "test"}:
            print(f"ERROR: Invalid split '{split}' for patient {patient_id}.")
            return

        patient_splits.setdefault(patient_id, set()).add(split)

    leakage = {
        patient: splits
        for patient, splits in patient_splits.items()
        if len(splits) > 1
    }

    print("\n========== PATIENT SPLIT CHECK ==========")
    print(f"Total records: {len(records)}")
    print(f"Unique patients: {len(patient_splits)}")

    for split in ("train", "validation", "test"):
        patients = {
            patient
            for patient, splits in patient_splits.items()
            if split in splits
        }
        print(f"Patients in {split}: {len(patients)}")

    if leakage:
        print("\nFAILED: Patient leakage detected!")
        for patient, splits in sorted(leakage.items()):
            print(f"  {patient}: {', '.join(sorted(splits))}")
    else:
        print("\nPASSED: No patient appears in multiple splits.")

    print("=========================================")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python evaluation/check_patient_split.py "
            "<split_dataset.csv>"
        )
        sys.exit(1)

    check_patient_split(sys.argv[1])

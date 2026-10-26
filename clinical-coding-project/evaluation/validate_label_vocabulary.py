
import csv
import sys
from pathlib import Path


def validate_labels(dataset_path, vocabulary_path):
    dataset_file = Path(dataset_path)
    vocabulary_file = Path(vocabulary_path)

    if not dataset_file.exists():
        print(f"ERROR: Dataset not found: {dataset_file}")
        return

    if not vocabulary_file.exists():
        print(f"ERROR: Vocabulary file not found: {vocabulary_file}")
        return

    # Load allowed labels, one code per line.
    with vocabulary_file.open("r", encoding="utf-8-sig") as file:
        vocabulary = {
            line.strip()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        }

    # Load dataset.
    with dataset_file.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or "codes" not in reader.fieldnames:
            print("ERROR: Dataset must contain a 'codes' column.")
            return

        records = list(reader)

    found_labels = set()
    missing_labels = 0

    for record in records:
        value = (record.get("codes") or "").strip()

        if not value:
            missing_labels += 1
            continue

        # Support multiple codes separated by semicolons or pipes.
        for label in value.replace("|", ";").split(";"):
            label = label.strip()
            if label:
                found_labels.add(label)

    unknown_labels = sorted(found_labels - vocabulary)
    unused_labels = sorted(vocabulary - found_labels)

    print("\n========== LABEL VALIDATION ==========")
    print(f"Dataset records: {len(records)}")
    print(f"Vocabulary labels: {len(vocabulary)}")
    print(f"Labels found in dataset: {len(found_labels)}")
    print(f"Records with missing codes: {missing_labels}")

    if unknown_labels:
        print("\nUnknown labels:")
        for label in unknown_labels:
            print(f"  - {label}")
    else:
        print("\nAll dataset labels are in the vocabulary.")

    if unused_labels:
        print("\nVocabulary labels not used in this dataset:")
        for label in unused_labels:
            print(f"  - {label}")

    if unknown_labels:
        print("\nRESULT: FAILED — update or verify the vocabulary.")
    else:
        print("\nRESULT: PASSED — no unknown labels detected.")

    print("======================================")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python evaluation/validate_label_vocabulary.py "
            "<dataset.csv> <vocabulary.txt>"
        )
        sys.exit(1)

    validate_labels(sys.argv[1], sys.argv[2])

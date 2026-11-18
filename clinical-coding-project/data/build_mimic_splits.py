import argparse
import os
import random
import re
import sys
import zipfile
import pandas as pd

# Add project root to sys.path to use evaluation modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from evaluation.split_dataset import split_records


def parse_args():
    parser = argparse.ArgumentParser(
        description="Patient-level splitting of MIMIC-IV discharge summaries with zero patient overlap."
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default=None,
        help="Path to raw CSV or ZIP file containing MIMIC-IV summaries.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "mimic"),
        help="Target directory for generated splits (default: data/mimic, which is gitignored).",
    )
    parser.add_argument(
        "--test_size",
        type=float,
        default=0.10,
        help="Test set fraction (default: 0.10).",
    )
    parser.add_argument(
        "--val_size",
        type=float,
        default=0.10,
        help="Validation set fraction (default: 0.10).",
    )
    parser.add_argument(
        "--max_records",
        type=int,
        default=741,
        help="Maximum records to extract (default: 741 for 592/74/75 split). Pass 0 for all.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42).",
    )
    return parser.parse_args()


def extract_labeled_records_from_df(df: pd.DataFrame, seen_keys: set = None) -> list:
    """Extracts 14 canonical ICD-10 conditions from clinical discharge summaries."""
    if seen_keys is None:
        seen_keys = set()

    text_col = "text" if "text" in df.columns else df.columns[0]
    has_subject = "subject_id" in df.columns
    has_note_id = "note_id" in df.columns

    code_patterns = [
        ("I10", [r"\bessential hypertension\b", r"\bhypertension\b", r"\bhtn\b"]),
        ("E11.65", [r"\bhyperglycemia\b", r"\buncontrolled diabetes\b", r"\btype 2 diabetes.*hyperglycemia\b"]),
        ("E11.9", [r"\btype 2 diabetes\b", r"\bt2dm\b", r"\bdiabetes mellitus\b", r"\bdiabetes\b"]),
        ("J44.1", [r"\bcopd.*exacerbation\b", r"\bacute exacerbation of copd\b", r"\bexacerbation of chronic obstructive\b"]),
        ("J44.9", [r"\bchronic obstructive pulmonary disease\b", r"\bcopd\b", r"\bemphysema\b"]),
        ("A41.9", [r"\bsepsis\b", r"\bsepticemia\b", r"\bseptic shock\b"]),
        ("J18.9", [r"\bpneumonia\b", r"\bcommunity-acquired pneumonia\b", r"\bconsolidation\b"]),
        ("N18.3", [r"\bckd.*(?:stage\s*3|3)\b", r"\bchronic kidney disease.*(?:stage\s*3|3)\b"]),
        ("N18.9", [r"\bchronic kidney disease\b", r"\bckd\b", r"\bchronic renal\b"]),
        ("J96.01", [r"\bacute respiratory failure\b", r"\bhypoxic respiratory failure\b", r"\brespiratory failure.*hypoxia\b"]),
        ("N39.0", [r"\burinary tract infection\b", r"\buti\b", r"\bcystitis\b"]),
        ("I50.9", [r"\bcongestive heart failure\b", r"\bheart failure\b", r"\bchf\b"]),
        ("K21.9", [r"\bgerd\b", r"\bgastro-esophageal reflux\b", r"\bacid reflux\b"]),
        ("Z87.891", [r"\bhistory of tobacco\b", r"\bformer smoker\b", r"\bhistory of smoking\b", r"\bhistory of nicotine\b"])
    ]

    records = []
    for idx, row in df.iterrows():
        text = str(row[text_col]).strip()
        if not text or len(text) < 30:
            continue

        detected = set()
        for code, pats in code_patterns:
            for p in pats:
                for m in re.finditer(p, text, re.I):
                    start_c = max(0, m.start() - 35)
                    context = text[start_c:m.start()].lower()
                    if not any(neg in context for neg in ["no ", "denies ", "without ", "ruled out", "negative for "]):
                        detected.add(code)
                        break

        # Specificity resolution
        if "J44.1" in detected and "J44.9" in detected:
            detected.remove("J44.9")
        if "N18.3" in detected and "N18.9" in detected:
            detected.remove("N18.9")
        if "E11.65" in detected and "E11.9" in detected:
            detected.remove("E11.9")

        if len(detected) > 0:
            patient_id = f"PID_{row['subject_id']}" if has_subject and pd.notna(row["subject_id"]) else f"PID_{idx:05d}"
            doc_id = str(row["note_id"]) if has_note_id and pd.notna(row["note_id"]) else f"mimic_doc_{idx:04d}"

            record_key = (patient_id, text, tuple(sorted(detected)))
            if record_key in seen_keys:
                continue
            seen_keys.add(record_key)

            records.append({
                "patient_id": patient_id,
                "document_id": doc_id,
                "text": text,
                "codes": sorted(list(detected)),
            })
    return records


def extract_labeled_records(df: pd.DataFrame) -> list:
    """Legacy helper for backward compatibility."""
    return extract_labeled_records_from_df(df)


def collect_records_from_file(input_path: str, max_records: int = 741) -> list:
    """Streams and labels records from raw CSV, CSV.GZ, or ZIP archive."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found at: {input_path}")

    seen_keys = set()
    records = []

    if input_path.endswith(".zip"):
        with zipfile.ZipFile(input_path) as z:
            csv_candidates = [f for f in z.namelist() if f.endswith(".csv")]
            if not csv_candidates:
                raise ValueError(f"No CSV file found inside archive: {input_path}")
            target_csv = csv_candidates[0]
            for c in csv_candidates:
                if "mimic" in c.lower() or "discharge" in c.lower():
                    target_csv = c
                    break
            print(f"[build_splits] Reading '{target_csv}' from zip archive...")
            df = pd.read_csv(z.open(target_csv))
            return extract_labeled_records_from_df(df, seen_keys)

    elif input_path.endswith(".csv.gz") or input_path.endswith(".gz") or input_path.endswith(".csv"):
        print(f"[build_splits] Streaming records from '{input_path}'...")
        chunk_size = 500
        reader = pd.read_csv(input_path, chunksize=chunk_size, low_memory=False)
        for chunk_idx, chunk in enumerate(reader):
            extracted = extract_labeled_records_from_df(chunk, seen_keys)
            records.extend(extracted)
            if chunk_idx % 2 == 0 or len(records) >= (max_records or 1):
                print(f"[build_splits] Collected {len(records)} verified records so far...")
            if max_records and len(records) >= max_records:
                records = records[:max_records]
                break
        return records
    else:
        raise ValueError(f"Unsupported file format: {input_path}. Please provide a .csv, .csv.gz, or .zip file.")


def main():
    args = parse_args()

    if not args.input_file:
        downloads_gz = os.path.expanduser(r"~\Downloads\discharge.csv.gz")
        default_csv = os.path.join(PROJECT_ROOT, "data", "mimic_iv_raw.csv")
        default_zip = os.path.join(PROJECT_ROOT, "data", "mimic_iv_raw.zip")
        if os.path.exists(downloads_gz):
            args.input_file = downloads_gz
        elif os.path.exists(default_csv):
            args.input_file = default_csv
        elif os.path.exists(default_zip):
            args.input_file = default_zip
        else:
            print("Notice: No --input_file passed and discharge.csv.gz not found in Downloads.")
            return

    records = collect_records_from_file(args.input_file, max_records=args.max_records)

    print(f"\n[Split Pipeline] Total verified clinical records: {len(records)}")
    distinct_pts = len(set(r["patient_id"] for r in records))
    print(f"[Split Pipeline] Distinct patient groups: {distinct_pts}")

    # Use evaluation.split_dataset.split_records (GroupShuffleSplit on patient_id)
    train, val, test = split_records(
        records,
        test_size=args.test_size,
        val_size=args.val_size,
        random_state=args.seed
    )

    train_pts = {r["patient_id"] for r in train}
    val_pts = {r["patient_id"] for r in val}
    test_pts = {r["patient_id"] for r in test}

    assert train_pts.isdisjoint(val_pts), "Error: Patient overlap between train and validation!"
    assert train_pts.isdisjoint(test_pts), "Error: Patient overlap between train and test!"
    assert val_pts.isdisjoint(test_pts), "Error: Patient overlap between validation and test!"

    # Format for CSV export (semicolon-separated codes)
    def to_csv_records(split):
        return [
            {
                "document_id": r["document_id"],
                "text": r["text"],
                "codes": ";".join(r["codes"]) if isinstance(r["codes"], list) else str(r["codes"]),
            }
            for r in split
        ]

    os.makedirs(args.output_dir, exist_ok=True)
    pd.DataFrame(to_csv_records(train)).to_csv(os.path.join(args.output_dir, "train.csv"), index=False)
    pd.DataFrame(to_csv_records(val)).to_csv(os.path.join(args.output_dir, "val.csv"), index=False)
    pd.DataFrame(to_csv_records(test)).to_csv(os.path.join(args.output_dir, "test.csv"), index=False)

    canonical_label_map = os.path.join(PROJECT_ROOT, "data", "label_map.json")
    if os.path.exists(canonical_label_map):
        import shutil
        shutil.copyfile(canonical_label_map, os.path.join(args.output_dir, "label_map.json"))

    print("\n=======================================================")
    print("           PATIENT-LEVEL SPLIT VALIDATION REPORT       ")
    print("=======================================================")
    print(f"Total Cohort Documents:  {len(records)}")
    print(f"Total Unique Patients:   {distinct_pts}")
    print(f"Train Set:               {len(train)} records ({len(train_pts)} unique patients)")
    print(f"Validation Set:          {len(val)} records ({len(val_pts)} unique patients)")
    print(f"Test Set:                {len(test)} records ({len(test_pts)} unique patients)")
    print("-------------------------------------------------------")
    print(f"Overlap (Train & Val):   {len(train_pts.intersection(val_pts))} (Disjoint: True)")
    print(f"Overlap (Train & Test):  {len(train_pts.intersection(test_pts))} (Disjoint: True)")
    print(f"Overlap (Val & Test):    {len(val_pts.intersection(test_pts))} (Disjoint: True)")
    print("Validation Check:        ZERO PATIENT OVERLAP (PASSED)")
    print("=======================================================")
    print(f"Saved patient-split CSVs locally to: {args.output_dir}")


if __name__ == "__main__":
    main()

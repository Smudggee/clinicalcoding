import argparse
import os
import random
import re
import zipfile
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract 14 canonical ICD-10 diagnosis codes from MIMIC-IV discharge summaries and create train/val/test splits."
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default=None,
        help="Path to raw CSV or ZIP file containing MIMIC-IV discharge summaries (e.g., mimic_iv_raw.csv or dataset.zip).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.path.abspath(os.path.join(os.path.dirname(__file__))),
        help="Directory to save train.csv, val.csv, and test.csv (default: same folder as this script).",
    )
    parser.add_argument(
        "--train_ratio",
        type=float,
        default=0.80,
        help="Proportion of data allocated to train set (default: 0.80).",
    )
    parser.add_argument(
        "--val_ratio",
        type=float,
        default=0.10,
        help="Proportion of data allocated to validation set (default: 0.10).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    return parser.parse_args()


def load_raw_dataframe(input_path: str) -> pd.DataFrame:
    """Loads dataframe from either a raw CSV file or a ZIP archive containing a CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found at: {input_path}")

    if input_path.endswith(".zip"):
        with zipfile.ZipFile(input_path) as z:
            csv_candidates = [f for f in z.namelist() if f.endswith(".csv")]
            if not csv_candidates:
                raise ValueError(f"No CSV file found inside archive: {input_path}")
            # Prefer summarization or discharge CSV
            target_csv = csv_candidates[0]
            for c in csv_candidates:
                if "mimic" in c.lower() or "discharge" in c.lower():
                    target_csv = c
                    break
            print(f"[build_splits] Reading '{target_csv}' from zip archive...")
            return pd.read_csv(z.open(target_csv))
    elif input_path.endswith(".csv"):
        print(f"[build_splits] Reading CSV from '{input_path}'...")
        return pd.read_csv(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path}. Please provide a .csv or .zip file.")


def main():
    args = parse_args()
    random.seed(args.seed)

    if not args.input_file:
        # Check standard local fallbacks
        default_csv = os.path.join(args.output_dir, "mimic_iv_raw.csv")
        default_zip = os.path.join(args.output_dir, "mimic_iv_raw.zip")
        if os.path.exists(default_csv):
            args.input_file = default_csv
        elif os.path.exists(default_zip):
            args.input_file = default_zip
        else:
            raise ValueError(
                "Please provide --input_file pointing to the MIMIC-IV CSV or ZIP archive. "
                f"Example: python build_mimic_splits.py --input_file path/to/dataset.csv --output_dir data"
            )

    df = load_raw_dataframe(args.input_file)
    text_col = "text" if "text" in df.columns else df.columns[0]

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
        detected = set()
        for code, pats in code_patterns:
            for p in pats:
                for m in re.finditer(p, text, re.I):
                    start_c = max(0, m.start() - 35)
                    context = text[start_c:m.start()].lower()
                    if not any(neg in context for neg in ["no ", "denies ", "without ", "ruled out", "negative for "]):
                        detected.add(code)
                        break
        if "J44.1" in detected and "J44.9" in detected:
            detected.remove("J44.9")
        if "N18.3" in detected and "N18.9" in detected:
            detected.remove("N18.9")
        if "E11.65" in detected and "E11.9" in detected:
            detected.remove("E11.9")

        if len(detected) > 0:
            doc_id = str(row.get("document_id", f"mimic_doc_{idx:04d}"))
            records.append({
                "document_id": doc_id,
                "text": text,
                "codes": ";".join(sorted(detected))
            })

    random.shuffle(records)
    n_total = len(records)
    n_train = int(n_total * args.train_ratio)
    n_val = int(n_total * args.val_ratio)

    train_recs = records[:n_train]
    val_recs = records[n_train:n_train + n_val]
    test_recs = records[n_train + n_val:]

    os.makedirs(args.output_dir, exist_ok=True)
    train_path = os.path.join(args.output_dir, "train.csv")
    val_path = os.path.join(args.output_dir, "val.csv")
    test_path = os.path.join(args.output_dir, "test.csv")

    pd.DataFrame(train_recs).to_csv(train_path, index=False)
    pd.DataFrame(val_recs).to_csv(val_path, index=False)
    pd.DataFrame(test_recs).to_csv(test_path, index=False)

    print("Successfully built authentic MIMIC-IV dataset splits!")
    print(f"Total notes processed: {n_total}")
    print(f"Train split: {len(train_recs)} notes -> {train_path}")
    print(f"Val split:   {len(val_recs)} notes -> {val_path}")
    print(f"Test split:  {len(test_recs)} notes -> {test_path}")


if __name__ == "__main__":
    main()

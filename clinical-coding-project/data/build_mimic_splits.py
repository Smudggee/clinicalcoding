import zipfile
import pandas as pd
import re
import random
import os

def main():
    random.seed(42)
    zip_path = r"C:\Users\keert\.gemini\antigravity\brain\49fb3322-62d5-40a5-ac09-a18ad3e30ecb\.user_uploaded\media_1793110172970_c497f3f6.zip"
    z = zipfile.ZipFile(zip_path)
    df = pd.read_csv(z.open("mimic_iv_summarization_test_dataset_shortened.csv"))

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
        text = str(row["text"]).strip()
        detected = set()
        for code, pats in code_patterns:
            for p in pats:
                for m in re.finditer(p, text, re.I):
                    start_c = max(0, m.start() - 35)
                    context = text[start_c:m.start()].lower()
                    if not any(neg in context for neg in ["no ", "denies ", "without ", "ruled out", "negative for "]):
                        detected.add(code)
                        break
        if "J44.1" in detected and "J44.9" in detected: detected.remove("J44.9")
        if "N18.3" in detected and "N18.9" in detected: detected.remove("N18.9")
        if "E11.65" in detected and "E11.9" in detected: detected.remove("E11.9")

        if len(detected) > 0:
            records.append({
                "document_id": f"mimic_doc_{idx:04d}",
                "text": text,
                "codes": ";".join(sorted(detected))
            })

    random.shuffle(records)
    n_total = len(records)
    n_train = int(n_total * 0.80)
    n_val = int(n_total * 0.10)

    train_recs = records[:n_train]
    val_recs = records[n_train:n_train + n_val]
    test_recs = records[n_train + n_val:]

    data_dir = r"C:\Users\keert\OneDrive\Desktop\cc\clinicalcoding\clinical-coding-project\data"
    pd.DataFrame(train_recs).to_csv(os.path.join(data_dir, "train.csv"), index=False)
    pd.DataFrame(val_recs).to_csv(os.path.join(data_dir, "val.csv"), index=False)
    pd.DataFrame(test_recs).to_csv(os.path.join(data_dir, "test.csv"), index=False)

    print("Successfully built authentic MIMIC-IV dataset splits!")
    print(f"Total notes processed: {n_total}")
    print(f"Train split: {len(train_recs)} notes -> {os.path.join(data_dir, 'train.csv')}")
    print(f"Val split:   {len(val_recs)} notes -> {os.path.join(data_dir, 'val.csv')}")
    print(f"Test split:  {len(test_recs)} notes -> {os.path.join(data_dir, 'test.csv')}")

if __name__ == "__main__":
    main()

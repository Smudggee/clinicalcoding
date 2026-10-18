
import json
from pathlib import Path

output_dir = Path(__file__).parent / "prepared_test_output"

with open(output_dir / "train.json", encoding="utf-8") as f:
    train = json.load(f)

with open(output_dir / "label_map.json", encoding="utf-8") as f:
    label_map = json.load(f)

training_codes = {
    code
    for record in train
    for code in record["codes"]
}

missing_codes = training_codes - set(label_map)

assert not missing_codes, f"Missing codes in label map: {missing_codes}"

print(f"Training records checked: {len(train)}")
print(f"Training codes found: {len(training_codes)}")
print("PASS: Every training code exists in the label map.")

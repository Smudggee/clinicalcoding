"""
Clinical Speech Transcription Error Analysis.
Evaluates Whisper transcription on pure Malayalam and Malayalam-English code-mixed clinical speech.
Documents common errors: phonetic transliteration drift, English loanword inflection,
abbreviation corruption, numerical/dosage boundaries, and negation capture.
"""
import csv
from pathlib import Path
import sys

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT / "evaluation" / "transcription_error_analysis.csv"

SAMPLES = [
    # --- Category A: Pure Malayalam Clinical Speech ---
    {
        "sample": "sample_01",
        "category": "Malayalam",
        "reference": "രോഗിക്ക് മൂന്ന് ദിവസമായി പനിയും ചുമയും ഉണ്ട്.",
        "prediction": "രോഗിക്ക് മൂണ്ണ് ദിവസംമായി പനയും ചുമയും ഉണ്ട്.",
        "error_type": "Phonetic / Vowel distortion",
        "observation": "Spelling differences in duration ('മൂണ്ണ്' vs 'മൂന്ന്') and symptom words.",
        "clinical_impact": "Low: root symptom 'ചുമ' (cough) preserved.",
        "priority": "Review",
    },
    {
        "sample": "sample_02",
        "category": "Malayalam",
        "reference": "എനിക്ക് ഇന്നലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്.",
        "prediction": "എനിക്ക് ഇന്നിലെ രാത്രി മുതൽ ശക്തമായ തലവേദനയുണ്ട്.",
        "error_type": "Vowel shift",
        "observation": "Spelling difference in temporal anchor ('ഇന്നലെ' -> 'ഇന്നിലെ').",
        "clinical_impact": "Low: symptom 'തലവേദന' (headache) recognized.",
        "priority": "Low",
    },
    {
        "sample": "sample_03",
        "category": "Malayalam",
        "reference": "ഇന്ന് രാവിലെ ഞാൻ ആശുപത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു.",
        "prediction": "ഇന്ന് രാവിലെ ഞാൻ ആശുവത്രിയിൽ എത്തി ഡോക്ടറെ കണ്ടു.",
        "error_type": "Consonant cluster substitution",
        "observation": "Spelling difference in facility term ('ആശുപത്രി' -> 'ആശുവത്രി').",
        "clinical_impact": "Low: non-diagnostic context word.",
        "priority": "Review",
    },
    {
        "sample": "sample_04",
        "category": "Malayalam",
        "reference": "ഡോക്ടർ എന്റെ രക്തസമ്മർദ്ദം പരിശോധിച്ച് മരുന്ന് നിർദ്ദേശിച്ചു.",
        "prediction": "ഡോക്ടർ എണ്ടെ രക്ത സമ്മർതം പരിഷോധിച്ച് മരിന്ന് നിർദ്ദേശിച്ചു.",
        "error_type": "Dental/retroflex confusion & word splitting",
        "observation": "Splitting of compound 'രക്തസമ്മർദ്ദം' into 'രക്ത സമ്മർതം'; retroflex shift in 'പരിഷോധിച്ച്'.",
        "clinical_impact": "Medium: vital sign 'blood pressure' segmented across word boundary.",
        "priority": "High",
    },
    {
        "sample": "sample_05",
        "category": "Malayalam",
        "reference": "എനിക്ക് ഒ.പി.യിൽ രജിസ്റ്റർ ചെയ്യണം, ഡോക്ടറെ കാണാൻ ടോക്കൺ വേണം.",
        "prediction": "എനിക്ക് ഓപ്പിയിൽ റെജിസ്റ്റർ ചെയ്യണം. ഡോക്ടറെ കാണാൻ ടോക്കൻ വേണം.",
        "error_type": "Abbreviation transliteration",
        "observation": "Format alteration: clinical abbreviation 'ഒ.പി.' transliterated phonetically as 'ഓപ്പി'.",
        "clinical_impact": "Medium: clinical encounters department formatted phonetically.",
        "priority": "Review",
    },

    # --- Category B: Malayalam-English Code-Mixed Clinical Speech ---
    {
        "sample": "sample_06",
        "category": "Malayalam-English",
        "reference": "രോഗിക്ക് 3 days ആയി fever ഉം productive cough ഉം ഉണ്ട്.",
        "prediction": "രോഗിക്ക് 3 ഡേയ്സ് ആയി ഫീവറും പ്രൊഡക്റ്റീവ് കോഫും ഉണ്ട്.",
        "error_type": "Phonetic transliteration of English medical loanwords",
        "observation": "English terms ('days', 'fever', 'productive cough') written in Malayalam script with agglutinative suffix '-ഉം'.",
        "clinical_impact": "High: Requires normalization mapping 'ഫീവർ' -> 'fever' and 'കോഫ്' -> 'cough' for ICD text matching.",
        "priority": "High",
    },
    {
        "sample": "sample_07",
        "category": "Malayalam-English",
        "reference": "Chest X-ray ൽ right lower lobe consolidation കണ്ടു.",
        "prediction": "ചെസ്റ്റ് എക്സ്റേയിൽ റൈറ്റ് ലോവർ ലോബ് കൺസോളിഡേഷൻ കണ്ടു.",
        "error_type": "Radiology jargon transliteration drift",
        "observation": "Diagnostic phrase 'right lower lobe consolidation' transliterated into phonetic Malayalam script.",
        "clinical_impact": "Critical: Direct evidence for ICD J18.9 (Pneumonia); downstream ICD matcher needs bilingual mapping.",
        "priority": "High",
    },
    {
        "sample": "sample_08",
        "category": "Malayalam-English",
        "reference": "Patient ന് Type 2 diabetes ഉം hypertension ഉം ഉണ്ട്, metformin 500mg daily നൽകി.",
        "prediction": "പേഷ്യന്റിന് ടൈപ്പ് 2 ഡയബറ്റിസും ഹൈപ്പർടെൻഷനും ഉണ്ട് മെറ്റ്ഫോർമിൻ 500 mg ഡെയ്ലി നൽകി.",
        "error_type": "Diagnosis transliteration & dosage unit separation",
        "observation": "Condition names transliterated into Malayalam; dosage unit separated from value ('500 mg').",
        "clinical_impact": "Medium: Numerical dosage preserved; diagnoses require English normalization for E11.9 and I10.",
        "priority": "High",
    },
    {
        "sample": "sample_09",
        "category": "Malayalam-English",
        "reference": "Blood culture എടുത്തു, sepsis സംശയിക്കുന്നതിനാൽ IV broad-spectrum antibiotics നൽകി.",
        "prediction": "ബ്ലഡ് കൾച്ചർ എടുത്തു സെപ്സിസ് സംശയിക്കുന്നതിനാൽ ഐവി ബ്രോഡ് സ്പെക്ട്രം ആന്റിബയോട്ടിക്സ് നൽകി.",
        "error_type": "Route abbreviation transliteration ('IV' -> 'ഐവി')",
        "observation": "Acronym 'IV' rendered phonetically; clinical concept 'sepsis' transcribed phonetically as 'സെപ്സിസ്'.",
        "clinical_impact": "High: Critical inpatient diagnosis (A41.9). Transliterated term matches concept lexicons.",
        "priority": "Review",
    },
    {
        "sample": "sample_10",
        "category": "Malayalam-English",
        "reference": "Pneumonia യുടെ evidence ഒന്നും chest imaging ൽ ഇല്ല.",
        "prediction": "ന്യുമോണിയയുടെ എവിഡൻസ് ഒന്നും ചെസ്റ്റ് ഇമേജിംഗിൽ ഇല്ല.",
        "error_type": "Negation phrase preservation in code-switched context",
        "observation": "Negated predicate ('ഒന്നും... ഇല്ല') correctly captured alongside transliterated term 'ന്യുമോണിയ' (pneumonia).",
        "clinical_impact": "Critical: Crucial for Module 3 Neuro-Symbolic verifier to prevent false positive ICD assignment.",
        "priority": "High",
    },
]


def main():
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "sample",
                "category",
                "reference",
                "prediction",
                "error_type",
                "observation",
                "clinical_impact",
                "priority",
            ],
        )
        writer.writeheader()
        writer.writerows(SAMPLES)

    print("=" * 65)
    print("Clinical Speech Transcription Error Analysis (Malayalam + Malayalam-English)")
    print("=" * 65)

    categories = set(s["category"] for s in SAMPLES)
    for cat in sorted(categories):
        cat_samples = [s for s in SAMPLES if s["category"] == cat]
        print(f"\n--- {cat} Samples ({len(cat_samples)}) ---")
        for item in cat_samples:
            print(f"\n[{item['sample']}] Error: {item['error_type']} | Impact: {item['clinical_impact']}")
            print(f"  Reference : {item['reference']}")
            print(f"  Predicted : {item['prediction']}")
            print(f"  Notes     : {item['observation']}")

    print(f"\n[OK] Error analysis saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

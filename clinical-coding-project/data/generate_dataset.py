"""
Script to generate synthetic clinical dataset (train, val, test) and label_map.json.
Provides realistic clinical discharge notes with ICD-10-CM codes for testing
and training the classifier pipeline immediately.
"""
import os
import json
import pandas as pd

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# 14 standard ICD-10-CM codes representing acute and chronic conditions
LABEL_MAP = {
    "A41.9": 0,    # Sepsis, unspecified organism
    "J18.9": 1,    # Pneumonia, unspecified organism
    "E11.9": 2,    # Type 2 diabetes mellitus without complications
    "E11.65": 3,   # Type 2 diabetes mellitus with hyperglycemia
    "I10": 4,      # Essential (primary) hypertension
    "J44.1": 5,    # Chronic obstructive pulmonary disease with (acute) exacerbation
    "J44.9": 6,    # Chronic obstructive pulmonary disease, unspecified
    "N18.3": 7,    # Chronic kidney disease, stage 3 (moderate)
    "N18.9": 8,    # Chronic kidney disease, unspecified
    "J96.01": 9,   # Acute respiratory failure with hypoxia
    "N39.0": 10,   # Urinary tract infection, site not specified
    "I50.9": 11,   # Heart failure, unspecified
    "K21.9": 12,   # Gastro-esophageal reflux disease without esophagitis
    "Z87.891": 13  # Personal history of other specified conditions
}

SAMPLE_RECORDS = [
    {
        "document_id": "doc_001",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Shortness of breath, high fever, and productive cough.
HISTORY OF PRESENT ILLNESS: A 72-year-old male with a history of essential hypertension and chronic obstructive pulmonary disease presents with acute worsening of dyspnea and yellowish sputum for 4 days.
PHYSICAL EXAMINATION: Temperature 39.1C, blood pressure 145/88 mmHg, pulse 102 bpm, respiratory rate 26 bpm, oxygen saturation 88% on room air. Diffuse wheezing and coarse bibasilar crackles noted on lung auscultation.
DIAGNOSTIC STUDIES: Chest X-ray reveals right lower lobe consolidation consistent with community-acquired pneumonia. Arterial blood gas indicates acute respiratory failure with hypoxia.
HOSPITAL COURSE: Patient received intravenous ceftriaxone and azithromycin along with supplemental oxygen via nasal cannula and nebulized bronchodilators for COPD with acute exacerbation. He showed significant clinical improvement over 5 days.
DISCHARGE DIAGNOSES:
1. Community-acquired pneumonia (unspecified organism).
2. Chronic obstructive pulmonary disease with acute exacerbation.
3. Acute respiratory failure with hypoxia.
4. Essential (primary) hypertension.""",
        "codes": ["J18.9", "J44.1", "J96.01", "I10"]
    },
    {
        "document_id": "doc_002",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Lethargy, confusion, and burning during urination.
HISTORY OF PRESENT ILLNESS: An 81-year-old female with long-standing type 2 diabetes mellitus and chronic kidney disease stage 3 was brought to the emergency department due to altered mental status and dysuria.
PHYSICAL EXAMINATION: Blood pressure 85/50 mmHg, heart rate 118 bpm, temperature 38.8C. Dry oral mucosa, suprapubic tenderness noted.
LABORATORY DATA: Urinalysis positive for pyuria, leukocyte esterase, and nitrites. Serum lactate 3.8 mmol/L, serum creatinine elevated at 2.4 mg/dL from baseline 1.6 mg/dL. Blood cultures grew Gram-negative bacilli, establishing severe sepsis secondary to urinary tract infection. Blood glucose was 340 mg/dL upon admission.
HOSPITAL COURSE: Aggressive fluid resuscitation with normal saline was initiated alongside IV meropenem. An insulin infusion protocol was administered for type 2 diabetes with hyperglycemia. The patient stabilized and lactate normalized within 48 hours.
DISCHARGE DIAGNOSES:
1. Sepsis, unspecified organism.
2. Urinary tract infection, site not specified.
3. Type 2 diabetes mellitus with hyperglycemia.
4. Chronic kidney disease, stage 3.""",
        "codes": ["A41.9", "N39.0", "E11.65", "N18.3"]
    },
    {
        "document_id": "doc_003",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Bilateral lower extremity edema and progressive orthopnea.
HISTORY OF PRESENT ILLNESS: A 65-year-old male with established essential hypertension, gastro-esophageal reflux disease, and well-controlled type 2 diabetes mellitus presents with progressive fluid overload and paroxysmal nocturnal dyspnea.
PHYSICAL EXAMINATION: Blood pressure 162/95 mmHg, heart rate 88 bpm. Elevated jugular venous distension and 3+ pitting edema to mid-calves. Lung fields show bilateral lower lobe crackles.
DIAGNOSTIC STUDIES: BNP elevated at 1,450 pg/mL. Transthoracic echocardiogram reveals left ventricular ejection fraction of 35% consistent with acute decompensated heart failure.
HOSPITAL COURSE: The patient was treated with intravenous furosemide with brisk diuresis and rapid symptomatic relief. Daily oral lisinopril for hypertension and omeprazole for GERD were continued. Metformin maintained adequate glycemic control.
DISCHARGE DIAGNOSES:
1. Decompensated congestive heart failure, unspecified.
2. Essential (primary) hypertension.
3. Type 2 diabetes mellitus without complications.
4. Gastro-esophageal reflux disease without esophagitis.""",
        "codes": ["I50.9", "I10", "E11.9", "K21.9"]
    },
    {
        "document_id": "doc_004",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Fever, severe chills, and hypotension.
HISTORY OF PRESENT ILLNESS: A 58-year-old female with essential hypertension was admitted with acute onset of rigors, diaphoresis, and profound weakness.
VITAL SIGNS: BP 82/46 mmHg, HR 122 bpm, Temp 39.4C, SpO2 95% on room air.
LABS & IMAGING: White blood cell count 19.8 k/uL, serum lactate 4.1 mmol/L. Blood cultures positive for bacteremia. Sepsis, unspecified organism, was treated urgently in the intensive care unit with fluid resuscitation and broad-spectrum IV piperacillin-tazobactam.
HOSPITAL COURSE: Patient gradually stabilized, blood pressures normalized without vasopressors, and she was transitioned to oral antibiotics prior to discharge.
DISCHARGE DIAGNOSES:
1. Sepsis, unspecified organism.
2. Essential (primary) hypertension.""",
        "codes": ["A41.9", "I10"]
    },
    {
        "document_id": "doc_005",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Chronic cough and progressive dyspnea on exertion.
HISTORY OF PRESENT ILLNESS: A 69-year-old male former smoker with chronic obstructive pulmonary disease and personal history of nicotine dependence reports worsening functional tolerance over the past 3 weeks without acute infection.
PHYSICAL EXAMINATION: Blood pressure 130/80 mmHg, pulse 78 bpm, SpO2 92% on room air. Breath sounds are decreased bilaterally with prolonged expiratory phase.
MANAGEMENT: Outpatient inhaler regimen optimized with tiotropium and fluticasone/salmeterol. Pulmonary rehabilitation referral provided.
DISCHARGE DIAGNOSES:
1. Chronic obstructive pulmonary disease, unspecified.
2. Personal history of other specified conditions.""",
        "codes": ["J44.9", "Z87.891"]
    },
    {
        "document_id": "doc_006",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: High blood sugars, polyuria, and polydipsia.
HISTORY OF PRESENT ILLNESS: A 54-year-old female with known type 2 diabetes mellitus presented with fasting blood sugars exceeding 380 mg/dL for several days following an upper respiratory infection.
LABS: Serum glucose 412 mg/dL, HbA1c 11.2%, urine negative for ketones. Basic metabolic panel shows stable creatinine of 1.1 mg/dL.
COURSE: Patient was treated with subcutaneous basal-bolus insulin glargine and lispro. Diabetes education provided with dietary counseling. Blood glucose stabilized in the 130-160 range.
DISCHARGE DIAGNOSES:
1. Type 2 diabetes mellitus with hyperglycemia.
2. Essential hypertension.""",
        "codes": ["E11.65", "I10"]
    },
    {
        "document_id": "doc_007",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Routine staging and follow-up of chronic kidney disease.
HISTORY OF PRESENT ILLNESS: A 76-year-old male with long-standing essential hypertension and stage 3 chronic kidney disease admitted for elective medication adjustment and fluid management.
LABS: Baseline creatinine 1.8 mg/dL with eGFR 42 mL/min/1.73m2, confirming moderate chronic kidney disease, stage 3. Serum potassium 4.6 mEq/L.
HOSPITAL COURSE: Antihypertensive therapy was optimized with amlodipine. Patient remained asymptomatic, euvolemic, and was discharged with nephrology follow-up.
DISCHARGE DIAGNOSES:
1. Chronic kidney disease, stage 3 (moderate).
2. Essential (primary) hypertension.""",
        "codes": ["N18.3", "I10"]
    },
    {
        "document_id": "doc_008",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Severe retrosternal burning and nocturnal regurgitation.
HISTORY OF PRESENT ILLNESS: A 51-year-old female with essential hypertension presents with intractable heartburn and regurgitation exacerbated by lying flat.
DIAGNOSTICS: Upper endoscopy showed non-erosive gastro-esophageal reflux disease without esophagitis.
HOSPITAL COURSE: Patient responded promptly to high-dose proton pump inhibitor therapy (pantoprazole 40 mg twice daily). Lifestyle modifications and dietary advice reviewed.
DISCHARGE DIAGNOSES:
1. Gastro-esophageal reflux disease without esophagitis.
2. Essential (primary) hypertension.""",
        "codes": ["K21.9", "I10"]
    },
    {
        "document_id": "doc_009",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Dyspnea, purulent sputum, and pleuritic chest pain.
HISTORY OF PRESENT ILLNESS: A 62-year-old male with chronic obstructive pulmonary disease and type 2 diabetes presents with acute fever, chills, and dense left lower lobe infiltrate on chest radiograph.
PHYSICAL EXAM: Temperature 38.9C, SpO2 89% requiring 3L nasal cannula. Bronchial breath sounds and inspiratory crackles over left base.
COURSE: Treated with IV levofloxacin for community-acquired bacterial pneumonia and systemic steroids for acute COPD flare. Discharged in stable condition.
DISCHARGE DIAGNOSES:
1. Pneumonia, unspecified organism.
2. Chronic obstructive pulmonary disease with acute exacerbation.
3. Type 2 diabetes mellitus without complications.""",
        "codes": ["J18.9", "J44.1", "E11.9"]
    },
    {
        "document_id": "doc_010",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Dysuria, flank pain, and low-grade fever.
HISTORY OF PRESENT ILLNESS: A 64-year-old female with a history of type 2 diabetes and chronic kidney disease presents with acute urinary tract infection symptoms.
LABS: Urinalysis shows 50-100 WBCs/hpf, moderate bacteria. Urine culture grew E. coli sensitive to nitrofurantoin. Serum creatinine stable at 1.4 mg/dL.
COURSE: Completed 3-day course of intravenous ceftriaxone, transitioned to oral cefdinir with complete resolution of dysuria and fever.
DISCHARGE DIAGNOSES:
1. Urinary tract infection, site not specified.
2. Type 2 diabetes mellitus without complications.
3. Chronic kidney disease, unspecified.""",
        "codes": ["N39.0", "E11.9", "N18.9"]
    },
    {
        "document_id": "doc_011",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Progressive breathlessness and leg swelling.
HISTORY OF PRESENT ILLNESS: An 80-year-old male with chronic kidney disease, stage 3 and hypertension presents with congestive heart failure exacerbation.
EXAM & LABS: Elevated JVP, bibasilar rales, BNP 1,890 pg/mL. Creatinine 2.1 mg/dL.
COURSE: Intravenous loop diuretics administered with 4 kg negative fluid balance over 4 days. Orthopnea resolved.
DISCHARGE DIAGNOSES:
1. Heart failure, unspecified.
2. Chronic kidney disease, stage 3 (moderate).
3. Essential (primary) hypertension.""",
        "codes": ["I50.9", "N18.3", "I10"]
    },
    {
        "document_id": "doc_012",
        "text": """DISCHARGE SUMMARY
CHIEF COMPLAINT: Severe shortness of breath and blue lips.
HISTORY OF PRESENT ILLNESS: A 70-year-old female with severe COPD admitted with acute hypoxemic respiratory failure following a viral respiratory illness.
VITAL SIGNS: SpO2 84% on room air, RR 32 bpm. Arterial blood gas confirmed severe hypoxia with PaO2 52 mmHg.
COURSE: Required non-invasive positive pressure ventilation (BiPAP), systemic corticosteroids, and nebulized ipratropium/albuterol. Weaned to 2L cannula prior to discharge.
DISCHARGE DIAGNOSES:
1. Acute respiratory failure with hypoxia.
2. Chronic obstructive pulmonary disease with acute exacerbation.""",
        "codes": ["J96.01", "J44.1"]
    }
]

def generate_splits():
    # Save label map
    label_map_path = os.path.join(DATA_DIR, "label_map.json")
    with open(label_map_path, "w", encoding="utf-8") as f:
        json.dump(LABEL_MAP, f, indent=2)
    print(f"Saved label map with {len(LABEL_MAP)} codes to: {label_map_path}")

    # Split: Train (7 records), Val (2 records), Test (3 records)
    train_records = SAMPLE_RECORDS[:7]
    val_records = SAMPLE_RECORDS[7:9]
    test_records = SAMPLE_RECORDS[9:]

    for name, records in [("train", train_records), ("val", val_records), ("test", test_records)]:
        rows = []
        for r in records:
            rows.append({
                "document_id": r["document_id"],
                "text": r["text"].replace("\n", " "),
                "codes": ";".join(r["codes"])
            })
        df = pd.DataFrame(rows)
        csv_path = os.path.join(DATA_DIR, f"{name}.csv")
        df.to_csv(csv_path, index=False)
        print(f"Saved {name}.csv with {len(df)} records to: {csv_path}")

if __name__ == "__main__":
    generate_splits()

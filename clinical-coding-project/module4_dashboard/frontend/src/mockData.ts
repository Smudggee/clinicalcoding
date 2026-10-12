import type { CaseItem, AuditEntry, SystemUser } from "./types";

// Discharge note for Case 1 - Pneumonia + T2DM + HTN
const DISCHARGE_TEXT_1 =
  "Patient is a 68-year-old male presenting with a 5-day history of productive cough with yellowish sputum, fever reaching 39.2°C, and progressive dyspnea on exertion. Physical examination revealed decreased breath sounds and dullness to percussion at the right lower lobe. Chest radiograph confirmed right lower lobe consolidation consistent with community-acquired pneumonia. Patient has a known history of Type 2 diabetes mellitus with HbA1c of 8.2% and essential hypertension, currently managed with metformin 1000mg twice daily and lisinopril 10mg once daily. Sputum culture collected; empiric antibiotic therapy commenced with amoxicillin-clavulanate 875/125mg twice daily. Blood glucose levels monitored closely given infection-induced hyperglycemia with readings between 180-240 mg/dL during admission. Patient discharged after a 4-day inpatient stay with a 7-day course of oral antibiotics. Follow-up appointment scheduled in one week with primary care physician for reassessment and repeat chest X-ray.";

// Discharge note for Case 2 - COPD exacerbation + CKD
const DISCHARGE_TEXT_2 =
  "Patient is a 55-year-old female with a known history of chronic obstructive pulmonary disease (COPD) admitted with acute exacerbation characterized by increased breathlessness, worsening productive cough with green sputum, and reduced exercise tolerance over 3 days. Spirometry on admission showed FEV1/FVC ratio of 0.58. She also carries a diagnosis of chronic kidney disease stage 3 with baseline eGFR of 38 mL/min/1.73m². Hypertension is managed with amlodipine 5mg once daily. Treatment included systemic corticosteroids, nebulized bronchodilators, and antibiotics. Creatinine levels monitored throughout admission; no significant acute-on-chronic deterioration noted. Patient responded well and was discharged on optimized inhalers with written exacerbation action plan.";

// Discharge note for Case 3 - Pneumonia + COPD history
const DISCHARGE_TEXT_3 =
  "Patient is a 72-year-old male with personal history of COPD presenting with 3-day history of increasing cough, purulent sputum, and fever of 38.6°C. Oxygen saturation on room air was 91%. CT chest demonstrated patchy consolidation in the left lower lobe raising concern for pneumonia. Given the background of COPD, distinguishing pneumonia from exacerbation was clinically challenging. Treatment initiated with broad-spectrum antibiotics alongside bronchodilator therapy. Patient's previous COPD diagnosis documented from prior admissions; current spirometry deferred due to acute illness. Discharged stable on oral antibiotics and continued COPD maintenance therapy with follow-up in respiratory clinic.";

// Discharge note for Case 4 - T2DM + HTN + CKD
const DISCHARGE_TEXT_4 =
  "Patient is a 61-year-old female admitted for optimization of poorly controlled Type 2 diabetes mellitus. HbA1c on admission 9.8%; fasting blood glucose consistently above 200 mg/dL. Background of essential hypertension managed with ramipril and amlodipine. Renal function consistent with chronic kidney disease stage 3 (eGFR 42 mL/min/1.73m²). Insulin regimen titrated during admission with diabetes nurse specialist input. Renal diet counseling provided. Blood pressure controlled at 138/82 on current regimen. Discharged with basal insulin glargine 18 units nightly added to existing metformin with close outpatient glucose monitoring arranged.";

// Discharge note for Case 5 - Multi-morbidity
const DISCHARGE_TEXT_5 =
  "Patient is a 79-year-old male with complex multi-morbidity admitted with acute COPD exacerbation. Background conditions include Type 2 diabetes mellitus, essential hypertension, and chronic kidney disease stage 3. Exacerbation triggered by viral upper respiratory tract infection. Significant dyspnea, oxygen requirement up to 4L/min on admission. Blood glucose elevated in context of corticosteroid use; insulin sliding scale implemented. Antihypertensive medications temporarily held given borderline renal function (eGFR 35 mL/min/1.73m²). Personal history of prior COPD exacerbations requiring hospitalisation documented. Discharged on rescue pack and optimized inhalers. Referral made to integrated COPD respiratory team.";

function tokenize(text: string): string[] {
  return text.split(/(\s+)/).filter((t) => t.trim().length > 0);
}

const words1 = tokenize(DISCHARGE_TEXT_1);
const words2 = tokenize(DISCHARGE_TEXT_2);
const words3 = tokenize(DISCHARGE_TEXT_3);
const words4 = tokenize(DISCHARGE_TEXT_4);
const words5 = tokenize(DISCHARGE_TEXT_5);

// Helper: find word indices containing a keyword
function findIndices(words: string[], keywords: string[]): number[] {
  return words.reduce<number[]>((acc, w, i) => {
    if (keywords.some((k) => w.toLowerCase().includes(k.toLowerCase()))) acc.push(i);
    return acc;
  }, []);
}

// Build attention spans from keyword indices
function spansFromIndices(indices: number[], weight: number) {
  return indices.map((i) => ({ startIdx: i, endIdx: i + 1, weight }));
}

export const MOCK_CASES: CaseItem[] = [
  {
    id: "CASE-2024-0831",
    patientId: "P-4821",
    submittedAt: "2026-09-14T08:14:00Z",
    status: "Pending Review",
    averageConfidence: 91,
    dischargeText: DISCHARGE_TEXT_1,
    words: words1,
    predictedCodes: [
      {
        id: "c1-1",
        code: "J18.9",
        description: "Pneumonia, unspecified organism",
        confidence: 92,
        verificationStatus: "VERIFIED",
        supportingEvidence: "productive cough with yellowish sputum, fever reaching 39.2°C … right lower lobe consolidation consistent with community-acquired pneumonia",
        attentionSpans: [
          ...spansFromIndices(findIndices(words1, ["pneumonia", "consolidation", "cough", "sputum", "fever", "dyspnea", "antibiotic", "radiograph"]), 0.9),
          ...spansFromIndices(findIndices(words1, ["breath", "percussion", "lobe"]), 0.6),
        ],
      },
      {
        id: "c1-2",
        code: "E11.9",
        description: "Type 2 diabetes mellitus without complications",
        confidence: 87,
        verificationStatus: "VERIFIED",
        supportingEvidence: "Type 2 diabetes mellitus with HbA1c of 8.2% … infection-induced hyperglycemia with readings between 180-240 mg/dL",
        attentionSpans: [
          ...spansFromIndices(findIndices(words1, ["diabetes", "HbA1c", "metformin", "glucose", "hyperglycemia"]), 0.95),
          ...spansFromIndices(findIndices(words1, ["mellitus", "mg/dL", "blood"]), 0.65),
        ],
      },
      {
        id: "c1-3",
        code: "I10",
        description: "Essential (primary) hypertension",
        confidence: 94,
        verificationStatus: "UNVERIFIED",
        supportingEvidence: "essential hypertension, currently managed with … lisinopril 10mg once daily",
        attentionSpans: [
          ...spansFromIndices(findIndices(words1, ["hypertension", "lisinopril"]), 0.95),
          ...spansFromIndices(findIndices(words1, ["managed", "daily"]), 0.4),
        ],
      },
    ],
  },
  {
    id: "CASE-2024-0832",
    patientId: "P-3317",
    submittedAt: "2026-09-14T09:02:00Z",
    status: "Processing",
    averageConfidence: 85,
    dischargeText: DISCHARGE_TEXT_2,
    words: words2,
    predictedCodes: [
      {
        id: "c2-1",
        code: "J44.1",
        description: "Chronic obstructive pulmonary disease with (acute) exacerbation",
        confidence: 89,
        verificationStatus: "PARENT CODE",
        supportingEvidence: "chronic obstructive pulmonary disease (COPD) admitted with acute exacerbation … increased breathlessness, worsening productive cough",
        attentionSpans: [
          ...spansFromIndices(findIndices(words2, ["COPD", "obstructive", "exacerbation", "breathlessness", "cough", "spirometry", "FEV1", "bronchodilators"]), 0.9),
          ...spansFromIndices(findIndices(words2, ["pulmonary", "chronic", "exercise"]), 0.55),
        ],
      },
      {
        id: "c2-2",
        code: "N18.3",
        description: "Chronic kidney disease, stage 3 (moderate)",
        confidence: 76,
        verificationStatus: "UNVERIFIED",
        supportingEvidence: "chronic kidney disease stage 3 with baseline eGFR of 38 mL/min/1.73m² … Creatinine levels monitored",
        attentionSpans: [
          ...spansFromIndices(findIndices(words2, ["kidney", "eGFR", "creatinine", "renal"]), 0.92),
          ...spansFromIndices(findIndices(words2, ["stage", "chronic", "monitored"]), 0.5),
        ],
      },
      {
        id: "c2-3",
        code: "I10",
        description: "Essential (primary) hypertension",
        confidence: 91,
        verificationStatus: "UNVERIFIED",
        supportingEvidence: "Hypertension is managed with amlodipine 5mg once daily",
        attentionSpans: [
          ...spansFromIndices(findIndices(words2, ["Hypertension", "amlodipine"]), 0.93),
          ...spansFromIndices(findIndices(words2, ["managed", "once"]), 0.3),
        ],
      },
    ],
  },
  {
    id: "CASE-2024-0833",
    patientId: "P-7740",
    submittedAt: "2026-09-14T09:47:00Z",
    status: "Pending Review",
    averageConfidence: 63,
    dischargeText: DISCHARGE_TEXT_3,
    words: words3,
    predictedCodes: [
      {
        id: "c3-1",
        code: "J18.9",
        description: "Pneumonia, unspecified organism",
        confidence: 45,
        verificationStatus: "UNVERIFIED",
        supportingEvidence: "CT chest demonstrated patchy consolidation in the left lower lobe raising concern for pneumonia",
        attentionSpans: [
          ...spansFromIndices(findIndices(words3, ["pneumonia", "consolidation", "CT", "chest", "antibiotics"]), 0.85),
          ...spansFromIndices(findIndices(words3, ["concern", "patchy", "lobe"]), 0.6),
        ],
      },
      {
        id: "c3-2",
        code: "Z87.891",
        description: "Personal history of other specified conditions",
        confidence: 83,
        verificationStatus: "VERIFIED",
        supportingEvidence: "personal history of COPD presenting … background of COPD … previous COPD diagnosis documented from prior admissions",
        attentionSpans: [
          ...spansFromIndices(findIndices(words3, ["history", "COPD", "prior", "previous", "admissions"]), 0.9),
          ...spansFromIndices(findIndices(words3, ["personal", "background", "documented"]), 0.55),
        ],
      },
      {
        id: "c3-3",
        code: "J44.1",
        description: "Chronic obstructive pulmonary disease with (acute) exacerbation",
        confidence: 61,
        verificationStatus: "UNVERIFIED",
        supportingEvidence: "Given the background of COPD, distinguishing pneumonia from exacerbation was clinically challenging",
        attentionSpans: [
          ...spansFromIndices(findIndices(words3, ["COPD", "exacerbation", "bronchodilator", "inhalers"]), 0.8),
          ...spansFromIndices(findIndices(words3, ["maintenance", "therapy", "distinguishing"]), 0.45),
        ],
      },
    ],
  },
  {
    id: "CASE-2024-0834",
    patientId: "P-1195",
    submittedAt: "2026-09-14T10:30:00Z",
    status: "Completed",
    averageConfidence: 81,
    dischargeText: DISCHARGE_TEXT_4,
    words: words4,
    predictedCodes: [
      {
        id: "c4-1",
        code: "E11.9",
        description: "Type 2 diabetes mellitus without complications",
        confidence: 96,
        verificationStatus: "VERIFIED",
        userAction: "confirmed",
        supportingEvidence: "poorly controlled Type 2 diabetes mellitus. HbA1c on admission 9.8%; fasting blood glucose consistently above 200 mg/dL",
        attentionSpans: [
          ...spansFromIndices(findIndices(words4, ["diabetes", "HbA1c", "glucose", "metformin", "insulin", "glargine"]), 0.95),
          ...spansFromIndices(findIndices(words4, ["fasting", "mellitus", "controlled"]), 0.6),
        ],
      },
      {
        id: "c4-2",
        code: "I10",
        description: "Essential (primary) hypertension",
        confidence: 93,
        verificationStatus: "VERIFIED",
        userAction: "confirmed",
        supportingEvidence: "essential hypertension managed with ramipril and amlodipine … Blood pressure controlled at 138/82",
        attentionSpans: [
          ...spansFromIndices(findIndices(words4, ["hypertension", "ramipril", "amlodipine", "pressure"]), 0.92),
          ...spansFromIndices(findIndices(words4, ["blood", "controlled", "regimen"]), 0.45),
        ],
      },
      {
        id: "c4-3",
        code: "N18.3",
        description: "Chronic kidney disease, stage 3 (moderate)",
        confidence: 78,
        verificationStatus: "UNVERIFIED",
        userAction: "confirmed",
        supportingEvidence: "chronic kidney disease stage 3 (eGFR 42 mL/min/1.73m²) … Renal diet counseling provided",
        attentionSpans: [
          ...spansFromIndices(findIndices(words4, ["kidney", "eGFR", "renal", "creatinine"]), 0.9),
          ...spansFromIndices(findIndices(words4, ["stage", "diet", "function"]), 0.5),
        ],
      },
      {
        id: "c4-4",
        code: "E11.65",
        description: "Type 2 diabetes mellitus with hyperglycemia",
        confidence: 55,
        verificationStatus: "UNVERIFIED",
        userAction: "overridden",
        overrideCode: "E11.9",
        overrideReason: "Code specificity",
        supportingEvidence: "blood glucose consistently above 200 mg/dL … insulin sliding scale implemented",
        attentionSpans: [
          ...spansFromIndices(findIndices(words4, ["glucose", "insulin", "200", "mg/dL"]), 0.8),
          ...spansFromIndices(findIndices(words4, ["fasting", "diabetes"]), 0.5),
        ],
      },
    ],
    submittedToBilling: true,
  },
  {
    id: "CASE-2024-0835",
    patientId: "P-9063",
    submittedAt: "2026-09-14T11:05:00Z",
    status: "Pending Review",
    averageConfidence: 79,
    dischargeText: DISCHARGE_TEXT_5,
    words: words5,
    predictedCodes: [
      {
        id: "c5-1",
        code: "J44.1",
        description: "Chronic obstructive pulmonary disease with (acute) exacerbation",
        confidence: 88,
        verificationStatus: "UNVERIFIED",
        supportingEvidence: "acute COPD exacerbation … Exacerbation triggered by viral upper respiratory tract infection. Significant dyspnea, oxygen requirement up to 4L/min",
        attentionSpans: [
          ...spansFromIndices(findIndices(words5, ["COPD", "exacerbation", "dyspnea", "oxygen", "bronchodilators", "inhalers", "rescue"]), 0.92),
          ...spansFromIndices(findIndices(words5, ["breathlessness", "respiratory", "viral"]), 0.6),
        ],
      },
      {
        id: "c5-2",
        code: "I10",
        description: "Essential (primary) hypertension",
        confidence: 90,
        verificationStatus: "UNVERIFIED",
        supportingEvidence: "essential hypertension … Antihypertensive medications temporarily held given borderline renal function",
        attentionSpans: [
          ...spansFromIndices(findIndices(words5, ["hypertension", "antihypertensive"]), 0.92),
          ...spansFromIndices(findIndices(words5, ["medications", "held"]), 0.35),
        ],
      },
      {
        id: "c5-3",
        code: "N18.3",
        description: "Chronic kidney disease, stage 3 (moderate)",
        confidence: 67,
        verificationStatus: "UNVERIFIED",
        supportingEvidence: "chronic kidney disease stage 3 … eGFR 35 mL/min/1.73m² … renal function",
        attentionSpans: [
          ...spansFromIndices(findIndices(words5, ["kidney", "eGFR", "renal"]), 0.9),
          ...spansFromIndices(findIndices(words5, ["stage", "chronic", "borderline"]), 0.55),
        ],
      },
      {
        id: "c5-4",
        code: "E11.9",
        description: "Type 2 diabetes mellitus without complications",
        confidence: 82,
        verificationStatus: "UNVERIFIED",
        supportingEvidence: "Type 2 diabetes mellitus … Blood glucose elevated in context of corticosteroid use; insulin sliding scale implemented",
        attentionSpans: [
          ...spansFromIndices(findIndices(words5, ["diabetes", "glucose", "insulin", "corticosteroid"]), 0.9),
          ...spansFromIndices(findIndices(words5, ["mellitus", "elevated", "scale"]), 0.5),
        ],
      },
      {
        id: "c5-5",
        code: "Z87.891",
        description: "Personal history of other specified conditions",
        confidence: 71,
        verificationStatus: "UNVERIFIED",
        supportingEvidence: "Personal history of prior COPD exacerbations requiring hospitalisation documented",
        attentionSpans: [
          ...spansFromIndices(findIndices(words5, ["Personal", "history", "prior", "hospitalisation", "documented"]), 0.88),
          ...spansFromIndices(findIndices(words5, ["COPD", "exacerbations"]), 0.55),
        ],
      },
    ],
  },
];

export const MOCK_AUDIT: AuditEntry[] = [
  {
    id: "AUD-001",
    timestamp: "2026-09-14T10:32:18Z",
    coderName: "Sarah Chen",
    caseId: "CASE-2024-0834",
    action: "Submitted",
    codeAffected: "ALL",
    oldValue: "—",
    newValue: "Submitted to billing",
  },
  {
    id: "AUD-002",
    timestamp: "2026-09-14T10:31:05Z",
    coderName: "Sarah Chen",
    caseId: "CASE-2024-0834",
    action: "Overridden",
    codeAffected: "E11.65",
    oldValue: "E11.65",
    newValue: "E11.9",
  },
  {
    id: "AUD-003",
    timestamp: "2026-09-14T10:29:40Z",
    coderName: "Sarah Chen",
    caseId: "CASE-2024-0834",
    action: "Confirmed",
    codeAffected: "N18.3",
    oldValue: "—",
    newValue: "Confirmed",
  },
  {
    id: "AUD-004",
    timestamp: "2026-09-14T10:28:11Z",
    coderName: "Sarah Chen",
    caseId: "CASE-2024-0834",
    action: "Confirmed",
    codeAffected: "I10",
    oldValue: "—",
    newValue: "Confirmed",
  },
  {
    id: "AUD-005",
    timestamp: "2026-09-14T10:26:55Z",
    coderName: "Sarah Chen",
    caseId: "CASE-2024-0834",
    action: "Confirmed",
    codeAffected: "E11.9",
    oldValue: "—",
    newValue: "Confirmed",
  },
  {
    id: "AUD-006",
    timestamp: "2026-09-14T08:14:00Z",
    coderName: "BioBERT Model",
    caseId: "CASE-2024-0831",
    action: "Predicted",
    codeAffected: "J18.9, E11.9, I10",
    oldValue: "—",
    newValue: "Predicted (92%, 87%, 94%)",
  },
  {
    id: "AUD-007",
    timestamp: "2026-09-14T09:02:00Z",
    coderName: "BioBERT Model",
    caseId: "CASE-2024-0832",
    action: "Predicted",
    codeAffected: "J44.1, N18.3, I10",
    oldValue: "—",
    newValue: "Predicted (89%, 76%, 91%)",
  },
  {
    id: "AUD-008",
    timestamp: "2026-09-14T09:47:00Z",
    coderName: "BioBERT Model",
    caseId: "CASE-2024-0833",
    action: "Predicted",
    codeAffected: "J18.9, Z87.891, J44.1",
    oldValue: "—",
    newValue: "Predicted (45%, 83%, 61%)",
  },
  {
    id: "AUD-009",
    timestamp: "2026-09-14T10:25:00Z",
    coderName: "BioBERT Model",
    caseId: "CASE-2024-0834",
    action: "Predicted",
    codeAffected: "E11.9, I10, N18.3, E11.65",
    oldValue: "—",
    newValue: "Predicted (96%, 93%, 78%, 55%)",
  },
  {
    id: "AUD-010",
    timestamp: "2026-09-14T11:05:00Z",
    coderName: "BioBERT Model",
    caseId: "CASE-2024-0835",
    action: "Predicted",
    codeAffected: "J44.1, I10, N18.3, E11.9, Z87.891",
    oldValue: "—",
    newValue: "Predicted (88%, 90%, 67%, 82%, 71%)",
  },
];

export const MOCK_SYSTEM_USERS: SystemUser[] = [
  {
    id: "usr-001",
    name: "Sarah Chen",
    email: "s.chen@citymedical.org",
    role: "Medical Coder",
    active: true,
    lastLogin: "2026-09-14T08:02:00Z",
  },
  {
    id: "usr-002",
    name: "Marcus Reid",
    email: "m.reid@citymedical.org",
    role: "Medical Coder",
    active: true,
    lastLogin: "2026-09-14T07:48:00Z",
  },
  {
    id: "usr-003",
    name: "Dr. Patricia Wong",
    email: "p.wong@citymedical.org",
    role: "Physician",
    active: true,
    lastLogin: "2026-09-13T16:30:00Z",
  },
  {
    id: "usr-004",
    name: "James Okafor",
    email: "j.okafor@citymedical.org",
    role: "Administrator",
    active: true,
    lastLogin: "2026-09-14T07:30:00Z",
  },
  {
    id: "usr-005",
    name: "Aisha Patel",
    email: "a.patel@citymedical.org",
    role: "Medical Coder",
    active: false,
    lastLogin: "2026-09-01T09:15:00Z",
  },
];

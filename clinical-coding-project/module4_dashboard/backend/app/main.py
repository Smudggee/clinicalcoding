"""
FastAPI backend for the Human-in-the-Loop Review Dashboard (Section VI-F Module 4, Section VIII).

Integrates:
- Module 1 (Sliding-window Ingestion & Preprocessing)
- Module 2 (Multi-label Classification & Window Aggregation)
- Module 3 (Neuro-Symbolic Verification Engine)
- Module 4 (Full-stack HITL Review API: Auth, Cases, Overrides, Audit Trail, Dynamic Note Analysis)
"""
import os
import sys
import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from .schemas import (
    CodeResult, DocumentReview, ReviewAction,
    LoginRequest, LoginResponse, UserSchema,
    CaseItem, PredictedCode, AttentionSpan,
    AnalyzeRequest, ConfirmRequest, RejectRequest, OverrideRequest, SubmitRequest,
    AuditEntry, SystemSettings,
)
from .pipeline_service import ClinicalCodingPipeline
from .storage import SQLiteCaseAuditStore


def _utc_now() -> datetime:
    """Return an aware UTC timestamp for API and audit records."""
    return datetime.now(timezone.utc)

app = FastAPI(
    title="Clinical Coding Review Dashboard API",
    description="Backend API powering the hybrid neuro-symbolic clinical coding HITL dashboard",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the live Neuro-Symbolic Pipeline
pipeline = ClinicalCodingPipeline(review_threshold=0.50, auto_accept_threshold=0.85)

# SQLite-backed state is loaded into lists to preserve the existing route logic.
DATABASE_PATH = os.environ.get(
    "ACCS_DB_PATH",
    os.path.join(PROJECT_ROOT, "data", "accs_dashboard.sqlite3"),
)
storage = SQLiteCaseAuditStore(DATABASE_PATH)
CASES_STORE, AUDIT_STORE = storage.load_state()
settings_state = SystemSettings(**(storage.load_settings() or {}))
pipeline.update_thresholds(
    review_threshold=settings_state.review_threshold,
    auto_accept_threshold=settings_state.auto_accept_threshold,
)


def _persist_state():
    storage.save_state(CASES_STORE, AUDIT_STORE)


def _seed_initial_cases():
    """Initializes cases store with sample discharge summaries analyzed by the pipeline."""
    if getattr(pipeline, "classifier_status", None) == "load_failed":
        print("[Startup] Skipping demo-case seeding because the configured classifier failed to load.")
        return

    seed_pipeline = pipeline
    if getattr(pipeline, "classifier_status", None) in {"ready", "provider_configured"}:
        seed_pipeline = ClinicalCodingPipeline(
            review_threshold=pipeline.review_threshold,
            auto_accept_threshold=pipeline.auto_accept_threshold,
            enable_classifier=False,
        )

    sample_path = os.path.join(PROJECT_ROOT, "data", "sample_note.txt")
    if os.path.exists(sample_path):
        with open(sample_path, "r", encoding="utf-8") as f:
            sample_text = f.read()
        case_sample = seed_pipeline.analyze_document(
            document_id="CASE-2024-0831",
            raw_text=sample_text,
            patient_id="P-4821",
        )
        CASES_STORE.append(case_sample)

    # Add Case 2: COPD exacerbation + CKD
    case2_text = (
        "Patient is a 55-year-old female with a known history of chronic obstructive pulmonary disease "
        "(COPD) admitted with acute exacerbation characterized by increased breathlessness, worsening productive "
        "cough with green sputum, and reduced exercise tolerance over 3 days. Spirometry on admission showed FEV1/FVC "
        "ratio of 0.58. She also carries a diagnosis of chronic kidney disease stage 3 with baseline eGFR of "
        "38 mL/min/1.73m2. Hypertension is managed with amlodipine 5mg once daily. Treatment included systemic "
        "corticosteroids, nebulized bronchodilators, and antibiotics. Creatinine levels monitored throughout admission; "
        "no significant acute-on-chronic deterioration noted. Patient responded well and was discharged on optimized inhalers."
    )
    case2 = seed_pipeline.analyze_document(document_id="CASE-2024-0832", raw_text=case2_text, patient_id="P-6109")
    CASES_STORE.append(case2)

    # Add Case 3: Pneumonia + COPD history
    case3_text = (
        "Patient is a 72-year-old male with personal history of COPD presenting with 3-day history of increasing cough, "
        "purulent sputum, and fever of 38.6C. Oxygen saturation on room air was 91%. CT chest demonstrated patchy consolidation "
        "in the left lower lobe raising concern for pneumonia. Given the background of COPD, distinguishing pneumonia from "
        "exacerbation was clinically challenging. Treatment initiated with broad-spectrum antibiotics alongside bronchodilator therapy. "
        "Patient's previous COPD diagnosis documented from prior admissions. Discharged stable on oral antibiotics."
    )
    case3 = seed_pipeline.analyze_document(document_id="CASE-2024-0833", raw_text=case3_text, patient_id="P-7740")
    CASES_STORE.append(case3)

    # Seed initial audit trail entries
    AUDIT_STORE.append({
        "id": "AUD-1726301200000",
        "timestamp": "2026-09-14T09:12:00Z",
        "coderName": "Dr. Sarah Chen",
        "caseId": "CASE-2024-0831",
        "action": "Predicted",
        "codeAffected": "A41.9",
        "oldValue": "—",
        "newValue": "A41.9",
    })
    AUDIT_STORE.append({
        "id": "AUD-1726301300000",
        "timestamp": "2026-09-14T09:15:00Z",
        "coderName": "Dr. Sarah Chen",
        "caseId": "CASE-2024-0831",
        "action": "Confirmed",
        "codeAffected": "A41.9",
        "oldValue": "—",
        "newValue": "Confirmed",
    })


# Seed sample data only for a new/empty database; existing cases survive restart.
if not CASES_STORE:
    _seed_initial_cases()
    _persist_state()


# ==============================================================================
# 1. Health & System Settings Endpoints
# ==============================================================================

@app.get("/health")
def health():
    classifier_status = getattr(pipeline, "classifier_status", "unknown")
    if classifier_status == "ready":
        classifier_module_status = "module2_classifier (trained checkpoint loaded; inference ready)"
    elif classifier_status == "provider_configured":
        classifier_module_status = "module2_classifier (candidate provider configured)"
    elif classifier_status == "load_failed":
        classifier_module_status = "module2_classifier (checkpoint load failed; analysis will return an error)"
    else:
        classifier_module_status = "module2_classifier (interface available; no checkpoint configured)"
    return {
        "status": "ok",
        "version": "2.0.0",
        "modules": [
            "module1_ingestion (SlidingWindow)",
            classifier_module_status,
            "module3_verification (NeuroSymbolic Verification)",
            "module4_dashboard (HITL Review)",
        ],
        "classifier_status": classifier_status,
        "analysis_mode": "module2_classifier" if classifier_status in {"ready", "provider_configured"} else (
            "classifier_error" if classifier_status == "load_failed" else "rule_based_demo"
        ),
        "cases_count": len(CASES_STORE),
        "audit_entries_count": len(AUDIT_STORE),
    }


@app.get("/api/admin/settings", response_model=SystemSettings)
def get_settings():
    return settings_state


@app.post("/api/admin/settings", response_model=SystemSettings)
def update_settings(new_settings: SystemSettings):
    global settings_state
    settings_state = new_settings
    storage.save_settings(new_settings.model_dump())
    pipeline.update_thresholds(
        review_threshold=new_settings.review_threshold,
        auto_accept_threshold=new_settings.auto_accept_threshold,
    )
    return settings_state


# ==============================================================================
# 2. Authentication Endpoints
# ==============================================================================

@app.post("/api/auth/login", response_model=LoginResponse)
def login(creds: LoginRequest):
    if not creds.username or not creds.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")

    name = creds.username.split("@")[0].capitalize() if "@" in creds.username else creds.username
    token = f"jwt-token-{int(_utc_now().timestamp() * 1000)}"
    return LoginResponse(
        token=token,
        user=UserSchema(
            id=f"usr-{abs(hash(creds.username)) % 10000}",
            name=name,
            email=creds.username if "@" in creds.username else f"{creds.username}@hospital.org",
            role=creds.role,
            active=True,
        ),
    )


# ==============================================================================
# 3. Case Management Endpoints (Powers Dashboard.tsx & CaseReview.tsx)
# ==============================================================================

@app.get("/api/cases", response_model=List[CaseItem])
def get_cases(status: Optional[str] = Query(None)):
    if status:
        return [c for c in CASES_STORE if c.get("status") == status]
    return CASES_STORE


@app.get("/api/cases/{case_id}", response_model=CaseItem)
def get_case(case_id: str):
    case = next((c for c in CASES_STORE if c["id"] == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


@app.post("/api/cases/analyze", response_model=CaseItem)
def analyze_note(req: AnalyzeRequest):
    """
    Analyzes a note through ingestion, rule-based demo matching, and verification.
    """
    doc_id = req.document_id or f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    try:
        new_case = pipeline.analyze_document(
            document_id=doc_id,
            raw_text=req.text,
            patient_id=req.patient_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Clinical note analysis failed: {exc}") from exc

    # Insert at top of list
    CASES_STORE.insert(0, new_case)

    # Log analysis event
    AUDIT_STORE.insert(0, {
        "id": f"AUD-{uuid4().hex}",
        "timestamp": _utc_now().isoformat().replace("+00:00", "Z"),
        "coderName": "System Pipeline",
        "caseId": doc_id,
        "action": "Predicted",
        "codeAffected": f"{len(new_case['predictedCodes'])} codes",
        "oldValue": "—",
        "newValue": new_case["analysisSourceLabel"],
    })
    _persist_state()

    return new_case


MAX_AUDIO_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_AUDIO_SUFFIXES = {".m4a", ".mp3", ".wav", ".flac", ".ogg", ".aac"}


def _create_transcription_service():
    """Load the optional speech service only when an audio upload is requested."""
    from module1_ingestion.stt.whisper_service import WhisperTranscriptionService

    return WhisperTranscriptionService(model_size=os.environ.get("ACCS_WHISPER_MODEL", "small"))


@app.post("/api/transcribe")
async def transcribe_audio(
    request: Request,
    x_audio_filename: str = Header(..., alias="X-Audio-Filename"),
    language: Optional[str] = Query(None, description="Use 'ml', 'en', or omit for language detection."),
):
    """Return an experimental transcript draft for a human to review and correct."""
    suffix = Path(x_audio_filename).suffix.lower()
    if suffix not in ALLOWED_AUDIO_SUFFIXES:
        raise HTTPException(status_code=415, detail="Unsupported audio format.")
    if language not in {None, "ml", "en"}:
        raise HTTPException(status_code=422, detail="Language must be 'ml', 'en', or omitted for automatic detection.")

    audio_payload = bytearray()
    async for chunk in request.stream():
        audio_payload.extend(chunk)
        if len(audio_payload) > MAX_AUDIO_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Audio uploads must be 25 MB or smaller.")
    if not audio_payload:
        raise HTTPException(status_code=400, detail="The uploaded audio file is empty.")

    try:
        service = _create_transcription_service()
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Audio transcription is unavailable. Install the faster-whisper dependency first.",
        ) from exc

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as audio_file:
            audio_file.write(audio_payload)
            temp_path = audio_file.name
        result = await asyncio.to_thread(service.transcribe, temp_path, language=language)
        return {
            "transcript": result["transcript"],
            "language": result["language"],
            "languageProbability": result["language_probability"],
            "segments": result["segments"],
            "transcriptionSourceLabel": "Experimental local Whisper transcript; review and correct before analysis.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {exc}") from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


def _require_case_open_for_review(case: dict) -> None:
    if case.get("submittedToBilling"):
        raise HTTPException(status_code=409, detail="Submitted cases cannot be changed.")


@app.post("/api/cases/{case_id}/codes/{code_id}/confirm")
def confirm_code(case_id: str, code_id: str, req: ConfirmRequest):
    case = next((c for c in CASES_STORE if c["id"] == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    _require_case_open_for_review(case)

    code_obj = next((cd for cd in case["predictedCodes"] if cd["id"] == code_id), None)
    if not code_obj:
        raise HTTPException(status_code=404, detail="Code not found.")

    code_obj["userAction"] = "confirmed"

    AUDIT_STORE.insert(0, {
        "id": f"AUD-{uuid4().hex}",
        "timestamp": _utc_now().isoformat().replace("+00:00", "Z"),
        "coderName": req.coderName,
        "caseId": case_id,
        "action": "Confirmed",
        "codeAffected": code_obj["code"],
        "oldValue": "—",
        "newValue": "Confirmed",
    })
    _persist_state()
    return {"status": "ok", "message": f"Code {code_obj['code']} confirmed"}


@app.post("/api/cases/{case_id}/codes/{code_id}/reject")
def reject_code(case_id: str, code_id: str, req: RejectRequest):
    case = next((c for c in CASES_STORE if c["id"] == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    _require_case_open_for_review(case)

    code_obj = next((cd for cd in case["predictedCodes"] if cd["id"] == code_id), None)
    if not code_obj:
        raise HTTPException(status_code=404, detail="Code not found.")
    if not req.reason.strip():
        raise HTTPException(status_code=422, detail="A reason is required to reject a code.")

    code_obj["userAction"] = "rejected"
    code_obj["userReason"] = req.reason.strip()
    AUDIT_STORE.insert(0, {
        "id": f"AUD-{uuid4().hex}",
        "timestamp": _utc_now().isoformat().replace("+00:00", "Z"),
        "coderName": req.coderName,
        "caseId": case_id,
        "action": "Rejected",
        "codeAffected": code_obj["code"],
        "oldValue": "Pending review",
        "newValue": req.reason.strip(),
    })
    _persist_state()
    return {"status": "ok", "message": f"Code {code_obj['code']} rejected"}


@app.post("/api/cases/{case_id}/codes/{code_id}/override")
def override_code(case_id: str, code_id: str, req: OverrideRequest):
    case = next((c for c in CASES_STORE if c["id"] == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    _require_case_open_for_review(case)

    code_obj = next((cd for cd in case["predictedCodes"] if cd["id"] == code_id), None)
    if not code_obj:
        raise HTTPException(status_code=404, detail="Code not found.")

    old_code = code_obj["code"]
    code_obj["userAction"] = "overridden"
    code_obj["overrideCode"] = req.newCode
    code_obj["overrideReason"] = req.reason

    AUDIT_STORE.insert(0, {
        "id": f"AUD-{uuid4().hex}",
        "timestamp": _utc_now().isoformat().replace("+00:00", "Z"),
        "coderName": req.coderName,
        "caseId": case_id,
        "action": "Overridden",
        "codeAffected": old_code,
        "oldValue": old_code,
        "newValue": req.newCode,
    })
    _persist_state()
    return {"status": "ok", "message": f"Code {old_code} overridden to {req.newCode}"}


@app.post("/api/cases/{case_id}/submit")
def submit_case(case_id: str, req: SubmitRequest):
    case = next((c for c in CASES_STORE if c["id"] == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    if case.get("submittedToBilling"):
        raise HTTPException(status_code=409, detail="Case has already been submitted.")

    predicted_codes = case.get("predictedCodes", [])
    if any(not code.get("userAction") for code in predicted_codes):
        raise HTTPException(status_code=409, detail="Review every predicted code before submitting the case.")
    if not any(code.get("userAction") in {"confirmed", "overridden"} for code in predicted_codes):
        raise HTTPException(status_code=409, detail="Confirm or override at least one code before submitting the case.")

    case["status"] = "Completed"
    case["submittedToBilling"] = True

    AUDIT_STORE.insert(0, {
        "id": f"AUD-{uuid4().hex}",
        "timestamp": _utc_now().isoformat().replace("+00:00", "Z"),
        "coderName": req.coderName,
        "caseId": case_id,
        "action": "Submitted",
        "codeAffected": "ALL",
        "oldValue": "—",
        "newValue": "Submitted to billing",
    })
    _persist_state()
    return {"status": "ok", "message": "Case submitted to billing"}


# ==============================================================================
# 4. Audit Trail Endpoints (Powers AuditTrail.tsx)
# ==============================================================================

@app.get("/api/audit", response_model=List[AuditEntry])
def get_audit(
    caseId: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
):
    results = AUDIT_STORE
    if caseId:
        results = [a for a in results if a["caseId"] == caseId]
    if from_date:
        results = [a for a in results if a["timestamp"] >= from_date]
    if to_date:
        results = [a for a in results if a["timestamp"] <= to_date + "T23:59:59Z"]
    return results


# ==============================================================================
# 5. Backward Compatible Paper Evaluation Endpoints (docs/interfaces.md)
# ==============================================================================

@app.post("/predict", response_model=DocumentReview)
def predict(document_id: str, text: str):
    res = pipeline.analyze_document(document_id=document_id, raw_text=text)
    code_results = [
        CodeResult(
            code=c["code"],
            probability=c["confidence"] / 100.0,
            verification_status="accepted" if c["verificationStatus"] == "VERIFIED" else ("needs_review" if c["verificationStatus"] == "PARENT CODE" else "rejected"),
            reject_reason=c.get("rejectReason"),
            evidence_span=c.get("supportingEvidence", ""),
        )
        for c in res["predictedCodes"]
    ]
    return DocumentReview(document_id=document_id, results=code_results)


@app.post("/review")
def submit_review(action: ReviewAction):
    AUDIT_STORE.insert(0, {
        "id": f"AUD-{uuid4().hex}",
        "timestamp": _utc_now().isoformat().replace("+00:00", "Z"),
        "coderName": "Reviewer",
        "caseId": action.document_id,
        "action": action.human_action.capitalize(),
        "codeAffected": action.code,
        "oldValue": "—",
        "newValue": action.human_action,
    })
    _persist_state()
    return {"status": "recorded", "log_size": len(AUDIT_STORE)}


@app.get("/audit-log")
def get_audit_log():
    return AUDIT_STORE

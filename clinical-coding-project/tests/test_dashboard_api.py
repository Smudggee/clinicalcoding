import os
import atexit
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Keep module-level FastAPI startup seeding in an ignored, workspace-local file.
_TEST_DATABASE_DIR = Path(__file__).resolve().parent / ".test_runtime"
_TEST_DATABASE_DIR.mkdir(exist_ok=True)
_STARTUP_DATABASE = _TEST_DATABASE_DIR / "startup.sqlite3"
os.environ["ACCS_DB_PATH"] = str(_STARTUP_DATABASE)
atexit.register(lambda: _STARTUP_DATABASE.unlink(missing_ok=True))

from module4_dashboard.backend.app import main
from module4_dashboard.backend.app.schemas import AnalyzeRequest, RejectRequest, SystemSettings
from module4_dashboard.backend.app.storage import SQLiteCaseAuditStore


@pytest.fixture
def test_database_path():
    path = _TEST_DATABASE_DIR / f"{uuid4().hex}.sqlite3"
    yield path
    path.unlink(missing_ok=True)


def test_health_reports_classifier_as_unconfigured():
    health = main.health()

    assert any("not configured" in module for module in health["modules"])


def test_admin_settings_validate_and_persist(monkeypatch, test_database_path):
    class _ThresholdRecorder:
        review_threshold = None
        auto_accept_threshold = None

        def update_thresholds(self, review_threshold, auto_accept_threshold):
            self.review_threshold = review_threshold
            self.auto_accept_threshold = auto_accept_threshold

    store = SQLiteCaseAuditStore(test_database_path)
    monkeypatch.setattr(main, "storage", store)
    monkeypatch.setattr(main, "settings_state", SystemSettings())
    monkeypatch.setattr(main, "pipeline", _ThresholdRecorder())

    with TestClient(main.app) as client:
        updated = client.post(
            "/api/admin/settings",
            json={"auto_accept_threshold": 0.9, "review_threshold": 0.4},
        )
        assert updated.status_code == 200
        assert updated.json()["auto_accept_threshold"] == 0.9
        assert main.pipeline.auto_accept_threshold == 0.9

        invalid = client.post(
            "/api/admin/settings",
            json={"auto_accept_threshold": 1.2, "review_threshold": 0.4},
        )
        assert invalid.status_code == 422

        loaded = client.get("/api/admin/settings")
        assert loaded.status_code == 200
        assert loaded.json()["auto_accept_threshold"] == 0.9

    reloaded_settings = SQLiteCaseAuditStore(test_database_path).load_settings()
    assert reloaded_settings["auto_accept_threshold"] == 0.9
    assert reloaded_settings["review_threshold"] == 0.4


def test_analyze_note_returns_clear_error_when_pipeline_fails(monkeypatch):
    class _FailingPipeline:
        def analyze_document(self, **kwargs):
            raise RuntimeError("model dependency unavailable")

    monkeypatch.setattr(main, "pipeline", _FailingPipeline())

    with pytest.raises(HTTPException) as exc:
        main.analyze_note(AnalyzeRequest(text="example note"))

    assert exc.value.status_code == 500
    assert "Clinical note analysis failed" in exc.value.detail


def test_analysis_source_and_audit_persist_over_http(monkeypatch, test_database_path):
    monkeypatch.setattr(main, "CASES_STORE", [])
    monkeypatch.setattr(main, "AUDIT_STORE", [])
    monkeypatch.setattr(main, "storage", SQLiteCaseAuditStore(test_database_path))

    with TestClient(main.app) as client:
        response = client.post(
            "/api/cases/analyze",
            json={
                "document_id": "CASE-ANALYSIS-PERSIST-1",
                "patient_id": "PATIENT-TEST-1",
                "text": "Discharge diagnosis: community-acquired pneumonia. Treated with antibiotics.",
            },
        )

        assert response.status_code == 200
        analyzed_case = response.json()
        assert analyzed_case["analysisSource"] == "rule_based_demo"
        assert "not BioClinicalBERT" in analyzed_case["analysisSourceLabel"]
        assert any(code["code"] == "J18.9" for code in analyzed_case["predictedCodes"])

        audit_response = client.get(
            "/api/audit", params={"caseId": "CASE-ANALYSIS-PERSIST-1"}
        )
        assert audit_response.status_code == 200
        assert audit_response.json()[0]["action"] == "Predicted"

    # Loading through a new store simulates the backend starting again.
    persisted_cases, persisted_audit = SQLiteCaseAuditStore(test_database_path).load_state()
    assert persisted_cases[0]["id"] == "CASE-ANALYSIS-PERSIST-1"
    assert persisted_cases[0]["analysisSource"] == "rule_based_demo"
    assert persisted_audit[0]["action"] == "Predicted"
    assert persisted_audit[0]["caseId"] == "CASE-ANALYSIS-PERSIST-1"


def test_reject_code_records_review_reason_and_audit(monkeypatch, test_database_path):
    case = {
        "id": "case-reject-test",
        "predictedCodes": [{"id": "code-1", "code": "J18.9"}],
    }
    audit = []
    monkeypatch.setattr(main, "CASES_STORE", [case])
    monkeypatch.setattr(main, "AUDIT_STORE", audit)
    monkeypatch.setattr(main, "storage", SQLiteCaseAuditStore(test_database_path))

    result = main.reject_code(
        "case-reject-test",
        "code-1",
        RejectRequest(reason="Not supported by documentation", coderName="Reviewer"),
    )

    assert result["status"] == "ok"
    assert case["predictedCodes"][0]["userAction"] == "rejected"
    assert case["predictedCodes"][0]["userReason"] == "Not supported by documentation"
    assert audit[0]["action"] == "Rejected"
    assert audit[0]["newValue"] == "Not supported by documentation"


def test_case_review_actions_and_audit_trail_over_http(monkeypatch, test_database_path):
    case = {
        "id": "CASE-HTTP-1",
        "patientId": "P-1001",
        "submittedAt": "2026-10-20T10:00:00Z",
        "status": "Pending Review",
        "averageConfidence": 75,
        "dischargeText": "Sample note",
        "words": ["Sample", "note"],
        "predictedCodes": [
            {"id": "code-confirm", "code": "A41.9", "description": "Sepsis", "confidence": 75,
             "verificationStatus": "UNVERIFIED", "attentionSpans": [], "supportingEvidence": "sepsis"},
            {"id": "code-override", "code": "J18.9", "description": "Pneumonia", "confidence": 75,
             "verificationStatus": "UNVERIFIED", "attentionSpans": [], "supportingEvidence": "pneumonia"},
            {"id": "code-reject", "code": "E11.9", "description": "Diabetes", "confidence": 75,
             "verificationStatus": "UNVERIFIED", "attentionSpans": [], "supportingEvidence": "diabetes"},
        ],
        "submittedToBilling": False,
        "analysisSource": "rule_based_demo",
        "analysisSourceLabel": "Test fixture",
    }
    monkeypatch.setattr(main, "CASES_STORE", [case])
    monkeypatch.setattr(main, "AUDIT_STORE", [])
    database_path = test_database_path
    monkeypatch.setattr(main, "storage", SQLiteCaseAuditStore(database_path))

    with TestClient(main.app) as client:
        assert client.get("/api/cases/CASE-HTTP-1").status_code == 200
        assert client.post("/api/cases/CASE-HTTP-1/codes/code-confirm/confirm", json={"coderName": "Coder"}).status_code == 200
        assert client.post(
            "/api/cases/CASE-HTTP-1/codes/code-override/override",
            json={"newCode": "J18.1", "reason": "More specific", "coderName": "Coder"},
        ).status_code == 200
        assert client.post(
            "/api/cases/CASE-HTTP-1/codes/code-reject/reject",
            json={"reason": "Not documented", "coderName": "Coder"},
        ).status_code == 200

        reviewed_case = client.get("/api/cases/CASE-HTTP-1").json()
        actions = {code["id"]: code["userAction"] for code in reviewed_case["predictedCodes"]}
        assert actions == {"code-confirm": "confirmed", "code-override": "overridden", "code-reject": "rejected"}
        assert next(code for code in reviewed_case["predictedCodes"] if code["id"] == "code-reject")["userReason"] == "Not documented"

        audit_response = client.get("/api/audit", params={"caseId": "CASE-HTTP-1"})
        assert audit_response.status_code == 200
        audit = audit_response.json()
        assert {entry["action"] for entry in audit} == {"Confirmed", "Overridden", "Rejected"}
        assert {entry["newValue"] for entry in audit} >= {"Confirmed", "J18.1", "Not documented"}
        assert len({entry["id"] for entry in audit}) == len(audit)

        submit_response = client.post("/api/cases/CASE-HTTP-1/submit", json={"coderName": "Coder"})
        assert submit_response.status_code == 200
        submitted_case = client.get("/api/cases/CASE-HTTP-1").json()
        assert submitted_case["status"] == "Completed"
        assert submitted_case["submittedToBilling"] is True
        final_audit = client.get("/api/audit", params={"caseId": "CASE-HTTP-1"}).json()
        assert [entry["action"] for entry in final_audit].count("Submitted") == 1

    # A newly opened store simulates a backend restart and must restore both records.
    persisted_cases, persisted_audit = SQLiteCaseAuditStore(database_path).load_state()
    assert persisted_cases[0]["status"] == "Completed"
    assert persisted_cases[0]["predictedCodes"][2]["userReason"] == "Not documented"
    assert {entry["action"] for entry in persisted_audit} >= {"Confirmed", "Overridden", "Rejected", "Submitted"}

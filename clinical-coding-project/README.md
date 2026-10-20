# Automated Clinical Coding — Hybrid Neuro-Symbolic Framework

Implementation scaffold for the four-module architecture proposed in Section VI-F
of "Automated Clinical Coding Using Transformer-Based Language Models: A Survey
of Methods, Research Gaps, and a Hybrid Neuro-Symbolic Framework."

## Architecture (matches the paper 1:1)

| Module | Paper Section | Folder | Owns |
|---|---|---|---|
| 1. Sliding-Window Ingestion & Preprocessing | III-C | `module1_ingestion/` | Chunking discharge summaries into 512-token windows (stride 256), normalization, tokenization |
| 2. BioClinicalBERT + Weighted Classification | III-B, VI-F | `module2_classifier/` | Multi-label ICD-10 prediction, focal loss / class-weighted BCE, window aggregation (Eq. 1) |
| 3. Neuro-Symbolic Verification Engine | VI-F, VIII | `module3_verification/` | Format validity, negation detection, temporal consistency, exclusion rules, HER/VRR (Eq. 4–5) |
| 4. Human-in-the-Loop Dashboard | VI-F | `module4_dashboard/` | FastAPI backend + React frontend for coder review, evidence highlighting, sign-off |

Cutting across all four: `evaluation/` implements the metrics from Section VII
(micro/macro F1, Precision@K, HER, VRR) so results are comparable regardless of
which module changes.

## Suggested 4-person split

Since each module has a clean interface (see `docs/interfaces.md`), one person
can own each module end-to-end and integrate via the contracts below:

- **Person A — Ingestion**: `module1_ingestion/` — turns a raw discharge summary
  into a list of token windows with offsets, ready for the classifier.
- **Person B — Classifier**: `module2_classifier/` — turns windows into
  per-code probabilities, then aggregates to document-level scores.
- **Person C — Verification**: `module3_verification/` — turns
  (code, probability, evidence span) triples into accept/reject/route-to-human
  decisions.
- **Person D — Dashboard + Evaluation**: `module4_dashboard/` and
  `evaluation/` — surfaces everything to a reviewer and computes the paper's
  metrics for the write-up.

All four modules are independently testable (see `tests/`) so you don't block
on each other — agree on the JSON contract in `docs/interfaces.md` first, then
build against mocked inputs/outputs until integration.

## Getting started

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# run the module-level unit tests
pytest tests/

# run the full pipeline on a sample note
python -m module1_ingestion.pipeline_demo
```

For the dashboard:
```bash
cd module4_dashboard/backend
python -m pip install -r ../../requirements.txt
python -m uvicorn app.main:app --app-dir . --reload

# In a second terminal, from the project root:
cd module4_dashboard/frontend
npm ci
npm run dev
```

The backend dependencies are listed in the project-root `requirements.txt`;
there is no separate backend requirements file. From the project root, install
them with `python -m pip install -r requirements.txt` before starting Uvicorn.

For PowerShell, the same commands are:

```powershell
# Run these from the project root.
python -m pip install -r requirements.txt
Set-Location module4_dashboard\backend
python -m uvicorn app.main:app --app-dir . --reload
```

In another PowerShell terminal:

```powershell
# In another terminal, run these from the project root.
Set-Location module4_dashboard\frontend
npm ci
npm run dev
```

The API documentation is available at `http://localhost:8000/docs`. Cases,
audit entries, and dashboard settings are stored in the local SQLite database
at `data/accs_dashboard.sqlite3` by default. Set `ACCS_DB_PATH` before starting
the backend to select another database file.

### Module 4 workflow and current limits

- Submit a note from the Dashboard or `POST /api/cases/analyze`. The current
  source is labelled `rule_based_demo`: candidate codes come from keyword
  matching against an illustrative ICD-10 knowledge base and then pass through
  the Module 3 verifier. These scores are not BioClinicalBERT predictions.
- Confirm, reject, override, and submit actions update the case and create audit
  entries. Case data, audit history, and verifier thresholds persist in SQLite.
- The Admin threshold is loaded from and saved to the backend. Its sample-case
  preview is illustrative demo data, not a live workload forecast.
- Local mock cases and audit entries are labelled in the dashboard. Admin user
  management is local-only. Sign-in is prototype behavior: the app does not
  verify real accounts or enforce role permissions.
- Module 2 currently has no trained task checkpoint or document-level
  inference provider wired to the pipeline. Classifier integration remains
  blocked until those are supplied and verified.
- The ICD sample list and verifier rules are an academic prototype and do not
  establish clinical coding correctness.

Run the supported project test suite from the project root:

```powershell
python -m pytest -p no:cacheprovider tests/
```

Build the frontend from its directory with `npm run build`.

## Data

This project targets MIMIC-III / MIMIC-IV discharge summaries. You must
complete PhysioNet's CITI training and credentialing before downloading real
data — see `data/README.md`. Until access is granted, use the synthetic
sample note in `data/sample_note.txt` to develop against.

## Status

This repository contains a working academic prototype for ingestion, rule-based
demo candidate generation, verification, and human review. It is not a finished
or clinically validated coding system. The current dashboard workflow and its
known classifier, authentication, and mock-data limitations are described
above.

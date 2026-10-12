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
cd module4_dashboard/backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd module4_dashboard/frontend && npm install && npm run dev
```

## Data

This project targets MIMIC-III / MIMIC-IV discharge summaries. You must
complete PhysioNet's CITI training and credentialing before downloading real
data — see `data/README.md`. Until access is granted, use the synthetic
sample note in `data/sample_note.txt` to develop against.

## Status

This is a **scaffold**, not a finished system: it gives you working,
paper-aligned interfaces and a couple of reference implementations (sliding
window aggregation, focal loss, a first pass at negation-based verification)
so the group can start integrating and iterating immediately rather than
agreeing on file layout in week 1.

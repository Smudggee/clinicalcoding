# Data

This project targets MIMIC-III / MIMIC-IV discharge summaries.

## Getting real data
1. Complete PhysioNet's CITI "Data or Specimens Only Research" training.
2. Apply for credentialed access at https://physionet.org
3. Sign the MIMIC-III/IV Data Use Agreement.
4. Download `NOTEEVENTS.csv` (MIMIC-III) or the discharge notes table (MIMIC-IV)
   and place it under `data/mimic/` (already gitignored -- never commit PHI).

## Until you have access
Use `data/sample_note.txt`, a synthetic (non-real) discharge summary, to
develop and unit-test the pipeline end to end.

# ACCS — Project Instructions

## Project
Automated Clinical Coding Using Transformer-Based Language Models.

The system aims to assist medical coders by predicting ICD-10 codes
from clinical notes, verifying predictions, and allowing human review.

This is a final-year academic prototype, not a clinically validated
autonomous coding system.

## My Role
I am Person 4, responsible for:
- FastAPI backend
- React/TypeScript frontend integration
- Connecting ingestion, classifier, and verifier modules
- Case management
- Human-in-the-loop review
- Audit logging
- Integration testing

Deadline: Two days.

## Existing Architecture
- module1_ingestion/: Text preprocessing and sliding windows.
- module2_classifier/: BioClinicalBERT model, dataset, losses, and training code.
- module3_verification/: ICD verification and negation/history checks.
- module4_dashboard/: FastAPI backend and React frontend.
- evaluation/: Evaluation helpers.
- tests/: Existing unit tests.

Backend files:
- module4_dashboard/backend/app/main.py
- module4_dashboard/backend/app/pipeline_service.py
- module4_dashboard/backend/app/schemas.py

## Known Problems
- The current analysis pipeline uses a hardcoded ICD knowledge base
  and keyword matching rather than calling BioClinicalBERT.
- A trained checkpoint and complete inference interface were not
  found during the initial repository inspection.
- Some frontend functionality falls back to mock data.
- Cases and audit logs use in-memory storage.
- Some review, settings, and dashboard functionality is incomplete.
- Existing tests do not establish that the full application works end to end.

Verify these findings against the current code before acting.

## Priority Order
1. Establish the real classifier availability and interface.
2. Connect the analysis pipeline to the available classifier and verifier.
3. Display actual backend responses in the frontend.
4. Complete confirmation, override, submission, and audit workflows.
5. Add persistent case/audit storage if feasible.
6. Improve error handling and run integration tests.
7. Integrate voice transcription if the teammate's service is ready.
8. Document the final workflow and remaining limitations.

## Development Rules
- Inspect before editing.
- Check Git status before changing files.
- Preserve uncommitted work and teammates' changes.
- Make small, targeted modifications.
- Do not rewrite the project from scratch.
- Do not overwrite working functionality unnecessarily.
- Do not commit, push, reset, or discard changes without permission.
- Run relevant tests after modifications.
- Never invent model checkpoints, predictions, metrics, or datasets.
- Never present keyword-based scores as BioClinicalBERT predictions.
- Clearly distinguish implemented, mocked, incomplete, and blocked features.
- Never silently show fabricated predictions when the backend fails.
- Do not claim that code validity guarantees clinical correctness.

## Learning Requirements
I am learning while implementing this project.

For every significant task:
1. Explain the goal in simple language.
2. Identify the files that need changes.
3. Explain the approach before making substantial changes.
4. Implement the change.
5. Run relevant tests.
6. Explain the important functions and data flow.
7. Tell me how to run and verify the feature myself.

Avoid explaining every trivial line unless I ask.

Use actual function names and files from this repository.
Do not give generic examples when the real implementation can be inspected.

## Definition of Done
- Backend and frontend start successfully.
- Clinical-note analysis works through available real module interfaces.
- The dashboard displays actual predictions and verification results.
- Review actions update case state consistently.
- Case history and audit records can be retrieved.
- Errors are handled without fabricating success.
- Relevant tests pass.
- Setup and demonstration instructions are documented.
- Any unavailable component is explicitly identified.

## Working Style
Maintain a checklist of completed, in-progress, blocked, and pending tasks.

Work autonomously on small, low-risk changes within scope.
Ask before destructive or broad changes.
Prioritize a minimal, reliable, demonstrable implementation over unnecessary refactoring.
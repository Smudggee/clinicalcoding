# Module Interfaces (agree on this before splitting up)

Each module is a black box to the others. As long as everyone implements
these shapes, you can build and test in isolation and integrate at the end.

## 1 → 2: Ingestion → Classifier

```json
{
  "document_id": "string",
  "windows": [
    {
      "window_id": 0,
      "text": "string (≤512 tokens)",
      "start_token_offset": 0,
      "end_token_offset": 512
    }
  ]
}
```

## 2 → 3: Classifier → Verifier

```json
{
  "document_id": "string",
  "predictions": [
    {
      "code": "A41.9",
      "probability": 0.87,
      "window_id": 3,
      "evidence_span": "sepsis, unspecified organism",
      "evidence_start_char": 120,
      "evidence_end_char": 152
    }
  ]
}
```

## 3 → 4: Verifier → Dashboard

```json
{
  "document_id": "string",
  "results": [
    {
      "code": "A41.9",
      "probability": 0.87,
      "verification_status": "accepted | rejected | needs_review",
      "reject_reason": "code not present in current ICD release | supporting evidence is negated | null",
      "evidence_span": "sepsis, unspecified organism"
    }
  ]
}
```

## 4 → Ground truth: Dashboard → Evaluation

```json
{
  "document_id": "string",
  "code": "A41.9",
  "model_decision": "accepted | rejected | needs_review",
  "human_action": "confirmed | overturned | added",
  "review_time_seconds": 14.2
}
```

Everyone's code should read/write these shapes (see `*/schemas.py` for the
Python dataclasses). Changing a shape is a group decision, not a solo one.

"""
Negation / historical-vs-current detection (Section III-B "Why Discharge
Summaries are Hard to Code", Section VIII).

Distinguishes 'diagnosed diabetes mellitus on admission' (active, code it)
from 'no evidence of diabetes' (negated, don't code) and 'history of
diabetes' (historical -- may need a different code or none, depending on
guidelines).

This is a lightweight rule-based baseline (a NegEx-style trigger-word
scanner). Swap in a proper NegEx/ConText implementation for the real system --
this exists so Module 3 can be developed and tested before that dependency
is wired in.
"""
import re

NEGATION_TRIGGERS = [
    "no evidence of", "no signs of", "denies", "negative for", "ruled out",
    "not consistent with", "without evidence of", "no history of",
]

HISTORICAL_TRIGGERS = [
    "history of", "previously diagnosed", "prior diagnosis of", "status post",
    "resolved", "in the past",
]

WINDOW_CHARS = 60  # how far before the evidence span we scan for a trigger


def classify_evidence(full_text: str, evidence_start_char: int) -> str:
    """
    Returns one of: "active", "negated", "historical".
    Looks at the text immediately preceding the evidence span for trigger
    phrases. This is intentionally simple -- do not treat it as clinically
    validated; it's a first-pass filter feeding into 'needs_review' when
    uncertain.
    """
    window_start = max(0, evidence_start_char - WINDOW_CHARS)
    preceding_text = full_text[window_start:evidence_start_char].lower()

    for trigger in NEGATION_TRIGGERS:
        if trigger in preceding_text:
            return "negated"

    for trigger in HISTORICAL_TRIGGERS:
        if trigger in preceding_text:
            return "historical"

    return "active"

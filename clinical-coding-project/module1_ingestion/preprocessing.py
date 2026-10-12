"""
Text normalization for clinical discharge summaries (Section III-B "Why
Discharge Summaries are Hard to Code").

Deliberately conservative: the paper warns that over-cleaning removes
clinically load-bearing signal (negations, time phrases, abbreviations,
section headers). Only fix encoding/whitespace issues here - do NOT strip
medical abbreviations or negation words.
"""
import re


def normalize(raw_text: str) -> str:
    """Normalize whitespace/formatting without touching clinical content."""
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_sections(text: str) -> dict:
    """
    Best-effort split into named sections (e.g. 'HISTORY OF PRESENT ILLNESS',
    'DISCHARGE DIAGNOSIS') using ALL-CAPS headers followed by a colon, the
    common MIMIC discharge-summary convention. Returns
    {section_name: section_text}; falls back to {'FULL_TEXT': text}.
    """
    header_pattern = re.compile(r"^([A-Z][A-Z /]{3,40}):\s*$", re.MULTILINE)
    headers = list(header_pattern.finditer(text))
    if not headers:
        return {"FULL_TEXT": text}

    sections = {}
    for i, match in enumerate(headers):
        name = match.group(1).strip()
        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        sections[name] = text[start:end].strip()
    return sections

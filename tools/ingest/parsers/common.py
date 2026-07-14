from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re


def guess_date_from_text(text: str) -> str:
    if not text:
        return ""
    iso = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if iso:
        return iso.group(1)
    compact = re.search(r"(20\d{2})[-_](\d{2})[-_](\d{2})", text)
    if compact:
        return f"{compact.group(1)}-{compact.group(2)}-{compact.group(3)}"
    return ""


def guess_case_ids(text: str) -> list[str]:
    if not text:
        return []
    patterns = [
        r"\bSPR\d{2}-\d{4}\b",
        r"\bPRS-\d{4,6}\b",
        r"\b[A-Z]+-PRR-\d{3}\b",
        r"\bC\d{2}-\d{4}\b",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return sorted({item.upper() for item in found})


def guess_district_codes(text: str) -> list[str]:
    text_upper = (text or "").upper()
    codes = []
    for code in ["ATTLEBORO", "FALLRIVER", "WHITMANH", "BRIDGEWAT", "NORTON", "DESE"]:
        if code in text_upper:
            codes.append(code)
    return sorted(set(codes))


def base_extract(doc: dict, doc_family: str, doc_type: str) -> dict:
    name = Path(doc.get("originalFileName", "")).name
    text_hint = f"{name} {doc.get('currentPath', '')}"
    return {
        "docId": doc.get("id"),
        "docFamily": doc_family,
        "docType": doc_type,
        "title": name,
        "summary": "",
        "documentDate": guess_date_from_text(text_hint),
        "datePrecision": "day" if guess_date_from_text(text_hint) else "unknown",
        "dateDerivedFrom": "file-name" if guess_date_from_text(text_hint) else "",
        "subjectLine": "",
        "sender": None,
        "recipients": [],
        "cc": [],
        "caseHints": guess_case_ids(text_hint),
        "districtHints": guess_district_codes(text_hint),
        "peopleHints": [],
        "organizationHints": [],
        "requestNumbers": guess_case_ids(text_hint),
        "requestedItems": [],
        "deadlines": [],
        "actionsOrdered": [],
        "determinationOutcome": None,
        "statusSignals": [],
        "citations": [],
        "attachments": [],
        "structuredFields": {},
        "textSpans": [],
        "parseWarnings": [],
        "confidence": 0.5,
        "needsReview": True,
    }


def iso_date_from_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.date().isoformat()


def safe_text_preview(path: Path, limit: int = 4000) -> str:
    try:
        if path.suffix.lower() == ".txt":
            return path.read_text(encoding="utf-8", errors="ignore")[:limit]
        if path.suffix.lower() == ".json":
            return json.dumps(json.loads(path.read_text(encoding="utf-8", errors="ignore")))[:limit]
        if path.suffix.lower() == ".csv":
            return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:  # pragma: no cover - defensive
        return ""
    return ""


def extract_deadlines(text: str) -> list[dict]:
    values = []
    for match in re.finditer(r"(?:due|deadline)[^0-9]{0,20}(20\d{2}-\d{2}-\d{2})", text, flags=re.IGNORECASE):
        values.append(
            {
                "label": "Detected deadline",
                "date": match.group(1),
                "sourceText": match.group(0),
                "datePrecision": "day",
                "appliesTo": "document",
            }
        )
    return values

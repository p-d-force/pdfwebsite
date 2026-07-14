from __future__ import annotations

from pathlib import Path

from .common import base_extract, extract_deadlines, guess_case_ids, guess_district_codes, safe_text_preview


def parse_public_records(doc: dict, path: Path) -> dict:
    extract = base_extract(doc, "public-records", doc.get("docType") or "public-records-document")
    name = Path(path).name
    low = name.lower()
    text = f"{name}\n{safe_text_preview(path)}"
    status_signals = []
    if "appeal" in low:
        status_signals.append("appeal-filed")
    if "request" in low or "prr" in low:
        status_signals.append("request-filed")
    if "response" in low or "production" in low:
        status_signals.append("response-produced")
    extract.update(
        {
            "summary": "Public records parser extracted request/appeal/response hints from filename and text preview.",
            "requestNumbers": guess_case_ids(text),
            "caseHints": sorted(set(extract.get("caseHints", []) + guess_case_ids(text))),
            "districtHints": sorted(set(extract.get("districtHints", []) + guess_district_codes(text))),
            "deadlines": extract_deadlines(text),
            "statusSignals": status_signals,
            "structuredFields": {
                "documentKind": "appeal" if "appeal" in low else "request" if "request" in low or "prr" in low else "response" if "response" in low or "production" in low else "other"
            },
            "confidence": 0.8,
            "needsReview": True,
        }
    )
    return extract

from __future__ import annotations

from pathlib import Path

from .common import base_extract, extract_deadlines, guess_case_ids, guess_district_codes, safe_text_preview


def parse_determination(doc: dict, path: Path) -> dict:
    extract = base_extract(doc, "determination", doc.get("docType") or "formal-determination")
    name = Path(path).name
    low = name.lower()
    text = f"{name}\n{safe_text_preview(path)}"
    outcome = "issued" if "determination" in low else None
    extract.update(
        {
            "summary": "Determination parser extracted formal determination/order hints.",
            "determinationOutcome": outcome,
            "statusSignals": ["determination-issued"] if outcome else [],
            "caseHints": sorted(set(extract.get("caseHints", []) + guess_case_ids(text))),
            "districtHints": sorted(set(extract.get("districtHints", []) + guess_district_codes(text))),
            "deadlines": extract_deadlines(text),
            "actionsOrdered": ["response-ordered"] if "request for local response" in text.lower() else [],
            "confidence": 0.86,
            "needsReview": True,
        }
    )
    return extract

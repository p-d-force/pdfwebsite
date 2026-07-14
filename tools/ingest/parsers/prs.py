from __future__ import annotations

from pathlib import Path

from .common import base_extract, extract_deadlines, guess_case_ids, guess_district_codes, safe_text_preview


def parse_prs(doc: dict, path: Path) -> dict:
    extract = base_extract(doc, "prs", doc.get("docType") or "prs-related-document")
    name = Path(path).name
    low = name.lower()
    text = f"{name}\n{safe_text_preview(path)}"
    actions = []
    if "local_response" in low or "local response" in low:
        actions.append("local-response-requested")
    if "complaint" in low:
        actions.append("complaint-filed")
    extract.update(
        {
            "summary": "PRS parser extracted complaint and local response workflow hints.",
            "actionsOrdered": actions,
            "statusSignals": actions,
            "caseHints": sorted(set(extract.get("caseHints", []) + guess_case_ids(text))),
            "districtHints": sorted(set(extract.get("districtHints", []) + guess_district_codes(text))),
            "deadlines": extract_deadlines(text),
            "confidence": 0.83,
            "needsReview": True,
        }
    )
    return extract

from __future__ import annotations

from pathlib import Path

from .common import base_extract


def parse_attachment(doc: dict, path: Path) -> dict:
    extract = base_extract(doc, doc.get("docFamily") or "attachment", doc.get("docType") or "generic-attachment")
    extract.update(
        {
            "summary": f"Generic attachment placeholder for {Path(path).name}.",
            "confidence": 0.4,
            "needsReview": True,
        }
    )
    return extract

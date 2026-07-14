from __future__ import annotations

from pathlib import Path

from .common import base_extract


def parse_correspondence(doc: dict, path: Path) -> dict:
    extract = base_extract(doc, "correspondence", doc.get("docType") or "general-correspondence")
    extract.update(
        {
            "summary": f"General correspondence document from filename {Path(path).name}.",
            "confidence": 0.63,
            "needsReview": True,
        }
    )
    return extract

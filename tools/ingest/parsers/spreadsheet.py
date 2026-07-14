from __future__ import annotations

from pathlib import Path

import openpyxl

from .common import base_extract


def parse_spreadsheet(doc: dict, path: Path) -> dict:
    extract = base_extract(doc, "spreadsheet", doc.get("docType") or "tabular-attachment")
    sheet_names: list[str] = []
    try:
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheet_names = list(workbook.sheetnames)
        workbook.close()
    except Exception as exc:  # pragma: no cover - defensive
        extract["parseWarnings"].append(str(exc))
    extract.update(
        {
            "summary": "Spreadsheet attachment with workbook metadata only in first implementation.",
            "structuredFields": {"sheetNames": sheet_names, "sheetCount": len(sheet_names)},
            "confidence": 0.88 if sheet_names else 0.5,
            "needsReview": True,
        }
    )
    return extract

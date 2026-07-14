from __future__ import annotations

import json
from pathlib import Path
import re

from ..common import ensure_dir, read_json, write_json
from .common import utc_now


def build_redaction_previews(root: Path) -> dict:
    ingest_dir = root / "data" / "derived" / "ingest"
    jobs_payload = read_json(ingest_dir / "redaction_jobs.json", default={"records": []})
    dashboard = read_json(ingest_dir / "review_dashboard.json", default={})
    doc_rows = {row.get("document", {}).get("id"): row for row in dashboard.get("documents", [])}
    preview_records = []
    output_root = root / "public_redacted"
    ensure_dir(output_root)

    for job in jobs_payload.get("records", []):
        target_id = job.get("targetId")
        row = doc_rows.get(target_id, {})
        document = row.get("document", {})
        extract = row.get("extract", {})
        rel_path = document.get("currentPath", "")
        source_path = root / rel_path if rel_path else None
        source_text = _load_redaction_source_text(source_path, extract)
        preview_text = _apply_redaction_profile(source_text, job.get("profileId", ""))
        preview_rel = _preview_rel_path(rel_path, target_id)
        preview_path = output_root / preview_rel
        ensure_dir(preview_path.parent)
        preview_path.write_text(preview_text, encoding="utf-8")
        preview_records.append(
            {
                "jobId": job.get("id"),
                "targetId": target_id,
                "profileId": job.get("profileId"),
                "reason": job.get("reason"),
                "status": "preview-generated",
                "sourcePath": rel_path,
                "previewPath": str(preview_path.relative_to(root)).replace("\\", "/"),
                "generatedAt": utc_now(),
                "redactionSummary": _redaction_summary(source_text, preview_text),
            }
        )

    write_json(ingest_dir / "redaction_previews.json", {"records": preview_records})
    return {"jobs": len(jobs_payload.get("records", [])), "previews": len(preview_records)}


def _load_redaction_source_text(source_path: Path | None, extract: dict) -> str:
    if source_path and source_path.exists():
        suffix = source_path.suffix.lower()
        try:
            if suffix in {".txt", ".json", ".csv", ".eml"}:
                return source_path.read_text(encoding="utf-8", errors="ignore")[:12000]
        except Exception:  # pragma: no cover
            pass
    return json.dumps(
        {
            "title": extract.get("title"),
            "summary": extract.get("summary"),
            "sender": extract.get("sender"),
            "recipients": extract.get("recipients"),
            "caseHints": extract.get("caseHints"),
            "districtHints": extract.get("districtHints"),
        },
        indent=2,
    )


def _apply_redaction_profile(text: str, profile_id: str) -> str:
    masked = text
    if profile_id in {"redaction-level-2", "redaction-level-3", "redaction-level-4", "redaction-level-5"}:
        masked = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", masked)
        masked = re.sub(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}", "[REDACTED_PHONE]", masked)
    if profile_id in {"redaction-level-3", "redaction-level-4", "redaction-level-5"}:
        masked = re.sub(r"\b\d{2,}[/-]\d{2,}[/-]\d{2,4}\b", "[REDACTED_DATE]", masked)
        masked = re.sub(r"\b\d{6,}\b", "[REDACTED_ID]", masked)
    if profile_id in {"redaction-level-4", "redaction-level-5"}:
        masked = re.sub(r"(?i)student", "[REDACTED_STUDENT_REF]", masked)
    if profile_id == "redaction-level-5":
        masked = re.sub(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", "[REDACTED_NAME]", masked)
    return masked


def _preview_rel_path(rel_path: str, target_id: str) -> Path:
    if rel_path:
        source = Path(rel_path)
        return source.with_suffix(source.suffix + ".redacted.preview.txt")
    safe = target_id.replace(":", "-")
    return Path("unlinked") / f"{safe}.redacted.preview.txt"


def _redaction_summary(original: str, redacted: str) -> dict:
    return {
        "originalLength": len(original),
        "redactedLength": len(redacted),
        "emailTokens": redacted.count("[REDACTED_EMAIL]"),
        "phoneTokens": redacted.count("[REDACTED_PHONE]"),
        "nameTokens": redacted.count("[REDACTED_NAME]"),
        "idTokens": redacted.count("[REDACTED_ID]"),
    }

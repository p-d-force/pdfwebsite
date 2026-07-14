from __future__ import annotations

from pathlib import Path
from typing import Any

from ..common import read_json, write_json


def _notes_path(root: Path, name: str) -> Path:
    return root / "data" / "derived" / "ingest" / name


def build_notes_scaffold(root: Path) -> dict:
    base = root / "data" / "derived" / "ingest"
    notes = read_json(_notes_path(root, "notes.json"), default={"records": []})
    bundles = read_json(_notes_path(root, "note_bundles.json"), default={"records": []})
    templates = read_json(
        _notes_path(root, "note_templates.json"),
        default={
            "records": [
                {"id": "template-red-flag", "title": "Red Flag", "category": "red-flag", "body": "Flag this file or entity and explain why it is concerning."},
                {"id": "template-chronology", "title": "Chronology", "category": "chronology", "body": "Describe where this fits in the timeline and what it changes."},
                {"id": "template-entity-context", "title": "Entity Context", "category": "entity", "body": "Summarize what this reveals about a person, district, school, or investigation."},
            ]
        },
    )
    redaction_profiles = read_json(
        _notes_path(root, "redaction_profiles.json"),
        default={
            "records": [
                {"id": "redaction-level-1", "title": "Level 1 - light", "description": "Minor public cleanup only.", "targets": ["incidental emails", "minor personal references"]},
                {"id": "redaction-level-2", "title": "Level 2 - moderate", "description": "Protect direct personal contact information.", "targets": ["emails", "phones", "street addresses"]},
                {"id": "redaction-level-3", "title": "Level 3 - privacy", "description": "Protect PII and student identifiers.", "targets": ["PII", "student data", "DOBs", "IDs"]},
                {"id": "redaction-level-4", "title": "Level 4 - sensitive", "description": "Protect high-sensitivity narrative and internal notes.", "targets": ["internal strategy", "sensitive medical/disability details"]},
                {"id": "redaction-level-5", "title": "Level 5 - aggressive", "description": "Public-safe anonymized output with strong minimization.", "targets": ["broad identity masking", "aggressive contextual removal"]},
            ]
        },
    )
    redaction_jobs = read_json(_notes_path(root, "redaction_jobs.json"), default={"records": []})
    write_json(_notes_path(root, "notes.json"), notes)
    write_json(_notes_path(root, "note_bundles.json"), bundles)
    write_json(_notes_path(root, "note_templates.json"), templates)
    write_json(_notes_path(root, "redaction_profiles.json"), redaction_profiles)
    write_json(_notes_path(root, "redaction_jobs.json"), redaction_jobs)
    return {
        "notes": len(notes.get("records", [])),
        "bundles": len(bundles.get("records", [])),
        "templates": len(templates.get("records", [])),
        "redactionProfiles": len(redaction_profiles.get("records", [])),
    }


def load_notes(root: Path) -> dict[str, Any]:
    return read_json(_notes_path(root, "notes.json"), default={"records": []})


def save_notes(root: Path, payload: dict[str, Any]) -> None:
    write_json(_notes_path(root, "notes.json"), payload)


def add_note(root: Path, note: dict[str, Any]) -> dict[str, Any]:
    payload = load_notes(root)
    records = payload.get("records", [])
    records.append(note)
    payload["records"] = records
    save_notes(root, payload)
    return note

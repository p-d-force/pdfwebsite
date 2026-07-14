from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .common import read_json, slugify, write_json


def parse_iso_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def collect_case_records(root: Path) -> list[dict]:
    approved_ingest = read_json(root / "data" / "derived" / "ingest" / "approved_events.json", default={}).get("records", [])
    ingest_by_case: dict[str, list[dict]] = {}
    for item in approved_ingest:
        case_id = item.get("caseId")
        if not case_id:
            continue
        ingest_by_case.setdefault(case_id, []).append(item)

    records: list[dict] = []
    case_meta_paths = sorted(root.glob("cases/*/*/metadata.json"))
    for path in case_meta_paths:
        payload = read_json(path, default={})
        case_id = payload.get("caseId")
        district_code = payload.get("district")
        if not case_id or not district_code:
            continue

        timeline = payload.get("timeline") or []
        normalized_timeline = []
        for item in timeline:
            entry_date = item.get("date", "")
            dt = parse_iso_date(entry_date)
            normalized_timeline.append(
                {
                    "entryId": item.get("entryId"),
                    "date": entry_date,
                    "sortDate": dt.isoformat() if dt else "",
                    "type": item.get("type", "Update"),
                    "title": item.get("title", "Update"),
                    "description": item.get("description", ""),
                    "notes": item.get("notes", ""),
                    "documents": item.get("documents", []),
                }
            )

        for item in ingest_by_case.get(case_id, []):
            dt = parse_iso_date(item.get("eventDate", ""))
            normalized_timeline.append(
                {
                    "entryId": item.get("eventId"),
                    "date": item.get("eventDate", ""),
                    "sortDate": dt.isoformat() if dt else "",
                    "type": item.get("eventType", "Update"),
                    "title": item.get("title", "Ingested document event"),
                    "description": item.get("description", ""),
                    "notes": item.get("sourceNote", "Approved from ingest review queue"),
                    "documents": item.get("documents", []),
                    "source": "ingest",
                    "visibility": item.get("visibility", "public"),
                }
            )

        normalized_timeline.sort(key=lambda x: x.get("sortDate") or "")

        records.append(
            {
                "id": slugify(case_id),
                "caseId": case_id,
                "districtCode": district_code,
                "districtName": payload.get("districtName", district_code),
                "location": payload.get("location", ""),
                "type": payload.get("type", "Case"),
                "caseType": payload.get("caseType", "case"),
                "status": payload.get("status", "open"),
                "statusLabel": payload.get("statusLabel", "Open"),
                "statusReason": payload.get("statusReason", ""),
                "currentStage": payload.get("currentStage", "In Progress"),
                "subject": payload.get("subject", ""),
                "filedDate": payload.get("filedDate", ""),
                "nextDeadline": payload.get("nextDeadline", ""),
                "nextDeadlineDescription": payload.get("nextDeadlineDescription", ""),
                "notes": payload.get("notes", ""),
                "recurrenceNotes": payload.get("recurrenceNotes", ""),
                "crossReferences": payload.get("crossReferences", []),
                "requestedItems": payload.get("requestedItems", []),
                "relatedCases": payload.get("relatedCases", []),
                "timeline": normalized_timeline,
                "sourceMetadata": str(path.relative_to(root)).replace("\\", "/"),
            }
        )

    records.sort(key=lambda x: x.get("filedDate") or "")
    return records


def build_timeline_dataset(root: Path) -> dict:
    cases = collect_case_records(root)
    events = []
    for case in cases:
        for entry in case["timeline"]:
            events.append(
                {
                    "id": slugify(f"{case['caseId']}-{entry['entryId']}-{entry['date']}-{entry['title']}"),
                    "caseId": case["caseId"],
                    "districtCode": case["districtCode"],
                    "type": entry["type"],
                    "title": entry["title"],
                    "date": entry["date"],
                    "description": entry["description"],
                    "documents": entry["documents"],
                    "source": entry.get("source", "metadata"),
                    "visibility": entry.get("visibility", "public"),
                }
            )

    events.sort(key=lambda x: x.get("date") or "")
    payload = {"cases": cases, "events": events}
    write_json(root / "data" / "cases_timeline.json", payload)
    return {"caseCount": len(cases), "eventCount": len(events)}

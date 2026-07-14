from __future__ import annotations

from datetime import date
from pathlib import Path

from .common import read_json, slugify, write_json


def infer_severity(text: str) -> str:
    low = text.lower()
    if "overdue" in low or "appeal" in low:
        return "high"
    if "deadline" in low or "determination" in low:
        return "medium"
    return "low"


def build_auto_updates(cases_timeline: dict) -> list[dict]:
    updates = []
    for event in cases_timeline.get("events", []):
        if event.get("visibility", "public") != "public":
            continue
        updates.append(
            {
                "id": slugify(f"auto-{event['caseId']}-{event['date']}-{event['title']}"),
                "date": event.get("date", ""),
                "source": "auto",
                "districtCode": event.get("districtCode", ""),
                "caseId": event.get("caseId", ""),
                "title": event.get("title", "Case update"),
                "summary": event.get("description", ""),
                "severity": infer_severity(f"{event.get('type', '')} {event.get('title', '')}"),
                "documents": event.get("documents", []),
                "eventSource": event.get("source", "metadata"),
            }
        )
    return updates


def build_updates_feed(root: Path) -> dict:
    manual = read_json(root / "data" / "manual_updates.json", default={}).get("updates", [])
    cases_timeline = read_json(root / "data" / "cases_timeline.json", default={})
    auto_updates = build_auto_updates(cases_timeline)

    merged = [*manual, *auto_updates]
    merged.sort(key=lambda x: x.get("date") or "", reverse=True)

    write_json(
        root / "data" / "updates.json",
        {
            "generatedAt": date.today().isoformat(),
            "records": merged,
            "counts": {
                "manual": len(manual),
                "auto": len(auto_updates),
                "total": len(merged),
            },
        },
    )

    return {"totalUpdates": len(merged)}

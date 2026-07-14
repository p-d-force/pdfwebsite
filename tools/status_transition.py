from __future__ import annotations

from datetime import date
from pathlib import Path

from .common import read_json, write_json
from .deadline_businessdays import business_day_status


def parse_iso_day(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def derive_status(case: dict, today: date) -> dict:
    deadline = parse_iso_day(case.get("nextDeadline", ""))
    jurisdiction = case.get("jurisdiction", "US-MA")
    status = case.get("status", "open")
    status_label = case.get("statusLabel", status.title())

    if not deadline:
        return {
            "caseId": case["caseId"],
            "status": status,
            "statusLabel": status_label,
            "deadline": case.get("nextDeadline", ""),
            "deadlineStatus": "none",
            "deadlineLabel": "No active deadline",
            "businessDaysDelta": None,
        }

    due = business_day_status(deadline, today, jurisdiction)
    normalized_status = status
    normalized_label = status_label

    if status != "closed" and due.status == "overdue":
        normalized_status = "overdue"
        normalized_label = "Overdue"
    elif status != "closed" and due.status == "due-today":
        normalized_status = "due"
        normalized_label = "Due Today"

    return {
        "caseId": case["caseId"],
        "status": normalized_status,
        "statusLabel": normalized_label,
        "deadline": deadline.isoformat(),
        "deadlineStatus": due.status,
        "deadlineLabel": due.label,
        "businessDaysDelta": due.business_days_delta,
    }


def apply_status_transitions(root: Path) -> dict:
    timeline = read_json(root / "data" / "cases_timeline.json", default={})
    cases = timeline.get("cases", [])
    today = date.today()

    transitions = [derive_status(case, today) for case in cases]
    transition_map = {row["caseId"]: row for row in transitions}

    for case in cases:
        row = transition_map.get(case["caseId"])
        if not row:
            continue
        case["statusComputed"] = row["status"]
        case["statusLabelComputed"] = row["statusLabel"]
        case["deadlineStatus"] = row["deadlineStatus"]
        case["deadlineLabel"] = row["deadlineLabel"]
        case["businessDaysDelta"] = row["businessDaysDelta"]

    write_json(root / "data" / "case_status.json", {"asOf": today.isoformat(), "records": transitions})
    write_json(root / "data" / "cases_timeline.json", timeline)
    return {"statusCount": len(transitions)}

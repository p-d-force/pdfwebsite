from __future__ import annotations

from typing import Any
from uuid import uuid4

from ..common import read_json, write_json
from .common import ENTITY_ROOT, utc_now
from .notes import add_note


def _task_path(root, task_id: str):
    return root / ENTITY_ROOT / "review_tasks" / f"{task_id.replace(':', '-')}.json"


def load_review_task_by_doc(root, doc_id: str) -> dict | None:
    task_dir = root / ENTITY_ROOT / "review_tasks"
    if not task_dir.exists():
        return None
    for path in sorted(task_dir.glob("*.json")):
        payload = read_json(path, default={})
        if payload.get("docId") == doc_id:
            return payload
    return None


def save_review_task(root, task: dict) -> None:
    write_json(_task_path(root, task["id"]), task)


def append_approval_history(task: dict, action: str, source: str, value: Any = None) -> dict:
    history = list(task.get("approvalHistory", []))
    entry = {"action": action, "at": utc_now(), "source": source}
    if value is not None:
        entry["value"] = value
    history.append(entry)
    task["approvalHistory"] = history
    task["updatedAt"] = entry["at"]
    return task


def set_review_state(root, doc_id: str, state: str, source: str = "local-admin") -> dict:
    task = load_review_task_by_doc(root, doc_id)
    if not task:
        raise ValueError("Review task not found")
    task["generalState"] = state
    if state == "completed":
        task["reviewCompletedAt"] = utc_now()
    append_approval_history(task, f"state:{state}", source)
    save_review_task(root, task)
    return task


def add_manual_link(root, doc_id: str, link_type: str, value: str, source: str = "local-admin") -> dict:
    task = load_review_task_by_doc(root, doc_id)
    if not task:
        raise ValueError("Review task not found")
    key = {
        "case": "manualCaseLinks",
        "district": "manualDistrictLinks",
        "person": "manualPeopleLinks",
        "event": "manualEventLinks",
    }[link_type]
    values = list(task.get(key, []))
    if value not in values:
        values.append(value)
    task[key] = values
    append_approval_history(task, f"link:{link_type}", source, value)
    save_review_task(root, task)
    return task


def set_override_field(root, doc_id: str, field_name: str, value: Any, source: str = "local-admin") -> dict:
    task = load_review_task_by_doc(root, doc_id)
    if not task:
        raise ValueError("Review task not found")
    overrides = dict(task.get("overrideFields", {}))
    overrides[field_name] = value
    task["overrideFields"] = overrides
    meta = dict(task.get("overrideFieldMeta", {}))
    field_meta = dict(meta.get(field_name, {}))
    provenance = list(field_meta.get("fieldProvenance", []))
    provenance.append(
        {
            "sourceUrlOrPath": task.get("docId", ""),
            "sourceEntityId": task.get("docId", ""),
            "sourceText": str(value),
            "method": f"override:{source}",
            "confidence": 1.0,
            "approvalHistory": [{"action": "override", "at": utc_now(), "source": source}],
        }
    )
    history = list(field_meta.get("fieldHistory", []))
    history.append({"at": utc_now(), "value": value, "source": source})
    field_meta["fieldProvenance"] = provenance
    field_meta["fieldHistory"] = history
    field_meta["current"] = value
    meta[field_name] = field_meta
    task["overrideFieldMeta"] = meta
    append_approval_history(task, f"override:{field_name}", source, value)
    save_review_task(root, task)
    return task


def add_note_action(root, target_type: str, target_id: str, category: str, body: str, created_by: str = "local-admin") -> dict:
    note = {
        "id": f"note:{uuid4().hex[:12]}",
        "targetType": target_type,
        "targetId": target_id,
        "category": category,
        "body": body,
        "createdAt": utc_now(),
        "createdBy": created_by,
        "tags": [],
    }
    return add_note(root, note)


def decide_field(root, doc_id: str, field_name: str, value: Any, source_lane: str, decision: str, actor: str = "local-admin") -> dict:
    task = load_review_task_by_doc(root, doc_id)
    if not task:
        raise ValueError("Review task not found")
    accepted = list(task.get("acceptedFields", []))
    rejected = list(task.get("rejectedSuggestions", []))
    entry = {
        "field": field_name,
        "value": value,
        "sourceLane": source_lane,
        "decision": decision,
        "at": utc_now(),
        "actor": actor,
    }
    accepted = [item for item in accepted if not (item.get("field") == field_name and item.get("sourceLane") == source_lane)]
    rejected = [item for item in rejected if not (item.get("field") == field_name and item.get("sourceLane") == source_lane)]
    if decision == "approve":
        accepted.append(entry)
    elif decision == "deny":
        rejected.append(entry)
    else:
        raise ValueError("Decision must be approve or deny")
    task["acceptedFields"] = accepted
    task["rejectedSuggestions"] = rejected
    append_approval_history(task, f"field:{decision}:{field_name}", actor, value)
    save_review_task(root, task)
    return task


def approve_all_fields(root, doc_id: str, fields: list[dict], actor: str = "local-admin") -> dict:
    task = load_review_task_by_doc(root, doc_id)
    if not task:
        raise ValueError("Review task not found")
    accepted = list(task.get("acceptedFields", []))
    existing_keys = {(item.get("field"), item.get("sourceLane")) for item in accepted}
    now = utc_now()
    for field in fields:
        key = (field.get("field"), field.get("sourceLane"))
        if key in existing_keys:
            continue
        accepted.append(
            {
                "field": field.get("field"),
                "value": field.get("value"),
                "sourceLane": field.get("sourceLane"),
                "decision": "approve",
                "at": now,
                "actor": actor,
            }
        )
    task["acceptedFields"] = accepted
    append_approval_history(task, "field:approve-all", actor, len(fields))
    save_review_task(root, task)
    return task

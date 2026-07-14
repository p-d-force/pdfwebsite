from __future__ import annotations

import argparse
from pathlib import Path
from uuid import uuid4

from skills.common import ROOT, read_json, write_json
from skills.ingest.common import utc_now
from skills.ingest.notes import add_note, load_notes
from skills.ingest.orchestrate import run_ingest_pipeline
from skills.ingest.review_actions import add_manual_link as add_manual_link_action, set_override_field as set_override_field_action, set_review_state as set_review_state_action


INGEST_DIR = ROOT / "data" / "derived" / "ingest"
ENTITY_DIR = ROOT / "data" / "entities"


def load_queue() -> list[dict]:
    return read_json(INGEST_DIR / "ingest_queue.json", default={"records": []}).get("records", [])


def load_dashboard() -> dict:
    return read_json(INGEST_DIR / "review_dashboard.json", default={})


def load_review_tasks() -> list[dict]:
    tasks = []
    task_dir = ENTITY_DIR / "review_tasks"
    if not task_dir.exists():
        return tasks
    for path in sorted(task_dir.glob("*.json")):
        tasks.append(read_json(path, default={}))
    return tasks


def save_review_task(task: dict) -> None:
    write_json(ENTITY_DIR / "review_tasks" / f"{task['id'].replace(':', '-')}.json", task)


def find_dashboard_doc(doc_id: str) -> dict | None:
    dashboard = load_dashboard()
    return next((item for item in dashboard.get("documents", []) if item.get("document", {}).get("id") == doc_id), None)


def find_task_by_doc(doc_id: str) -> dict | None:
    for task in load_review_tasks():
        if task.get("docId") == doc_id:
            return task
    return None


def list_queue() -> None:
    for item in load_queue():
        print(f"{item.get('docId')} | {item.get('generalState')} | {item.get('docType')} | {item.get('currentLocation')}")


def show_doc(doc_id: str) -> None:
    dashboard = load_dashboard()
    row = next((item for item in dashboard.get("documents", []) if item.get("document", {}).get("id") == doc_id), None)
    if not row:
        print("Document not found")
        return
    print(f"Doc: {row['document'].get('id')}")
    print(f"Path: {row['document'].get('currentPath')}")
    print(f"Type: {row['document'].get('docType')}")
    print(f"State: {row.get('review', {}).get('generalState')}")
    print(f"Cases: {row.get('extract', {}).get('caseHints', [])}")
    print(f"Districts: {row.get('extract', {}).get('districtHints', [])}")


def update_state(doc_id: str, target: str) -> None:
    set_review_state_action(ROOT, doc_id, target, source="cli")
    run_ingest_pipeline(ROOT)
    print(f"Updated {doc_id} -> {target}")


def add_manual_link(doc_id: str, link_type: str, value: str) -> None:
    add_manual_link_action(ROOT, doc_id, link_type, value, source="cli")
    run_ingest_pipeline(ROOT)
    print(f"Linked {doc_id} -> {link_type}:{value}")


def move_doc_to_completed(doc_id: str) -> None:
    update_state(doc_id, "completed")
    print("Completed as state-only workflow (no file move).")


def show_qa() -> None:
    report = read_json(ROOT / "data" / "qa_report.json", default={})
    print(f"passed={report.get('passed')} failures={report.get('failureCount')}")
    for failure in report.get("failures", []):
        print(f"- {failure}")


def add_note_cmd(target_type: str, target_id: str, category: str, body: str) -> None:
    note = {
        "id": f"note:{uuid4().hex[:12]}",
        "targetType": target_type,
        "targetId": target_id,
        "category": category,
        "body": body,
        "createdAt": utc_now(),
        "createdBy": "cli",
        "tags": [],
    }
    add_note(ROOT, note)
    run_ingest_pipeline(ROOT)
    print(f"Added note {note['id']} -> {target_type}:{target_id}")


def list_notes_cmd(target_id: str = "") -> None:
    records = load_notes(ROOT).get("records", [])
    if target_id:
        records = [record for record in records if record.get("targetId") == target_id]
    for record in records:
        print(f"{record.get('id')} | {record.get('targetType')}:{record.get('targetId')} | {record.get('category')} | {record.get('body')}")


def set_override_cmd(doc_id: str, field_name: str, value: str) -> None:
    set_override_field_action(ROOT, doc_id, field_name, value, source="cli")
    run_ingest_pipeline(ROOT)
    print(f"Override set {doc_id} -> {field_name}={value}")


def create_redaction_job(target_id: str, profile_id: str, reason: str) -> None:
    path = INGEST_DIR / "redaction_jobs.json"
    payload = read_json(path, default={"records": []})
    records = payload.get("records", [])
    job = {
        "id": f"redact:{uuid4().hex[:12]}",
        "targetId": target_id,
        "profileId": profile_id,
        "reason": reason,
        "status": "preview-pending",
        "createdAt": utc_now(),
        "createdBy": "cli",
        "parallelOutputRoot": "public_redacted",
    }
    records.append(job)
    payload["records"] = records
    write_json(path, payload)
    print(f"Created redaction job {job['id']} for {target_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parent Data Force ingest CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("discover")

    queue = sub.add_parser("queue")
    queue_sub = queue.add_subparsers(dest="queue_command", required=True)
    queue_sub.add_parser("list")
    show_parser = queue_sub.add_parser("show")
    show_parser.add_argument("doc_id")

    for name in ["classify", "parse", "approve", "defer", "reopen", "move-completed"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("doc_id")

    link = sub.add_parser("link")
    link_sub = link.add_subparsers(dest="link_command", required=True)
    for item in ["case", "district", "person"]:
        cmd = link_sub.add_parser(item)
        cmd.add_argument("doc_id")
        cmd.add_argument("value")

    sub.add_parser("qa")

    notes = sub.add_parser("notes")
    notes_sub = notes.add_subparsers(dest="notes_command", required=True)
    notes_list = notes_sub.add_parser("list")
    notes_list.add_argument("target_id", nargs="?", default="")
    notes_add = notes_sub.add_parser("add")
    notes_add.add_argument("target_type")
    notes_add.add_argument("target_id")
    notes_add.add_argument("category")
    notes_add.add_argument("body")

    override = sub.add_parser("override")
    override.add_argument("doc_id")
    override.add_argument("field_name")
    override.add_argument("value")

    redact = sub.add_parser("redact")
    redact_sub = redact.add_subparsers(dest="redact_command", required=True)
    redact_add = redact_sub.add_parser("add")
    redact_add.add_argument("target_id")
    redact_add.add_argument("profile_id")
    redact_add.add_argument("reason")

    args = parser.parse_args()
    if args.command == "discover":
        result = run_ingest_pipeline(ROOT)
        print(result)
    elif args.command == "queue" and args.queue_command == "list":
        list_queue()
    elif args.command == "queue" and args.queue_command == "show":
        show_doc(args.doc_id)
    elif args.command in {"classify", "parse"}:
        show_doc(args.doc_id)
    elif args.command == "approve":
        update_state(args.doc_id, "approved")
    elif args.command == "defer":
        update_state(args.doc_id, "deferred")
    elif args.command == "reopen":
        update_state(args.doc_id, "reviewing")
    elif args.command == "move-completed":
        move_doc_to_completed(args.doc_id)
    elif args.command == "link":
        add_manual_link(args.doc_id, args.link_command, args.value)
    elif args.command == "qa":
        show_qa()
    elif args.command == "notes" and args.notes_command == "list":
        list_notes_cmd(args.target_id)
    elif args.command == "notes" and args.notes_command == "add":
        add_note_cmd(args.target_type, args.target_id, args.category, args.body)
    elif args.command == "override":
        set_override_cmd(args.doc_id, args.field_name, args.value)
    elif args.command == "redact" and args.redact_command == "add":
        create_redaction_job(args.target_id, args.profile_id, args.reason)


if __name__ == "__main__":
    main()

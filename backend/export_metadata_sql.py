from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "cases"
OUT_FILE = Path(__file__).resolve().parent / "seed_from_metadata.sql"


def sql_str(value: str | None) -> str:
    if value is None:
        return "NULL"
    escaped = value.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def sql_date(value: str | None) -> str:
    if not value:
        return "NULL"
    try:
        if len(value) == 10:
            datetime.strptime(value, "%Y-%m-%d")
            return sql_str(value)
    except ValueError:
        pass
    return "NULL"


def infer_doc_type(path: str) -> str:
    lower = path.lower()
    if "/appeals/" in lower:
        return "appeal"
    if "/determinations/" in lower:
        return "determination"
    if "/correspondence/" in lower:
        return "correspondence"
    if "/original-request/" in lower:
        return "prr"
    if "/recordings/" in lower:
        return "recording"
    if "/attachments/" in lower:
        return "attachment"
    return "document"


def discover_case_metadata() -> list[dict]:
    cases = []
    for meta_path in sorted(CASES_DIR.glob("*/*/metadata.json")):
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        if "caseId" not in data:
            continue
        cases.append(data)
    return cases


def render_sql(cases: list[dict]) -> str:
    district_map: dict[str, tuple[str, str]] = {}
    for case in cases:
        code = case.get("district") or "UNKNOWN"
        name = case.get("districtName") or code
        location = case.get("location")
        district_map[code] = (name, location)

    lines: list[str] = []
    lines.append("-- Generated from /cases/*/*/metadata.json")
    lines.append("-- Non-deployment local seed for MySQL schema")
    lines.append("")

    lines.append("-- Districts")
    district_values = []
    for code in sorted(district_map):
        name, location = district_map[code]
        district_values.append(
            f"({sql_str(code)}, {sql_str(name)}, {sql_str(location)}, 'active', NULL)"
        )
    lines.append(
        "INSERT INTO districts (district_code, district_name, location, status, notes) VALUES\n  "
        + ",\n  ".join(district_values)
        + "\nON DUPLICATE KEY UPDATE district_name = VALUES(district_name), location = VALUES(location);"
    )
    lines.append("")

    lines.append("-- Cases")
    for case in cases:
        case_code = case.get("caseId", "")
        district_code = case.get("district", "")
        title = case.get("subject") or case_code
        case_type = case.get("type") or "Unknown"
        status = case.get("status") or "open"
        stage = case.get("currentStage")
        subject = case.get("subject")
        filed_date = case.get("filedDate")
        next_deadline = case.get("nextDeadline")
        next_deadline_desc = case.get("nextDeadlineDescription")
        recurrence = case.get("recurrenceNotes")

        lines.append(
            "INSERT INTO cases (case_code, district_id, title, case_type, status, stage, subject, filed_date, next_deadline, next_deadline_description, recurrence_notes)\n"
            "SELECT "
            f"{sql_str(case_code)}, d.id, {sql_str(title)}, {sql_str(case_type)}, {sql_str(status)}, {sql_str(stage)}, {sql_str(subject)}, {sql_date(filed_date)}, {sql_date(next_deadline)}, {sql_str(next_deadline_desc)}, {sql_str(recurrence)}\n"
            f"FROM districts d WHERE d.district_code = {sql_str(district_code)}\n"
            "ON DUPLICATE KEY UPDATE\n"
            "  title = VALUES(title),\n"
            "  case_type = VALUES(case_type),\n"
            "  status = VALUES(status),\n"
            "  stage = VALUES(stage),\n"
            "  subject = VALUES(subject),\n"
            "  filed_date = VALUES(filed_date),\n"
            "  next_deadline = VALUES(next_deadline),\n"
            "  next_deadline_description = VALUES(next_deadline_description),\n"
            "  recurrence_notes = VALUES(recurrence_notes);"
        )
    lines.append("")

    lines.append("-- Events")
    for case in cases:
        case_code = case.get("caseId", "")
        timeline = case.get("timeline", [])
        for idx, event in enumerate(timeline, start=1):
            lines.append(
                "INSERT INTO case_events (case_id, event_date, event_type, title, description, status, sort_order)\n"
                "SELECT c.id, "
                f"{sql_date(event.get('date'))}, {sql_str(event.get('type') or 'Event')}, {sql_str(event.get('title') or f'Event {idx}')}, {sql_str(event.get('description'))}, {sql_str(event.get('status'))}, {idx}\n"
                f"FROM cases c WHERE c.case_code = {sql_str(case_code)};"
            )
    lines.append("")

    lines.append("-- Timeline documents")
    for case in cases:
        case_code = case.get("caseId", "")
        timeline = case.get("timeline", [])
        for idx, event in enumerate(timeline, start=1):
            docs = event.get("documents", [])
            for doc_path in docs:
                if not isinstance(doc_path, str):
                    continue
                ext = Path(doc_path).suffix.lower().lstrip(".")
                lines.append(
                    "INSERT INTO documents (case_id, case_event_id, doc_type, title, relative_path, file_ext, document_date, date_estimated)\n"
                    "SELECT c.id, e.id, "
                    f"{sql_str(infer_doc_type(doc_path))}, {sql_str(Path(doc_path).name)}, {sql_str(doc_path)}, {sql_str(ext or None)}, {sql_date(event.get('date'))}, 0\n"
                    "FROM cases c\n"
                    "JOIN case_events e ON e.case_id = c.id\n"
                    f"WHERE c.case_code = {sql_str(case_code)} AND e.sort_order = {idx}\n"
                    f"  AND e.title = {sql_str(event.get('title') or f'Event {idx}')};"
                )
    lines.append("")

    lines.append("-- Related case links")
    for case in cases:
        case_code = case.get("caseId", "")
        for related in case.get("relatedCases", []):
            if not related:
                continue
            lines.append(
                "INSERT IGNORE INTO case_links (from_case_id, to_case_id, link_type, notes)\n"
                "SELECT src.id, dst.id, 'related', NULL\n"
                "FROM cases src\n"
                "JOIN cases dst\n"
                f"  ON src.case_code = {sql_str(case_code)} AND dst.case_code = {sql_str(str(related))};"
            )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    cases = discover_case_metadata()
    sql = render_sql(cases)
    OUT_FILE.write_text(sql, encoding="utf-8")
    print(f"Exported {len(cases)} cases to {OUT_FILE}")


if __name__ == "__main__":
    main()

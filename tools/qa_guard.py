from __future__ import annotations

from pathlib import Path

from .common import read_json, write_json


REQUIRED_DATASETS = (
    "data/cases_timeline.json",
    "data/case_status.json",
    "data/updates.json",
    "data/calendar.json",
    "data/meeting_scrape_report.json",
    "data/speeches_fetch_report.json",
    "data/restraint_district_rollup.json",
    "data/restraint_explorer.json",
    "data/derived/ingest/ingest_queue.json",
    "data/derived/ingest/review_dashboard.json",
    "data/derived/ingest/study_email_report.json",
    "data/derived/ingest/attachment_documents.json",
    "data/derived/ingest/study_threads.json",
    "data/derived/ingest/study_combined_events.json",
    "data/derived/ingest/study_timeline_candidates.json",
    "data/derived/ingest/study_participant_graph.json",
    "data/derived/ingest/study_entity_candidates.json",
    "data/derived/ingest/rule_sets.json",
    "data/derived/ingest/rule_matches.json",
    "data/derived/ingest/notes.json",
    "data/derived/ingest/note_templates.json",
    "data/derived/ingest/redaction_profiles.json",
    "data/derived/ingest/redaction_previews.json",
    "data/derived/dese_enrichment/targets.json",
    "data/derived/dese_enrichment/parsed_profiles.json",
    "public/data/site_stats.json",
    "data/site_stats.json",
)

REQUIRED_PUBLIC = (
    "public/index.html",
    "public/sitemap.xml",
    "public/robots.txt",
    "public/calendar/index.html",
    "public/restraint-seclusion/index.html",
    "public/admin-ingest/index.html",
    "public/admin-ingest/queue/index.html",
    "public/admin-ingest/cases/index.html",
    "public/admin-ingest/review/index.html",
    "public/admin-ingest/study/index.html",
    "public/admin-ingest/notes/index.html",
    "public/admin-ingest/redaction/index.html",
    "public/admin-ingest/dese/index.html",
    "public/districts/index.html",
    "public/cases/index.html",
)


def run_qa_guard(root: Path) -> dict:
    checks = []
    failures = []

    for rel in REQUIRED_DATASETS:
        path = root / rel
        ok = path.exists()
        checks.append({"target": rel, "ok": ok})
        if not ok:
            failures.append(rel)

    for rel in REQUIRED_PUBLIC:
        path = root / rel
        ok = path.exists()
        checks.append({"target": rel, "ok": ok})
        if not ok:
            failures.append(rel)

    case_count = len(read_json(root / "data" / "cases_timeline.json", default={}).get("cases", []))
    if case_count == 0:
        failures.append("data/cases_timeline.json empty")
        checks.append({"target": "case_count>0", "ok": False})
    else:
        checks.append({"target": "case_count>0", "ok": True})

    result = {
        "passed": not failures,
        "failureCount": len(failures),
        "failures": failures,
        "checks": checks,
    }
    write_json(root / "data" / "qa_report.json", result)
    return result

from __future__ import annotations

from datetime import date
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

import requests

from skills.common import ROOT, ensure_dir, read_json, slugify, write_json
from skills.dese_enrichment import run_dese_enrichment_scaffold
from skills.evidence_to_timeline import build_timeline_dataset
from skills.ingest.orchestrate import run_ingest_pipeline
from skills.ingest.notes import build_notes_scaffold
from skills.ingest.redaction import build_redaction_previews
from skills.meeting_scrape import extract_meetings_for_district_detailed
from skills.permalink_build import build_permalink_site
from skills.qa_guard import run_qa_guard
from skills.restraint_analytics import run_restraint_pipeline
from skills.status_transition import apply_status_transitions
from skills.updates_hybrid import build_updates_feed


DEFAULT_SITE_CONFIG = {
    "domain": "parentdataforce.com",
    "timezone": "America/New_York",
    "defaultJurisdiction": "US-MA",
}

DEFAULT_DISTRICT_SOURCES = {
    "districts": [
        {
            "districtCode": "ATTLEBORO",
            "districtName": "Attleboro Public Schools",
            "timezone": "America/New_York",
            "jurisdiction": "US-MA",
            "meetingSources": [
                "https://www.attleboroschools.com/o/sc",
                "https://www.attleboroschools.com/page/school-committee-documents",
            ],
        },
        {
            "districtCode": "FALLRIVER",
            "districtName": "Fall River Public Schools",
            "timezone": "America/New_York",
            "jurisdiction": "US-MA",
            "meetingSources": [
                "https://www.fallriverschools.org/page/school-committee-locations-and-agendas",
            ],
        },
        {
            "districtCode": "WHITMANH",
            "districtName": "Whitman-Hanson Regional School District",
            "timezone": "America/New_York",
            "jurisdiction": "US-MA",
            "meetingSources": [
                "https://www.whrsd.org/district/school_committee",
            ],
        },
        {
            "districtCode": "BRIDGEWAT",
            "districtName": "Bridgewater-Raynham Regional School District",
            "timezone": "America/New_York",
            "jurisdiction": "US-MA",
            "meetingSources": [
                "https://www.brrsd.org/committees/school-committee",
            ],
        },
        {
            "districtCode": "NORTON",
            "districtName": "Norton Public Schools",
            "timezone": "America/New_York",
            "jurisdiction": "US-MA",
            "meetingSources": [
                "https://www.norton.k12.ma.us/school-committee",
            ],
        },
    ]
}

DEFAULT_MANUAL_EVENTS = {
    "events": [
        {
            "id": "manual-governance-review",
            "title": "Governance packet review window",
            "type": "deadline",
            "districtCode": "DESE",
            "jurisdiction": "US-MA",
            "date": "2026-04-01",
            "source": {"method": "manual", "note": "Seeded manual calendar placeholder"},
        }
    ]
}

DEFAULT_MANUAL_UPDATES = {
    "updates": [
        {
            "id": "manual-restraint-pipeline-online",
            "date": "2026-03-20",
            "source": "manual",
            "districtCode": "DESE",
            "caseId": "SYSTEM",
            "title": "Restraint analytics pipeline activated",
            "summary": "Initial DESE restraint ingestion and rollup datasets are now generated from intake workbooks.",
            "severity": "medium",
            "documents": [],
        }
    ]
}

DEFAULT_GOALS = {
    "goals": [
        {
            "id": "goal-prr-response-compliance",
            "title": "Improve PRR response compliance tracking",
            "status": "active",
            "targetDate": "2026-06-30",
        },
        {
            "id": "goal-restraint-public-reporting",
            "title": "Publish restraint district and school profile pages",
            "status": "active",
            "targetDate": "2026-05-31",
        },
    ]
}

DEFAULT_SPEECH_SOURCES = {
    "sources": [
        {
            "id": "pdforce-youtube-rss",
            "type": "youtube-rss",
            "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCFG50jRRfBXG45zLsy9logQ",
            "channel": "@pdforce",
        }
    ]
}


def ensure_seed_files(root: Path) -> None:
    ensure_dir(root / "config")
    ensure_dir(root / "data")
    ensure_dir(root / "intake" / "completed")
    for case_root in root.glob("cases/*/*"):
        if not case_root.is_dir():
            continue
        ensure_dir(case_root / "intake")
        ensure_dir(case_root / "completed")

    defaults = {
        root / "config" / "site.json": DEFAULT_SITE_CONFIG,
        root / "config" / "district_sources.json": DEFAULT_DISTRICT_SOURCES,
        root / "data" / "manual_events.json": DEFAULT_MANUAL_EVENTS,
        root / "data" / "manual_updates.json": DEFAULT_MANUAL_UPDATES,
        root / "data" / "goals.json": DEFAULT_GOALS,
        root / "data" / "speeches_sources.json": DEFAULT_SPEECH_SOURCES,
    }
    for path, payload in defaults.items():
        if not path.exists():
            write_json(path, payload)


def build_meetings(root: Path) -> dict:
    district_source = read_json(root / "config" / "district_sources.json", default={})
    districts = district_source.get("districts", [])
    events = []
    review_candidates = []
    diagnostics = []
    manual_queue = []

    for district in districts:
        district_code = district.get("districtCode", "")
        source_urls = district.get("meetingSources", [])
        timezone = district.get("timezone", "America/New_York")
        if not district_code or not source_urls:
            continue

        result = extract_meetings_for_district_detailed(
            district_code=district_code,
            source_urls=source_urls,
            timezone=timezone,
        )
        scraped = result.get("events", [])
        review = result.get("review", [])
        diagnostic = result.get("diagnostics", {})

        review_candidates.extend(review)
        diagnostics.append(diagnostic)

        if not scraped:
            manual_queue.append(
                {
                    "districtCode": district_code,
                    "reason": "No upcoming meetings extracted with confidence threshold.",
                    "sources": source_urls,
                    "diagnostic": diagnostic,
                }
            )
        events.extend(scraped)

    events.sort(key=lambda x: x.get("startAt", ""))
    review_candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    write_json(root / "data" / "meetings.json", {"events": events})
    write_json(root / "data" / "meeting_manual_queue.json", {"records": manual_queue})
    write_json(root / "data" / "meeting_review_candidates.json", {"records": review_candidates})
    write_json(
        root / "data" / "meeting_scrape_report.json",
        {
            "generatedAt": date.today().isoformat(),
            "districts": diagnostics,
            "totals": {
                "districtCount": len(diagnostics),
                "meetingCount": len(events),
                "reviewCount": len(review_candidates),
                "manualQueueCount": len(manual_queue),
            },
        },
    )
    return {
        "meetingCount": len(events),
        "manualQueueCount": len(manual_queue),
        "reviewCount": len(review_candidates),
    }


def fetch_speeches(root: Path) -> dict:
    source_data = read_json(root / "data" / "speeches_sources.json", default={})
    cache_path = root / "data" / "speeches_cache.json"
    records: list[dict] = []
    reports = []

    def iter_entries(xml_root: ET.Element) -> list[ET.Element]:
        return [node for node in xml_root.iter() if isinstance(node.tag, str) and node.tag.endswith("entry")]

    def first_text(entry: ET.Element, suffixes: tuple[str, ...]) -> str:
        for node in entry.iter():
            if not isinstance(node.tag, str):
                continue
            if any(node.tag.endswith(suffix) for suffix in suffixes):
                value = (node.text or "").strip()
                if value:
                    return value
        return ""

    def parse_entries(xml_text: str, source_id: str) -> list[dict]:
        root_xml = ET.fromstring(xml_text)
        parsed = []
        for entry in iter_entries(root_xml):
            video_id = first_text(entry, ("videoId",))
            title = first_text(entry, ("title",))
            published_at = first_text(entry, ("published", "updated"))
            url = ""
            for link in [n for n in entry.iter() if isinstance(n.tag, str) and n.tag.endswith("link")]:
                href = (link.attrib.get("href") or "").strip()
                rel = (link.attrib.get("rel") or "alternate").strip()
                if href and rel in {"alternate", ""}:
                    url = href
                    break
            if not url and video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"

            if not (video_id or url):
                continue
            parsed.append(
                {
                    "id": slugify(video_id or url),
                    "videoId": video_id,
                    "title": title or "Untitled speech",
                    "publishedAt": published_at,
                    "url": url,
                    "sourceId": source_id,
                }
            )
        return parsed

    def extract_channel_id(page_text: str) -> str:
        match = re.search(r'"channelId"\s*:\s*"(UC[0-9A-Za-z_-]{20,})"', page_text)
        return match.group(1) if match else ""

    session = requests.Session()
    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/xml,text/xml,text/html;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
    }

    for source in source_data.get("sources", []):
        if source.get("type") != "youtube-rss":
            continue
        source_id = source.get("id", "unknown")
        channel_handle = source.get("channel", "")
        configured_url = source.get("url")
        if not configured_url:
            continue

        attempt_urls = [configured_url]
        if channel_handle.startswith("@"):
            attempt_urls.append(f"https://www.youtube.com/feeds/videos.xml?user={channel_handle[1:]}")
            attempt_urls.append(f"https://www.youtube.com/{channel_handle}/videos")

        source_report = {
            "sourceId": source_id,
            "type": source.get("type"),
            "url": configured_url,
            "status": "skipped",
            "httpStatus": None,
            "entries": 0,
            "error": "",
            "attempts": [],
        }

        source_entries: list[dict] = []
        last_error = ""
        for attempt_url in attempt_urls:
            try:
                response = session.get(attempt_url, timeout=30, headers=request_headers)
                source_report["attempts"].append({"url": attempt_url, "httpStatus": response.status_code})
                source_report["httpStatus"] = response.status_code
                response.raise_for_status()

                if attempt_url.endswith("/videos"):
                    channel_id = extract_channel_id(response.text)
                    if channel_id:
                        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                        response = session.get(rss_url, timeout=30, headers=request_headers)
                        source_report["attempts"].append({"url": rss_url, "httpStatus": response.status_code})
                        source_report["httpStatus"] = response.status_code
                        response.raise_for_status()

                source_entries = parse_entries(response.text, source_id)
                if source_entries:
                    break
            except requests.RequestException as exc:
                last_error = str(exc)
            except ET.ParseError as exc:
                last_error = str(exc)

        source_report["entries"] = len(source_entries)
        if source_entries:
            source_report["status"] = "ok"
            records.extend(source_entries)
        else:
            source_report["status"] = "fetch-error" if last_error else "empty"
            source_report["error"] = last_error
        reports.append(source_report)

    deduped: dict[str, dict] = {}
    for row in records:
        key = row.get("videoId") or row.get("url")
        if not key:
            continue
        existing = deduped.get(key)
        if not existing or (row.get("publishedAt", "") > existing.get("publishedAt", "")):
            deduped[key] = row

    final_records = list(deduped.values())
    used_cache = False

    if final_records:
        final_records.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
        write_json(
            cache_path,
            {
                "generatedAt": date.today().isoformat(),
                "records": final_records,
            },
        )
    else:
        cached = read_json(cache_path, default={})
        final_records = cached.get("records", [])
        final_records.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
        used_cache = bool(final_records)

    write_json(
        root / "data" / "speeches.json",
        {
            "generatedAt": date.today().isoformat(),
            "fromCache": used_cache,
            "records": final_records,
        },
    )
    write_json(
        root / "data" / "speeches_fetch_report.json",
        {
            "generatedAt": date.today().isoformat(),
            "usedCache": used_cache,
            "recordCount": len(final_records),
            "sources": reports,
        },
    )
    return {"speechCount": len(final_records), "usedCache": used_cache}


def build_calendar(root: Path) -> dict:
    meetings = read_json(root / "data" / "meetings.json", default={}).get("events", [])
    manual_events = read_json(root / "data" / "manual_events.json", default={}).get("events", [])
    cases = read_json(root / "data" / "cases_timeline.json", default={}).get("cases", [])
    statuses = read_json(root / "data" / "case_status.json", default={}).get("records", [])
    status_map = {row.get("caseId"): row for row in statuses}

    deadline_events = []
    for case in cases:
        due = case.get("nextDeadline")
        if not due:
            continue
        state = status_map.get(case.get("caseId"), {})
        deadline_events.append(
            {
                "id": slugify(f"deadline-{case.get('caseId')}-{due}"),
                "title": f"{case.get('caseId')} deadline",
                "type": "deadline",
                "districtCode": case.get("districtCode"),
                "jurisdiction": "US-MA",
                "date": due,
                "caseId": case.get("caseId"),
                "status": state.get("deadlineStatus", "upcoming"),
                "label": state.get("deadlineLabel", ""),
                "source": {"method": "derived"},
            }
        )

    merged = [*meetings, *deadline_events, *manual_events]
    merged.sort(key=lambda x: x.get("startAt") or x.get("date") or "")
    write_json(root / "data" / "calendar.json", {"events": merged})
    return {"calendarCount": len(merged), "deadlineCount": len(deadline_events)}


def sync_public_assets(root: Path) -> dict:
    public_dir = root / "public"
    ensure_dir(public_dir)

    static_files = ("index.html", "styles.css", "script.js", "logo.png")
    copied_static = 0
    for rel in static_files:
        src = root / rel
        dst = public_dir / rel
        if not src.exists():
            continue
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        copied_static += 1

    src_data = root / "data"
    dst_data = public_dir / "data"
    if dst_data.exists():
        shutil.rmtree(dst_data)
    if src_data.exists():
        shutil.copytree(src_data, dst_data)

    src_cases = root / "cases"
    dst_cases = public_dir / "cases"
    ensure_dir(dst_cases)
    copied_case_files = 0
    if src_cases.exists():
        for source in src_cases.rglob("*"):
            if not source.is_file():
                continue
            if source.suffix.lower() == ".html":
                continue
            rel = source.relative_to(src_cases)
            target = dst_cases / rel
            ensure_dir(target.parent)
            shutil.copy2(source, target)
            copied_case_files += 1

    return {
        "publicDir": str(public_dir.relative_to(root)).replace("\\", "/"),
        "staticFilesCopied": copied_static,
        "caseArtifactsCopied": copied_case_files,
        "dataSynced": src_data.exists(),
    }


def write_redirect_html(path: Path, target: str) -> None:
    ensure_dir(path.parent)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="0; url={target}">
  <title>Redirecting...</title>
</head>
<body>
  <p>Redirecting to <a href="{target}">{target}</a></p>
  <script>window.location.replace({target!r});</script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def create_root_redirect_stubs(root: Path) -> dict:
    route_dirs = (
        "calendar",
        "districts",
        "goals",
        "prs",
        "public-records",
        "restraint-seclusion",
        "speeches",
        "updates",
    )

    written = 0
    for route in route_dirs:
        write_redirect_html(root / route / "index.html", f"/public/{route}/")
        written += 1

    write_redirect_html(root / "cases" / "index.html", "/public/cases/")
    written += 1

    cases = read_json(root / "data" / "cases_timeline.json", default={}).get("cases", [])
    case_slugs = sorted({slugify(case.get("caseId", "")) for case in cases if case.get("caseId")})
    for slug in case_slugs:
        write_redirect_html(root / "cases" / slug / "index.html", f"/public/cases/{slug}/")
        written += 1

    return {"redirectPages": written, "caseRedirects": len(case_slugs)}


def run() -> None:
    root = ROOT
    ensure_seed_files(root)

    results = {
        "ingest": run_ingest_pipeline(root),
        "notes": build_notes_scaffold(root),
        "redaction": build_redaction_previews(root),
        "dese_enrichment": run_dese_enrichment_scaffold(root),
        "restraint": run_restraint_pipeline(root),
        "timeline": build_timeline_dataset(root),
        "status": apply_status_transitions(root),
        "meetings": build_meetings(root),
        "speeches": fetch_speeches(root),
    }
    results["updates"] = build_updates_feed(root)
    results["calendar"] = build_calendar(root)
    results["permalinks"] = build_permalink_site(root)
    results["publish"] = sync_public_assets(root)
    results["redirects"] = create_root_redirect_stubs(root)
    results["qa"] = run_qa_guard(root)

    write_json(
        root / "data" / "build_manifest.json",
        {
            "generatedAt": date.today().isoformat(),
            "results": results,
        },
    )


if __name__ == "__main__":
    run()

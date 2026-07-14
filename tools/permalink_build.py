from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import shutil

from .common import ensure_dir, read_json, slugify, write_json


def esc(value: object) -> str:
    text = str(value or "")
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def fmt_num(value: object, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    try:
        num = float(str(value))
    except (TypeError, ValueError):
        return esc(value)
    rendered = f"{num:.{digits}f}"
    if digits == 0:
        return rendered
    return rendered.rstrip("0").rstrip(".")


def fmt_delta(value: object, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    try:
        num = float(str(value))
    except (TypeError, ValueError):
        return esc(value)
    sign = "+" if num > 0 else ""
    return f"{sign}{fmt_num(num, digits)}"


def fmt_pct(value: object, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    try:
        num = float(str(value))
    except (TypeError, ValueError):
        return esc(value)
    return f"{fmt_num(num * 100.0, digits)}%"


def fmt_rank(rank: object, total: object) -> str:
    if rank is None or total in (None, 0):
        return "n/a"
    rank_text = fmt_num(rank, 0)
    total_text = fmt_num(total, 0)
    if "n/a" in {rank_text, total_text}:
        return "n/a"
    return f"{rank_text} / {total_text}"


def relative_prefix(page_path: Path, site_root: Path) -> str:
    rel = page_path.parent.relative_to(site_root)
    depth = len(rel.parts)
    return "" if depth == 0 else "../" * depth


def district_slug_map(cases: list[dict]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for case in cases:
        code = case.get("districtCode", "")
        name = case.get("districtName", code)
        if code and code not in mapping:
            mapping[code] = slugify(name)
    return mapping


def shell_nav(prefix: str, active: str) -> str:
    links = [
        ("districts/", "Districts", "districts"),
        ("cases/", "Cases", "cases"),
        ("calendar/", "Calendar", "calendar"),
        ("restraint-seclusion/", "Restraint", "restraint"),
        ("updates/", "Updates", "updates"),
        ("speeches/", "Speeches", "speeches"),
    ]
    nav_items = "".join(
        f'<li><a href="{prefix}{href}" class="nav-link{" active" if key == active else ""}">{label}</a></li>'
        for href, label, key in links
    )
    return f"""
<nav class="nav" id="nav">
  <div class="nav-container">
    <a href="{prefix}index.html" class="nav-logo">
      <img src="{prefix}logo.png" alt="Parent Data Force Logo" class="nav-logo-img">
      <span class="nav-logo-text">PARENT DATA FORCE</span>
    </a>
    <button class="nav-toggle" id="navToggle" aria-label="Toggle navigation">
      <span class="hamburger"></span>
    </button>
    <ul class="nav-menu" id="navMenu">
      {nav_items}
      <li><a href="{prefix}index.html#about" class="nav-link">About</a></li>
      <li><a href="{prefix}index.html#contact" class="nav-link">Contact</a></li>
    </ul>
  </div>
</nav>
"""


def shell_footer(prefix: str) -> str:
    return f"""
<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="{prefix}index.html" class="footer-logo">
          <img src="{prefix}logo.png" alt="Parent Data Force Logo" class="footer-logo-img">
          <span class="footer-logo-text">PARENT DATA FORCE</span>
        </a>
        <p class="footer-tagline">MAKING DATA MAKE SENSE</p>
        <p class="footer-description">Independent advocacy for families navigating special education and public accountability systems.</p>
      </div>
      <div class="footer-nav">
        <h4 class="footer-nav-title">Pages</h4>
        <ul class="footer-nav-list">
          <li><a href="{prefix}districts/">Districts</a></li>
          <li><a href="{prefix}cases/">Cases</a></li>
          <li><a href="{prefix}calendar/">Calendar</a></li>
          <li><a href="{prefix}restraint-seclusion/">Restraint &amp; Seclusion</a></li>
          <li><a href="{prefix}updates/">Updates</a></li>
          <li><a href="{prefix}speeches/">Speeches</a></li>
        </ul>
      </div>
      <div class="footer-nav">
        <h4 class="footer-nav-title">Records</h4>
        <ul class="footer-nav-list">
          <li><a href="{prefix}public-records/">Public Records</a></li>
          <li><a href="{prefix}prs/">PRS Cases</a></li>
          <li><a href="{prefix}goals/">Goals</a></li>
          <li><a href="{prefix}index.html#submit-tip">Submit a Tip</a></li>
        </ul>
      </div>
      <div class="footer-contact">
        <h4 class="footer-nav-title">Contact</h4>
        <div class="footer-contact-info">
          <a href="mailto:contact@parentdataforce.org">contact@parentdataforce.org</a>
          <a href="tel:+13392136110">(339) 213-6110</a>
        </div>
      </div>
    </div>
  </div>
</footer>
"""


def write_page(path: Path, title: str, content: str, site_root: Path, active: str) -> None:
    ensure_dir(path.parent)
    prefix = relative_prefix(path, site_root)
    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>{esc(title)}</title>
  <link rel=\"stylesheet\" href=\"{prefix}styles.css\">
</head>
<body>
  {shell_nav(prefix, active)}
  {content}
  {shell_footer(prefix)}
  <script src=\"{prefix}script.js\"></script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def section_header(tag: str, title: str, subtitle: str) -> str:
    return f"""
<div class="section-header" data-animate>
  <span class="section-tag">{esc(tag)}</span>
  <h2 class="section-title">{esc(title)}</h2>
  <p class="section-subtitle">{esc(subtitle)}</p>
</div>
"""


def status_badge(text: object) -> str:
    low = str(text or "").lower()
    status = "pending"
    if "open" in low or "due" in low:
        status = "open"
    if "overdue" in low:
        status = "overdue"
    if "closed" in low:
        status = "closed"
    return f'<span class="status-badge status-{status}">{esc(text or "Pending")}</span>'


def metric_meta_items(label: str, metric: dict) -> str:
    return f"""
<div class="case-card" data-animate>
  <div class="case-card-header">
    <span class="case-district">{esc(label)}</span>
  </div>
  <h3 class="case-card-title">Per 100 Rate Range</h3>
  <div class="case-card-meta">
    <div class="meta-item"><span class="meta-label">Min</span><span class="meta-value">{fmt_num(metric.get('min'))}</span></div>
    <div class="meta-item"><span class="meta-label">Mid</span><span class="meta-value">{fmt_num(metric.get('mid'))}</span></div>
    <div class="meta-item"><span class="meta-label">Max</span><span class="meta-value">{fmt_num(metric.get('max'))}</span></div>
  </div>
</div>
"""


def build_district_pages(
    site_dir: Path,
    cases: list[dict],
    restraint_rollup: dict,
    calendar_events: list[dict],
    updates: list[dict],
    slug_map: dict[str, str],
) -> list[str]:
    district_map: dict[str, dict] = {}
    for case in cases:
        code = case.get("districtCode", "")
        if not code:
            continue
        district_map.setdefault(code, {"districtCode": code, "districtName": case.get("districtName", code), "cases": []})
        district_map[code]["cases"].append(case)

    urls = []
    cards = []
    for district in district_map.values():
        code = district["districtCode"]
        slug = slug_map.get(code, slugify(district["districtName"]))
        page_path = site_dir / "districts" / slug / "index.html"

        district_cases = sorted(district["cases"], key=lambda x: x.get("nextDeadline") or "")
        open_count = len([c for c in district_cases if c.get("status") != "closed"])
        rollup = restraint_rollup.get(code, {})
        incidents = rollup.get("incidentsPer100", {}) if rollup else {}

        case_cards = "".join(
            f"""
<article class="case-card" data-animate>
  <div class="case-card-header">
    <span class="case-district">{esc(c.get('type', 'Case'))}</span>
    {status_badge(c.get('statusLabelComputed') or c.get('statusLabel') or c.get('status'))}
  </div>
  <div class="case-card-id">{esc(c.get('caseId'))}</div>
  <h3 class="case-card-title">{esc(c.get('subject') or c.get('caseId'))}</h3>
  <p class="case-card-summary">{esc(c.get('nextDeadlineDescription') or 'No deadline detail provided.')}</p>
  <div class="case-card-meta">
    <div class="meta-item"><span class="meta-label">Deadline</span><span class="meta-value">{esc(c.get('nextDeadline') or 'None')}</span></div>
    <div class="meta-item"><span class="meta-label">Status</span><span class="meta-value">{esc(c.get('deadlineLabel') or 'In progress')}</span></div>
  </div>
  <a class="resource-link" href="../../cases/{slugify(c['caseId'])}/">Open Case Page</a>
</article>
"""
            for c in district_cases
        )

        meeting_cards = "".join(
            f"""
<article class="resource-card" data-animate>
  <div class="resource-category">{esc(e.get('type', 'meeting')).upper()}</div>
  <h3 class="resource-title">{esc(e.get('title'))}</h3>
  <p class="resource-excerpt">{esc(e.get('startAt') or e.get('date'))}</p>
  <a class="resource-link" href="{esc(e.get('source', {}).get('url') or '#')}">Source Link</a>
</article>
"""
            for e in calendar_events
            if e.get("districtCode") == code and e.get("type") == "meeting"
        )

        update_cards = "".join(
            f"""
<article class="resource-card" data-animate>
  <div class="resource-category">{esc(u.get('severity', 'info')).upper()}</div>
  <h3 class="resource-title">{esc(u.get('title'))}</h3>
  <p class="resource-excerpt">{esc(u.get('summary') or '')}</p>
  <span class="resource-read-time">{esc(u.get('date'))}</span>
</article>
"""
            for u in updates
            if u.get("districtCode") == code
        )

        metrics = ""
        if incidents:
            metrics = "".join(
                [
                    metric_meta_items("Incidents per 100", rollup.get("incidentsPer100", {})),
                    metric_meta_items("Students Restrained per 100", rollup.get("studentsRestrainedPer100", {})),
                    metric_meta_items("Injuries per 100", rollup.get("injuriesPer100", {})),
                ]
            )

        content = f"""
<section class="section">
  <div class="container">
    {section_header('District Profile', district['districtName'], 'Case tracking, deadlines, meeting coverage, and linked restraint metrics.')}
    <div class="cases-grid">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">District Summary</span></div>
        <h3 class="case-card-title">{esc(district['districtName'])}</h3>
        <div class="case-card-meta">
          <div class="meta-item"><span class="meta-label">Code</span><span class="meta-value">{esc(code)}</span></div>
          <div class="meta-item"><span class="meta-label">Cases Tracked</span><span class="meta-value">{len(district_cases)}</span></div>
          <div class="meta-item"><span class="meta-label">Open Cases</span><span class="meta-value">{open_count}</span></div>
          <div class="meta-item"><span class="meta-label">Restraint Data</span><span class="meta-value">{'Available' if rollup else 'Not mapped'}</span></div>
        </div>
      </article>
      {metrics or ''}
    </div>
  </div>
</section>

<section class="section section-dark">
  <div class="container">
    {section_header('Cases', 'District Case Pages', 'Card-first case view with linked deadlines and status.')}
    <div class="cases-grid">{case_cards or '<p>No cases available.</p>'}</div>
  </div>
</section>

<section class="section">
  <div class="container">
    {section_header('Meetings', 'Upcoming Governance Meetings', 'Scraped school committee meetings for this district.')}
    <div class="resources-grid">{meeting_cards or '<p>No meetings scraped yet.</p>'}</div>
  </div>
</section>

<section class="section section-dark">
  <div class="container">
    {section_header('Updates', 'Recent District Updates', 'Manual and rules-derived updates tied to this district.')}
    <div class="resources-grid">{update_cards or '<p>No updates currently available.</p>'}</div>
  </div>
</section>
"""
        write_page(page_path, f"{district['districtName']} | Parent Data Force", content, site_dir, active="districts")
        urls.append(f"/districts/{slug}/")

        cards.append(
            f"""
<article class="resource-card" data-animate>
  <div class="resource-category">DISTRICT</div>
  <h3 class="resource-title">{esc(district['districtName'])}</h3>
  <p class="resource-excerpt">{len(district_cases)} tracked cases, {open_count} open.</p>
  <a class="resource-link" href="{slug}/">Open District Profile</a>
</article>
"""
        )

    index_content = f"""
<section class="section">
  <div class="container">
    {section_header('Districts', 'Investigation District Profiles', 'District-level pages for active investigation portfolios.')}
    <div class="resources-grid">{''.join(cards) or '<p>No district pages available.</p>'}</div>
  </div>
</section>
"""
    write_page(site_dir / "districts" / "index.html", "Districts | Parent Data Force", index_content, site_dir, active="districts")
    urls.append("/districts/")
    return urls


def build_case_pages(site_dir: Path, cases: list[dict], updates: list[dict], slug_map: dict[str, str]) -> list[str]:
    case_id_to_slug = {case.get("caseId", ""): slugify(case.get("caseId", "")) for case in cases}
    urls = []

    cards = []
    for case in sorted(cases, key=lambda x: x.get("caseId", "")):
        case_slug = case_id_to_slug.get(case["caseId"], slugify(case["caseId"]))
        page_path = site_dir / "cases" / case_slug / "index.html"

        district_code = case.get("districtCode", "")
        district_slug = slug_map.get(district_code, slugify(case.get("districtName", district_code)))
        related_rows = "".join(
            f'<li><a href="../{case_id_to_slug.get(item, slugify(item))}/">{esc(item)}</a></li>'
            for item in case.get("relatedCases", [])
        )

        timeline_items = case.get("timeline", [])
        timeline_sorted = sorted(timeline_items, key=lambda item: item.get("date") or "")
        timeline_count = len(timeline_sorted)
        first_event = timeline_sorted[0] if timeline_sorted else {}
        latest_event = timeline_sorted[-1] if timeline_sorted else {}
        timeline_doc_count = sum(len(item.get("documents", [])) for item in timeline_sorted)

        type_counts: dict[str, int] = {}
        for entry in timeline_sorted:
            t = entry.get("type", "Update")
            type_counts[t] = type_counts.get(t, 0) + 1
        type_summary = ", ".join(f"{k}: {v}" for k, v in sorted(type_counts.items(), key=lambda item: item[0]))

        timeline_notes = [entry.get("notes", "") for entry in timeline_sorted if entry.get("notes")]
        notes_rows = "".join(f"<li>{esc(text)}</li>" for text in timeline_notes[:8])
        top_level_notes = [
            case.get("statusReason", ""),
            case.get("recurrenceNotes", ""),
            case.get("notes", ""),
        ]
        top_level_notes_rows = "".join(f"<li>{esc(text)}</li>" for text in top_level_notes if text)

        cross_ref_rows = ""
        for ref in case.get("crossReferences", []):
            if isinstance(ref, dict):
                desc = ref.get("description", "")
                ref_type = ref.get("type", "Reference")
                cross_ref_rows += f"<li><strong>{esc(ref_type)}:</strong> {esc(desc)}</li>"
            elif ref:
                cross_ref_rows += f"<li>{esc(ref)}</li>"

        timeline_cards = "".join(
            f"""
<article class="resource-card" data-animate>
  <div class="resource-category">{esc(item.get('date'))}</div>
  <h3 class="resource-title">{esc(item.get('title'))}</h3>
  <p class="resource-excerpt">{esc(item.get('description'))}</p>
  {'<p class="resource-excerpt">Notes: ' + esc(item.get('notes')) + '</p>' if item.get('notes') else ''}
  <div class="resource-meta">{' '.join(f'<a class="related-link" href="../../{esc(doc)}">doc</a>' for doc in item.get('documents', []))}</div>
</article>
"""
            for item in timeline_sorted
        )

        case_updates = [u for u in updates if u.get("caseId") == case.get("caseId")]
        update_cards = "".join(
            f"""
<article class="resource-card" data-animate>
  <div class="resource-category">{esc(u.get('date'))}</div>
  <h3 class="resource-title">{esc(u.get('title'))}</h3>
  <p class="resource-excerpt">{esc(u.get('summary'))}</p>
</article>
"""
            for u in case_updates
        )

        content = f"""
<section class="section">
  <div class="container">
    {section_header('Case File', case.get('caseId', 'Case'), case.get('subject') or 'Detailed case timeline and document index.')}
    <div class="cases-grid">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">{esc(case.get('districtName'))}</span>{status_badge(case.get('statusLabelComputed') or case.get('statusLabel') or case.get('status'))}</div>
        <div class="case-card-id">{esc(case.get('type'))}</div>
        <h3 class="case-card-title">Status and Deadlines</h3>
        <div class="case-card-meta">
          <div class="meta-item"><span class="meta-label">Filed</span><span class="meta-value">{esc(case.get('filedDate') or 'n/a')}</span></div>
          <div class="meta-item"><span class="meta-label">Deadline</span><span class="meta-value">{esc(case.get('nextDeadline') or 'n/a')}</span></div>
          <div class="meta-item"><span class="meta-label">Deadline Status</span><span class="meta-value">{esc(case.get('deadlineLabel') or 'In progress')}</span></div>
          <div class="meta-item"><span class="meta-label">District</span><span class="meta-value"><a href="../../districts/{district_slug}/">{esc(case.get('districtName'))}</a></span></div>
        </div>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Scope</span></div>
        <h3 class="case-card-title">Requested Items</h3>
        <ul>
          {''.join(f'<li>{esc(item)}</li>' for item in case.get('requestedItems', [])) or '<li>No requested items listed.</li>'}
        </ul>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Timeline Summary</span></div>
        <h3 class="case-card-title">At-a-Glance Progress</h3>
        <div class="case-card-meta">
          <div class="meta-item"><span class="meta-label">Events</span><span class="meta-value">{timeline_count}</span></div>
          <div class="meta-item"><span class="meta-label">Linked Docs</span><span class="meta-value">{timeline_doc_count}</span></div>
          <div class="meta-item"><span class="meta-label">First Event</span><span class="meta-value">{esc(first_event.get('date') or 'n/a')}</span></div>
          <div class="meta-item"><span class="meta-label">Latest Event</span><span class="meta-value">{esc(latest_event.get('date') or 'n/a')}</span></div>
        </div>
        <p class="case-card-summary" style="margin-top:0.7rem;">Latest: {esc(latest_event.get('title') or 'No timeline yet')}</p>
        <p class="case-card-summary">Type Mix: {esc(type_summary or 'No typed events')}</p>
      </article>
    </div>
  </div>
</section>

<section class="section section-dark">
  <div class="container">
    {section_header('Related and Notes', 'Linked Cases and Context Notes', 'Related case references and qualitative notes from metadata and timeline events.')}
    <div class="cases-grid">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Related</span></div>
        <h3 class="case-card-title">Related Case Links</h3>
        <ul>{related_rows or '<li>No related cases.</li>'}</ul>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Notes</span></div>
        <h3 class="case-card-title">Case Notes</h3>
        <ul>{top_level_notes_rows or '<li>No top-level notes recorded.</li>'}</ul>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Pattern Flags</span></div>
        <h3 class="case-card-title">Cross References and Timeline Notes</h3>
        <ul>{cross_ref_rows or notes_rows or '<li>No cross references or timeline notes recorded.</li>'}</ul>
      </article>
    </div>
  </div>
</section>

<section class="section section-dark">
  <div class="container">
    {section_header('Timeline', 'Chronological Event Cards', 'All timeline entries and linked artifacts.')}
    <div class="resources-grid">{timeline_cards or '<p>No timeline entries.</p>'}</div>
  </div>
</section>

<section class="section">
  <div class="container">
    {section_header('Updates', 'Case Update Stream', 'Recent updates directly associated with this case.')}
    <div class="resources-grid">{update_cards or '<p>No updates for this case.</p>'}</div>
  </div>
</section>
"""
        write_page(page_path, f"{case['caseId']} | Parent Data Force", content, site_dir, active="cases")
        urls.append(f"/cases/{case_slug}/")

        cards.append(
            f"""
<article class="case-card" data-animate>
  <div class="case-card-header"><span class="case-district">{esc(case.get('districtName'))}</span>{status_badge(case.get('statusLabelComputed') or case.get('statusLabel') or case.get('status'))}</div>
  <div class="case-card-id">{esc(case.get('caseId'))}</div>
  <h3 class="case-card-title">{esc(case.get('subject') or case.get('type'))}</h3>
  <p class="case-card-summary">{esc(case.get('nextDeadlineDescription') or 'No summary provided.')}</p>
  <a class="resource-link" href="{case_slug}/">Open Case Page</a>
</article>
"""
        )

    index_content = f"""
<section class="section">
  <div class="container">
    {section_header('Cases', 'Investigation Case Pages', 'Dedicated pages for each tracked case with timelines and documents.')}
    <div class="cases-grid">{''.join(cards) or '<p>No case pages available.</p>'}</div>
  </div>
</section>
"""
    write_page(site_dir / "cases" / "index.html", "Cases | Parent Data Force", index_content, site_dir, active="cases")
    urls.append("/cases/")
    return urls


def event_card(event: dict, lane: str = "") -> str:
    when = event.get("startAt") or event.get("date")
    event_type = event.get("type", "event")
    district = event.get("districtCode", "")
    case = event.get("caseId", "")
    source_url = event.get("source", {}).get("url", "")
    lane_label = lane or ("Governance" if event_type == "meeting" else "Deadline")
    extras = []
    if district:
        extras.append(f"District: {district}")
    if case:
        extras.append(f"Case: {case}")
    label_html = f'<span class="resource-read-time">{esc(event.get("label"))}</span>' if event.get("label") else '<span class="resource-read-time">&nbsp;</span>'
    source_html = f'<a class="resource-link" href="{esc(source_url)}">Source</a>' if source_url else '<a class="resource-link" href="#">Derived</a>'
    return f"""
<article class="resource-card" data-animate>
  <div class="resource-category">{esc(lane_label).upper()}</div>
  <h3 class="resource-title">{esc(event.get('title'))}</h3>
  <p class="resource-excerpt">{esc(when)}{' | ' + esc(' | '.join(extras)) if extras else ''}</p>
  <div class="resource-meta">
    {label_html}
    {source_html}
  </div>
</article>
"""


def build_calendar_page(site_dir: Path, calendar_events: list[dict]) -> str:
    today_iso = date.today().isoformat()
    governance_events = [e for e in calendar_events if e.get("type") == "meeting"]
    deadline_events = [e for e in calendar_events if e.get("type") != "meeting"]

    upcoming_governance = [e for e in governance_events if (e.get("startAt") or e.get("date") or "") >= today_iso]
    upcoming_deadlines = [e for e in deadline_events if (e.get("startAt") or e.get("date") or "") >= today_iso]
    past = [e for e in calendar_events if (e.get("startAt") or e.get("date") or "") < today_iso]

    upcoming_governance.sort(key=lambda x: x.get("startAt") or x.get("date") or "")
    upcoming_deadlines.sort(key=lambda x: x.get("startAt") or x.get("date") or "")
    past.sort(key=lambda x: x.get("startAt") or x.get("date") or "", reverse=True)

    calendar_payload = [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "type": item.get("type"),
            "date": item.get("date") or (item.get("startAt") or "")[:10],
            "startAt": item.get("startAt") or "",
            "districtCode": item.get("districtCode") or "",
            "caseId": item.get("caseId") or "",
            "status": item.get("status") or "",
            "label": item.get("label") or "",
            "sourceUrl": item.get("source", {}).get("url") or "",
        }
        for item in calendar_events
    ]

    governance_cards = "".join(event_card(e, lane="Governance") for e in upcoming_governance[:300])
    deadline_cards = "".join(event_card(e, lane="Deadline") for e in upcoming_deadlines[:300])
    past_cards = "".join(
        event_card(e, lane=("Governance" if e.get("type") == "meeting" else "Deadline")) for e in past[:300]
    )
    calendar_payload_json = json.dumps(calendar_payload).replace("</", "<\\/")

    content = f"""
<section class="section">
  <div class="container">
    {section_header('Calendar', 'Governance Meetings and Deadlines', 'Visual month calendar with separated governance and deadline event lanes.')}
    <div class="cases-grid" style="margin-bottom:1rem;">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Governance</span></div>
        <h3 class="case-card-title">Upcoming Meetings</h3>
        <div class="case-card-meta"><div class="meta-item"><span class="meta-label">Count</span><span class="meta-value">{len(upcoming_governance)}</span></div></div>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Deadlines</span></div>
        <h3 class="case-card-title">Upcoming Deadline Events</h3>
        <div class="case-card-meta"><div class="meta-item"><span class="meta-label">Count</span><span class="meta-value">{len(upcoming_deadlines)}</span></div></div>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Past</span></div>
        <h3 class="case-card-title">Historical Entries</h3>
        <div class="case-card-meta"><div class="meta-item"><span class="meta-label">Count</span><span class="meta-value">{len(past)}</span></div></div>
      </article>
    </div>

    <div class="repo-controls" data-calendar-controls>
      <div class="repo-filters">
        <button class="filter-btn active" data-calendar-lane="all" type="button">All Events</button>
        <button class="filter-btn" data-calendar-lane="meeting" type="button">Governance</button>
        <button class="filter-btn" data-calendar-lane="deadline" type="button">Deadlines</button>
      </div>
      <div class="repo-filters">
        <button class="filter-btn" id="calendarPrevMonth" type="button">Previous Month</button>
        <button class="filter-btn" id="calendarToday" type="button">Today</button>
        <button class="filter-btn" id="calendarNextMonth" type="button">Next Month</button>
      </div>
    </div>

    <div class="repo-table-wrapper" data-animate style="padding:0.8rem;">
      <div class="calendar-month-header">
        <h3 id="calendarMonthLabel" class="section-title" style="font-size:1.2rem;margin:0;"></h3>
      </div>
      <div class="calendar-weekdays">
        <span>Sun</span><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span>
      </div>
      <div id="calendarGrid" class="calendar-grid"></div>
    </div>

    <div class="repo-table-wrapper" style="margin-top:1rem;padding:0.8rem;" data-animate>
      <h3 class="section-title" style="font-size:1.1rem;">Selected Day</h3>
      <div class="cases-grid">
        <article class="case-card">
          <div class="case-card-header"><span class="case-district">Governance Meetings</span></div>
          <ul id="calendarDayMeetings"><li>Select a date.</li></ul>
        </article>
        <article class="case-card">
          <div class="case-card-header"><span class="case-district">Deadline Events</span></div>
          <ul id="calendarDayDeadlines"><li>Select a date.</li></ul>
        </article>
        <article class="case-card">
          <div class="case-card-header"><span class="case-district">Day Summary</span></div>
          <div class="case-card-meta">
            <div class="meta-item"><span class="meta-label">Date</span><span class="meta-value" id="calendarSelectedDate">-</span></div>
            <div class="meta-item"><span class="meta-label">Events</span><span class="meta-value" id="calendarSelectedCount">0</span></div>
          </div>
        </article>
      </div>
    </div>
    <script id="calendarEventsData" type="application/json">{calendar_payload_json}</script>
  </div>
</section>

<section class="section section-dark">
  <div class="container">
    {section_header('Governance', 'Upcoming Governance Meetings', 'School committee and governance meetings shown separately from deadlines.')}
    <div class="resources-grid">{governance_cards or '<p>No upcoming governance meetings.</p>'}</div>
  </div>
</section>

<section class="section">
  <div class="container">
    {section_header('Deadlines', 'Upcoming Deadline Events', 'Case and governance deadline milestones grouped independently.')}
    <div class="resources-grid">{deadline_cards or '<p>No upcoming deadlines.</p>'}</div>
  </div>
</section>

<section class="section section-dark">
  <div class="container">
    {section_header('History', 'Past Governance and Deadline Events', 'Chronological backfill with both event families retained.')}
    <div class="resources-grid">{past_cards or '<p>No past events.</p>'}</div>
  </div>
</section>
"""
    write_page(site_dir / "calendar" / "index.html", "Calendar | Parent Data Force", content, site_dir, active="calendar")
    return "/calendar/"


def build_updates_page(site_dir: Path, updates: list[dict]) -> str:
    cards = "".join(
        f"""
<article class="resource-card" data-animate>
  <div class="resource-category">{esc(item.get('severity', 'info')).upper()}</div>
  <h3 class="resource-title">{esc(item.get('title'))}</h3>
  <p class="resource-excerpt">{esc(item.get('summary') or '')}</p>
  <div class="resource-meta"><span class="resource-read-time">{esc(item.get('date'))}</span></div>
</article>
"""
        for item in updates[:500]
    )
    content = f"""
<section class="section">
  <div class="container">
    {section_header('Updates', 'Hybrid Update Stream', 'Manual and rules-derived updates across cases and districts.')}
    <div class="resources-grid">{cards or '<p>No updates available.</p>'}</div>
  </div>
</section>
"""
    write_page(site_dir / "updates" / "index.html", "Updates | Parent Data Force", content, site_dir, active="updates")
    return "/updates/"


def build_goals_page(site_dir: Path, goals: list[dict]) -> str:
    cards = "".join(
        f"""
<article class="case-card" data-animate>
  <div class="case-card-header"><span class="case-district">GOAL</span>{status_badge(item.get('status', 'active'))}</div>
  <h3 class="case-card-title">{esc(item.get('title'))}</h3>
  <div class="case-card-meta">
    <div class="meta-item"><span class="meta-label">Target Date</span><span class="meta-value">{esc(item.get('targetDate') or 'n/a')}</span></div>
  </div>
</article>
"""
        for item in goals
    )
    content = f"""
<section class="section">
  <div class="container">
    {section_header('Goals', 'Advocacy and Operations Goals', 'Current goals and target dates.')}
    <div class="cases-grid">{cards or '<p>No goals configured.</p>'}</div>
  </div>
</section>
"""
    write_page(site_dir / "goals" / "index.html", "Goals | Parent Data Force", content, site_dir, active="updates")
    return "/goals/"


def build_speeches_page(site_dir: Path, speeches: list[dict]) -> str:
    cards = "".join(
        f"""
<article class="resource-card" data-animate>
  <div class="resource-category">{esc(item.get('publishedAt', ''))[:10]}</div>
  <h3 class="resource-title">{esc(item.get('title'))}</h3>
  <a class="resource-link" href="{esc(item.get('url'))}">Watch Speech</a>
</article>
"""
        for item in speeches
    )
    content = f"""
<section class="section">
  <div class="container">
    {section_header('Speeches', 'Public Comments and Testimony', 'Ingested from configured speech feed sources.')}
    <div class="resources-grid">{cards or '<p>No speech records available.</p>'}</div>
  </div>
</section>
"""
    write_page(site_dir / "speeches" / "index.html", "Speeches | Parent Data Force", content, site_dir, active="speeches")
    return "/speeches/"


def build_pr_pages(site_dir: Path, cases: list[dict]) -> tuple[str, str]:
    prs_cards = []
    prr_cards = []
    for case in cases:
        card = f"""
<article class="case-card" data-animate>
  <div class="case-card-header"><span class="case-district">{esc(case.get('districtName') or case.get('districtCode'))}</span>{status_badge(case.get('statusLabelComputed') or case.get('statusLabel') or case.get('status'))}</div>
  <div class="case-card-id">{esc(case.get('caseId'))}</div>
  <h3 class="case-card-title">{esc(case.get('subject') or case.get('type'))}</h3>
  <a class="resource-link" href="../cases/{slugify(case.get('caseId', ''))}/">Open Case</a>
</article>
"""
        if "PRS" in case.get("caseId", ""):
            prs_cards.append(card)
        if "Public Records" in case.get("type", ""):
            prr_cards.append(card)

    prs_content = f"""
<section class="section">
  <div class="container">
    {section_header('PRS', 'DESE PRS Cases', 'Request for local response and determination-linked matters.')}
    <div class="cases-grid">{''.join(prs_cards) or '<p>No PRS cases.</p>'}</div>
  </div>
</section>
"""
    prr_content = f"""
<section class="section">
  <div class="container">
    {section_header('Public Records', 'Public Records Request Cases', 'Records-focused case pages and progress tracking.')}
    <div class="cases-grid">{''.join(prr_cards) or '<p>No public records cases.</p>'}</div>
  </div>
</section>
"""
    write_page(site_dir / "prs" / "index.html", "PRS Cases | Parent Data Force", prs_content, site_dir, active="cases")
    write_page(site_dir / "public-records" / "index.html", "Public Records Cases | Parent Data Force", prr_content, site_dir, active="cases")
    return "/prs/", "/public-records/"


def restraint_table_row(cols: list[str], attrs: dict[str, object] | None = None) -> str:
    attr_bits = []
    for key, value in (attrs or {}).items():
        attr_bits.append(f'data-{key}="{esc(value)}"')
    attrs_text = " " + " ".join(attr_bits) if attr_bits else ""
    return f"<tr{attrs_text}>" + "".join(f"<td>{col}</td>" for col in cols) + "</tr>"


def build_restraint_pages(site_dir: Path, district_records: list[dict], school_records: list[dict], year_records: list[dict]) -> list[str]:
    entity_year_rows = [row for row in year_records if not row.get("isSummaryRow")]
    summary_rows = sorted([row for row in year_records if row.get("isSummaryRow")], key=lambda row: str(row.get("schoolYear", "")))
    latest_summary = summary_rows[-1] if summary_rows else {}
    latest_year = max((str(row.get("schoolYear")) for row in entity_year_rows if row.get("schoolYear")), default="n/a")
    known_latest_rows = [
        row for row in entity_year_rows if row.get("schoolYear") == latest_year and row.get("isRawKnownRestraints")
    ]

    source_workbooks = sorted({str(row.get("sourceWorkbook", "")).strip() for row in year_records if row.get("sourceWorkbook")})
    workbook_links = "".join(
        f'<li><a class="resource-link" href="../data/raw/dese-restraint/{esc(name)}">{esc(name)}</a></li>'
        for name in source_workbooks
    )

    content = f"""
<section class="section" id="restraintExplorer" data-url="../data/restraint_explorer.json">
  <div class="container">
    {section_header('Restraint and Seclusion', 'Single-Page JSON Explorer', 'All restraint and seclusion analysis is consolidated into JSON datasets and rendered on this one page.')}
    <div class="cases-grid">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Coverage</span></div>
        <h3 class="case-card-title">Rows Loaded</h3>
        <div class="case-card-meta">
          <div class="meta-item"><span class="meta-label">Districts</span><span class="meta-value">{len(district_records)}</span></div>
          <div class="meta-item"><span class="meta-label">Schools</span><span class="meta-value">{len(school_records)}</span></div>
          <div class="meta-item"><span class="meta-label">School-Year Rows</span><span class="meta-value">{len(entity_year_rows)}</span></div>
          <div class="meta-item"><span class="meta-label">Latest Year</span><span class="meta-value">{esc(latest_year)}</span></div>
        </div>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Statewide</span></div>
        <h3 class="case-card-title">Latest Public Schools Total</h3>
        <div class="case-card-meta">
          <div class="meta-item"><span class="meta-label">Year</span><span class="meta-value">{esc(latest_summary.get('schoolYear') or 'n/a')}</span></div>
          <div class="meta-item"><span class="meta-label">Restraints</span><span class="meta-value">{fmt_num(latest_summary.get('rawTotalRestraints'), 0)}</span></div>
          <div class="meta-item"><span class="meta-label">Rate/100</span><span class="meta-value">{fmt_num(latest_summary.get('rawRestraintRatePer100'))}</span></div>
          <div class="meta-item"><span class="meta-label">Rows with Raw Values</span><span class="meta-value">{len(known_latest_rows)}</span></div>
        </div>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Method</span></div>
        <h3 class="case-card-title">Source-Table Fidelity</h3>
        <ul>
          <li>DESE values are loaded directly from source workbooks.</li>
          <li>Suppressed marker '-' remains unknown and is not midpoint-estimated.</li>
          <li>Rank context is shown in two lenses: all rows minus summary + traditional comparable.</li>
          <li>Use selectors below to view important calculations for any district or school.</li>
        </ul>
      </article>
    </div>

    <div class="cases-grid" style="margin-top:1rem;">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">District Selector</span></div>
        <h3 class="case-card-title">Important District Calculations</h3>
        <div class="repo-filters" style="margin-bottom:0.7rem;">
          <select class="repo-select" id="restraintDistrictSelect">
            <option value="">Select a district...</option>
          </select>
        </div>
        <div id="restraintDistrictHighlights"><p>Select a district to view calculations.</p></div>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">School Selector</span></div>
        <h3 class="case-card-title">Important School Calculations</h3>
        <div class="repo-filters" style="margin-bottom:0.7rem;">
          <select class="repo-select" id="restraintSchoolSelect">
            <option value="">Select a school...</option>
          </select>
        </div>
        <div id="restraintSchoolHighlights"><p>Select a school to view calculations.</p></div>
      </article>
    </div>

    <div class="repo-table-wrapper" style="margin-top:1rem;padding:0.8rem;">
      <h3 class="section-title" style="font-size:1.1rem;">Source Workbooks</h3>
      <ul>{workbook_links or '<li>No workbook links available.</li>'}</ul>
    </div>
  </div>
</section>

<section class="section section-dark">
  <div class="container">
    {section_header('District Data', 'Latest-Year District Calculations', 'Search, filter, and sort district-level metrics in this single page.')}
    <div class="repo-controls" data-table-controls data-target-table="restraintDistrictTable">
      <div class="repo-search"><input type="text" class="repo-search-input" placeholder="Search district or code..." data-table-search></div>
      <div class="repo-filters">
        <select class="repo-select" data-table-sort>
          <option value="4|num|desc">Sort: Latest Rate (High to Low)</option>
          <option value="5|num|desc">Sort: YoY Delta (High to Low)</option>
          <option value="9|num|desc">Sort: Top Share (High to Low)</option>
          <option value="0|text|asc">Sort: District A-Z</option>
        </select>
        <span class="resource-read-time" data-table-count></span>
      </div>
    </div>
    <div class="repo-table-wrapper" data-animate>
      <table class="repo-table" id="restraintDistrictTable">
        <thead>
          <tr>
            <th>District</th><th>Code</th><th>Latest Year</th><th>Restraints</th><th>Rate/100</th><th>YoY Delta</th>
            <th>Peak Year</th><th>Peak Total</th><th>Top School</th><th>Top Share</th><th>Rate Rank (All)</th><th>Rate Rank (Trad)</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    {section_header('School Data', 'Latest-Year School Calculations', 'Search, filter, and sort school-level metrics in this single page.')}
    <div class="repo-controls" data-table-controls data-target-table="restraintSchoolTable">
      <div class="repo-search"><input type="text" class="repo-search-input" placeholder="Search school or district..." data-table-search></div>
      <div class="repo-filters">
        <select class="repo-select" data-table-filter-key="district" data-table-populate="district"><option value="all">All Districts</option></select>
        <select class="repo-select" data-table-filter-key="traditional"><option value="all">Traditional: Any</option><option value="yes">Traditional: Yes</option><option value="no">Traditional: No</option></select>
        <select class="repo-select" data-table-sort>
          <option value="5|num|desc">Sort: Latest Rate (High to Low)</option>
          <option value="7|num|desc">Sort: YoY Delta (High to Low)</option>
          <option value="0|text|asc">Sort: School A-Z</option>
        </select>
        <span class="resource-read-time" data-table-count></span>
      </div>
    </div>
    <div class="repo-table-wrapper" data-animate>
      <table class="repo-table" id="restraintSchoolTable">
        <thead>
          <tr>
            <th>School</th><th>District</th><th>Code</th><th>Latest Year</th><th>Restraints</th><th>Rate/100</th>
            <th>Repeat</th><th>YoY Delta</th><th>Peak Year</th><th>Peak Total</th><th>Rate Rank (All)</th><th>Rate Rank (Trad)</th><th>Traditional?</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</section>

<section class="section section-dark">
  <div class="container">
    {section_header('School-Year Data', 'Direct DESE Rows + Rank Context', 'Full school-year rows are retained in JSON and rendered in this single explorer page.')}
    <div class="repo-controls" id="restraintSchoolYearControls">
      <div class="repo-search"><input type="text" class="repo-search-input" placeholder="Search by year, district, or school..." id="restraintSchoolYearSearch"></div>
      <div class="repo-filters">
        <select class="repo-select" id="restraintSchoolYearDistrict"><option value="all">All Districts</option></select>
        <select class="repo-select" id="restraintSchoolYearYear"><option value="all">All Years</option></select>
        <select class="repo-select" id="restraintSchoolYearTraditional"><option value="all">Traditional: Any</option><option value="yes">Traditional: Yes</option><option value="no">Traditional: No</option></select>
        <select class="repo-select" id="restraintSchoolYearSort">
          <option value="7|num|desc">Sort: Rate/100 (High to Low)</option>
          <option value="0|text|desc">Sort: Year Desc</option>
          <option value="1|text|asc">Sort: District A-Z</option>
        </select>
        <select class="repo-select" id="restraintSchoolYearPageSize"><option value="50">50 / page</option><option value="100" selected>100 / page</option><option value="250">250 / page</option></select>
        <span class="resource-read-time" id="restraintSchoolYearCount"></span>
      </div>
    </div>
    <div class="repo-table-wrapper" data-animate>
      <table class="repo-table" id="restraintSchoolYearTable">
        <thead>
          <tr>
            <th>Year</th><th>District</th><th>School</th><th>Enroll</th><th>Students</th><th>Restraints</th><th>Injuries</th>
            <th>Rate/100</th><th>Repeat</th><th>Inj/Restraint</th><th>Rate Rank (All)</th><th>Total Rank (All)</th><th>Rate Rank (Trad)</th><th>Total Rank (Trad)</th><th>Traditional?</th><th>Workbook</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="repo-filters" style="margin-top:0.75rem;justify-content:flex-end;" id="restraintSchoolYearPager">
      <button type="button" class="btn btn-secondary" id="restraintSchoolYearPrev">Previous</button>
      <span class="resource-read-time" id="restraintSchoolYearPageLabel">Page 1 of 1</span>
      <button type="button" class="btn btn-secondary" id="restraintSchoolYearNext">Next</button>
    </div>
  </div>
</section>
"""
    write_page(site_dir / "restraint-seclusion" / "index.html", "Restraint and Seclusion | Parent Data Force", content, site_dir, active="restraint")
    return ["/restraint-seclusion/"]


def build_admin_ingest_pages(site_dir: Path) -> None:
    base = site_dir / "admin-ingest"
    pages = {
        "index.html": (
            "Admin Ingest | Parent Data Force",
            f"""
<section class="section" id="adminIngestDashboard" data-url="../data/derived/ingest/review_dashboard.json">
  <div class="container">
    {section_header('Admin Ingest', 'Hidden Review Dashboard', 'Local-first admin queue for deterministic extraction, heuristic suggestions, linking, and file handling.')}
    <div class="cases-grid">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Queue Summary</span></div>
        <h3 class="case-card-title">Ingest Pipeline</h3>
        <div id="adminIngestSummary"><p>Loading ingest summary...</p></div>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Shortcuts</span></div>
        <h3 class="case-card-title">Admin Routes</h3>
        <ul>
          <li><a class="resource-link" href="queue/">Open Queue</a></li>
          <li><a class="resource-link" href="cases/">Manage Cases</a></li>
          <li><a class="resource-link" href="review/">Open Review Console</a></li>
          <li><a class="resource-link" href="study/">Open Study Analysis</a></li>
          <li><a class="resource-link" href="notes/">Open Notes and Context</a></li>
          <li><a class="resource-link" href="redaction/">Open Redaction</a></li>
          <li><a class="resource-link" href="dese/">Open DESE Enrichment</a></li>
          <li><a class="resource-link" href="completed/">Open Completed Queue</a></li>
          <li><a class="resource-link" href="runs/">Open Run History</a></li>
        </ul>
      </article>
    </div>
  </div>
</section>
""",
        ),
        "queue/index.html": (
            "Admin Ingest Queue | Parent Data Force",
            f"""
<section class="section" id="adminIngestQueue" data-url="../../data/derived/ingest/review_dashboard.json">
  <div class="container">
    {section_header('Admin Queue', 'Queued Intake Documents', 'Review files from global intake and case-level intake folders. Filter, inspect, and move items through the review workflow.')}
    <div class="repo-controls" data-table-controls data-target-table="adminIngestQueueTable">
      <div class="repo-search"><input type="text" class="repo-search-input" placeholder="Search doc id, type, path, case, or district..." data-table-search></div>
      <div class="repo-filters">
        <select class="repo-select" data-table-filter-key="state"><option value="all">All States</option></select>
        <select class="repo-select" data-table-filter-key="family"><option value="all">All Families</option></select>
        <select class="repo-select" data-table-filter-key="source"><option value="all">All Sources</option></select>
        <select class="repo-select" data-table-sort>
          <option value="8|text|asc">Sort: Priority</option>
          <option value="0|text|asc">Sort: Doc ID</option>
          <option value="4|num|desc">Sort: Case Links</option>
        </select>
        <span class="resource-read-time" data-table-count></span>
      </div>
    </div>
    <div class="repo-table-wrapper" data-animate>
      <table class="repo-table" id="adminIngestQueueTable">
        <thead>
          <tr>
            <th>Doc ID</th><th>State</th><th>Family</th><th>Type</th><th>Case Links</th><th>District Links</th><th>Source</th><th>Location</th><th>Priority</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</section>
""",
        ),
        "review/index.html": (
            "Admin Ingest Review | Parent Data Force",
            f"""
<section class="section" id="adminIngestReview" data-url="../../data/derived/ingest/review_dashboard.json">
  <div class="container">
    {section_header('Review Console', 'Deterministic vs Suggestion Lane', 'Select a document and inspect deterministic extraction, suggestion fields, linking hints, and manual override needs.')}
    <div class="cases-grid">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Document Selector</span></div>
        <h3 class="case-card-title">Pick Queue Item</h3>
        <div class="repo-filters"><select class="repo-select" id="adminReviewSelect"><option value="">Select a document...</option></select></div>
        <div id="adminReviewMeta"><p>Select a document to review.</p></div>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Manual Linking</span></div>
        <h3 class="case-card-title">Suggested Entity Targets</h3>
        <div id="adminReviewLinks"><p>Links will appear here.</p></div>
      </article>
    </div>
    <div class="cases-grid" style="margin-top:1rem;">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Local Admin Writes</span></div>
        <h3 class="case-card-title">Review Actions</h3>
        <div id="adminWriteStatus"><p>Connect to local admin server at `http://127.0.0.1:8765` for browser-side writes.</p></div>
        <div class="repo-filters" style="margin:0.75rem 0;">
          <button type="button" class="btn btn-secondary" id="adminReviewApproveBtn">Approve</button>
          <button type="button" class="btn btn-secondary" id="adminReviewDeferBtn">Defer</button>
          <button type="button" class="btn btn-secondary" id="adminReviewReopenBtn">Reopen</button>
        </div>
        <div class="repo-filters" style="margin-bottom:0.75rem;">
          <input type="text" class="repo-search-input" id="adminReviewCaseLink" placeholder="Case ID for manual link">
          <button type="button" class="btn btn-secondary" id="adminReviewLinkCaseBtn">Link Case</button>
        </div>
        <div class="repo-filters">
          <input type="text" class="repo-search-input" id="adminReviewDistrictLink" placeholder="District code for manual link">
          <button type="button" class="btn btn-secondary" id="adminReviewLinkDistrictBtn">Link District</button>
        </div>
        <div class="repo-filters" style="margin-top:0.75rem;">
          <input type="text" class="repo-search-input" id="adminReviewOverrideField" placeholder="Field name to override">
          <input type="text" class="repo-search-input" id="adminReviewOverrideValue" placeholder="Override value">
          <button type="button" class="btn btn-secondary" id="adminReviewOverrideBtn">Set Override</button>
        </div>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Quick Note</span></div>
        <h3 class="case-card-title">Add Context</h3>
        <div class="repo-filters" style="margin-bottom:0.75rem;">
          <select class="repo-select" id="adminReviewNoteCategory">
            <option value="red-flag">Red Flag</option>
            <option value="chronology">Chronology</option>
            <option value="entity">Entity</option>
            <option value="general">General</option>
          </select>
        </div>
        <textarea id="adminReviewNoteBody" class="repo-search-input" style="min-height:8rem;resize:vertical;" placeholder="Add a note for this document..."></textarea>
        <div class="repo-filters" style="margin-top:0.75rem;">
          <button type="button" class="btn btn-secondary" id="adminReviewAddNoteBtn">Add Note</button>
        </div>
      </article>
    </div>
    <div class="repo-table-wrapper" style="margin-top:1rem;padding:0.8rem;">
      <h3 class="section-title" style="font-size:1.05rem;">Local Shell Actions</h3>
      <pre id="adminReviewCommands" style="white-space:pre-wrap;overflow:auto;">Select a document to show CLI actions for approve, link, defer, or move-to-completed.</pre>
    </div>
    <div class="cases-grid" style="margin-top:1rem;">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Field Candidates</span></div>
        <h3 class="case-card-title">Human-Readable Suggested Fills</h3>
        <div class="repo-filters" style="margin-bottom:0.75rem;">
          <button type="button" class="btn btn-secondary" id="adminReviewApproveAllBtn">Approve All Visible</button>
        </div>
        <div id="adminReviewFieldCandidates"><p>Select a document to review field candidates.</p></div>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Attachments</span></div>
        <h3 class="case-card-title">Attachment Analysis</h3>
        <div id="adminReviewAttachments"><p>Select a document to inspect email attachments.</p></div>
      </article>
    </div>
    <div class="cases-grid" style="margin-top:1rem;">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Thread Context</span></div>
        <h3 class="case-card-title">Prior Messages</h3>
        <div id="adminReviewThreadContext"><p>Select a document to view thread context.</p></div>
      </article>
    </div>
    <div class="cases-grid" style="margin-top:1rem;">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Deterministic Extract</span></div>
        <pre id="adminReviewDeterministic" style="white-space:pre-wrap;overflow:auto;max-height:34rem;">Select a document to view deterministic extraction.</pre>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Suggestion Lane</span></div>
        <pre id="adminReviewSuggestions" style="white-space:pre-wrap;overflow:auto;max-height:34rem;">Select a document to view suggestion output.</pre>
      </article>
    </div>
  </div>
</section>
""",
        ),
        "study/index.html": (
            "Admin Study Analysis | Parent Data Force",
            f"""
<section class="section" id="adminStudyAnalysis" data-report-url="../../data/derived/ingest/study_email_report.json" data-threads-url="../../data/derived/ingest/study_threads.json" data-events-url="../../data/derived/ingest/study_combined_events.json" data-graph-url="../../data/derived/ingest/study_participant_graph.json" data-candidates-url="../../data/derived/ingest/study_entity_candidates.json">
  <div class="container">
    {section_header('Study Corpus', 'Combined Email + Attachment Learning Window', 'Focused analysis view for the Attleboro records-access and Supervisor of Public Records email window.')}
    <div class="cases-grid">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Summary</span></div>
        <h3 class="case-card-title">Study Snapshot</h3>
        <pre id="adminStudySummary" style="white-space:pre-wrap;overflow:auto;max-height:18rem;">Loading study summary...</pre>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Participant Graph</span></div>
        <h3 class="case-card-title">Top Contact Paths</h3>
        <pre id="adminStudyGraph" style="white-space:pre-wrap;overflow:auto;max-height:18rem;">Loading participant graph...</pre>
      </article>
    </div>
    <div class="cases-grid" style="margin-top:1rem;">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Threads</span></div>
        <h3 class="case-card-title">Thread Clusters</h3>
        <pre id="adminStudyThreads" style="white-space:pre-wrap;overflow:auto;max-height:30rem;">Loading thread clusters...</pre>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Combined Events</span></div>
        <h3 class="case-card-title">Process Stage Candidates</h3>
        <pre id="adminStudyEvents" style="white-space:pre-wrap;overflow:auto;max-height:30rem;">Loading combined events...</pre>
      </article>
    </div>
    <div class="repo-table-wrapper" style="margin-top:1rem;padding:0.8rem;">
      <h3 class="section-title" style="font-size:1.05rem;">Entity/Profile Fill Candidates</h3>
      <pre id="adminStudyCandidates" style="white-space:pre-wrap;overflow:auto;max-height:22rem;">Loading entity candidates...</pre>
    </div>
  </div>
</section>
""",
        ),
        "notes/index.html": (
            "Admin Ingest Notes | Parent Data Force",
            f"""
<section class="section" id="adminIngestNotes" data-notes-url="../../data/derived/ingest/notes.json" data-bundles-url="../../data/derived/ingest/note_bundles.json" data-templates-url="../../data/derived/ingest/note_templates.json">
  <div class="container">
    {section_header('Notes and Context', 'File Notes, Bundles, and Reusable Blocks', 'Scaffold view for per-file notes, multi-file bundles, reusable note blocks, chronology notes, and red-flag context.')}
    <div class="cases-grid">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Templates</span></div>
        <h3 class="case-card-title">Reusable Note Blocks</h3>
        <pre id="adminNotesTemplates" style="white-space:pre-wrap;overflow:auto;max-height:28rem;">Loading note templates...</pre>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Active Notes</span></div>
        <h3 class="case-card-title">Current Notes Store</h3>
        <pre id="adminNotesRecords" style="white-space:pre-wrap;overflow:auto;max-height:28rem;">Loading notes...</pre>
      </article>
    </div>
  </div>
</section>
""",
        ),
        "cases/index.html": (
            "Admin Cases | Parent Data Force",
            f"""
<section class="section" id="adminCasesManager" data-cases-url="../../data/entities/cases" data-dashboard-url="../../data/derived/ingest/review_dashboard.json">
  <div class="container">
    {section_header('Case Management', 'Existing Cases, Investigations, and Related Records', 'Manage current case records from the makeshift JSON database and review linked ingest activity.')}
    <div class="repo-controls" data-table-controls data-target-table="adminCasesTable">
      <div class="repo-search"><input type="text" class="repo-search-input" placeholder="Search case, district, type, or title..." data-table-search></div>
      <div class="repo-filters">
        <select class="repo-select" data-table-filter-key="district"><option value="all">All Districts</option></select>
        <select class="repo-select" data-table-sort>
          <option value="0|text|asc">Sort: Case ID</option>
          <option value="3|text|asc">Sort: Status</option>
          <option value="1|text|asc">Sort: District</option>
        </select>
        <span class="resource-read-time" data-table-count></span>
      </div>
    </div>
    <div class="repo-table-wrapper" data-animate>
      <table class="repo-table" id="adminCasesTable">
        <thead><tr><th>Case ID</th><th>District</th><th>Type</th><th>Status</th><th>Title</th><th>Next Deadline</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</section>
""",
        ),
        "redaction/index.html": (
            "Admin Redaction | Parent Data Force",
            f"""
<section class="section" id="adminIngestRedaction" data-profiles-url="../../data/derived/ingest/redaction_profiles.json" data-jobs-url="../../data/derived/ingest/redaction_jobs.json" data-previews-url="../../data/derived/ingest/redaction_previews.json">
  <div class="container">
    {section_header('Redaction and Anonymization', 'Profiles, Jobs, and Public-Safe Output Planning', 'Scaffold view for redaction levels, preview jobs, and public-safe parallel outputs.')}
    <div class="cases-grid">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Profiles</span></div>
        <h3 class="case-card-title">Redaction Levels</h3>
        <pre id="adminRedactionProfiles" style="white-space:pre-wrap;overflow:auto;max-height:28rem;">Loading redaction profiles...</pre>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Jobs</span></div>
        <h3 class="case-card-title">Queued Redaction Jobs</h3>
        <pre id="adminRedactionJobs" style="white-space:pre-wrap;overflow:auto;max-height:28rem;">Loading redaction jobs...</pre>
      </article>
    </div>
    <div class="repo-table-wrapper" style="margin-top:1rem;padding:0.8rem;">
      <h3 class="section-title" style="font-size:1.05rem;">Preview Output</h3>
      <pre id="adminRedactionPreviews" style="white-space:pre-wrap;overflow:auto;max-height:28rem;">Loading redaction previews...</pre>
    </div>
  </div>
</section>
""",
        ),
        "dese/index.html": (
            "Admin DESE Enrichment | Parent Data Force",
            f"""
<section class="section" id="adminDeseEnrichment" data-targets-url="../../data/derived/dese_enrichment/targets.json" data-fields-url="../../data/derived/dese_enrichment/field_catalog.json">
  <div class="container">
    {section_header('DESE Enrichment', 'District, School, People, Metrics, and Report Targets', 'Scaffold view for DESE Profiles enrichment targets, field catalog, and report families to ingest next.')}
    <div class="cases-grid">
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Targets</span></div>
        <h3 class="case-card-title">DESE Target Queue</h3>
        <pre id="adminDeseTargets" style="white-space:pre-wrap;overflow:auto;max-height:34rem;">Loading DESE targets...</pre>
      </article>
      <article class="case-card" data-animate>
        <div class="case-card-header"><span class="case-district">Field Catalog</span></div>
        <h3 class="case-card-title">Potential Enrichment Fields</h3>
        <pre id="adminDeseFields" style="white-space:pre-wrap;overflow:auto;max-height:34rem;">Loading DESE field catalog...</pre>
      </article>
    </div>
  </div>
</section>
""",
        ),
        "completed/index.html": (
            "Admin Ingest Completed | Parent Data Force",
            f"""
<section class="section" id="adminIngestCompleted" data-url="../../data/derived/ingest/review_dashboard.json">
  <div class="container">
    {section_header('Completed Queue', 'Reviewed / Completed Items', 'Visibility into documents that have been marked completed or moved to completed queues.')}
    <div class="repo-table-wrapper" data-animate>
      <table class="repo-table" id="adminCompletedTable">
        <thead><tr><th>Doc ID</th><th>State</th><th>Type</th><th>Location</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</section>
""",
        ),
        "runs/index.html": (
            "Admin Ingest Runs | Parent Data Force",
            f"""
<section class="section" id="adminIngestRuns" data-url="../../data/derived/ingest/run_history.json">
  <div class="container">
    {section_header('Ingest Runs', 'Run History and Batch Diagnostics', 'Recent ingest runs, queue sizes, and QA summary metrics.')}
    <div class="repo-table-wrapper" data-animate>
      <table class="repo-table" id="adminRunsTable">
        <thead><tr><th>Batch</th><th>Started</th><th>Docs</th><th>Parsed</th><th>Errors</th><th>New Doc Types</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</section>
""",
        ),
    }
    for rel, (title, content) in pages.items():
        write_page(base / rel, title, content, site_dir, active="updates")


def build_permalink_site(root: Path) -> dict:
    site_dir = root / "public"
    ensure_dir(site_dir)
    generated_dirs = (
        "admin-ingest",
        "calendar",
        "cases",
        "districts",
        "goals",
        "prs",
        "public-records",
        "restraint-seclusion",
        "speeches",
        "updates",
    )
    for rel in generated_dirs:
        target = site_dir / rel
        if target.exists():
            shutil.rmtree(target)
    for rel in ("sitemap.xml", "robots.txt"):
        target = site_dir / rel
        if target.exists():
            target.unlink()

    case_payload = read_json(root / "data" / "cases_timeline.json", default={})
    cases = case_payload.get("cases", [])
    updates = read_json(root / "data" / "updates.json", default={}).get("records", [])
    calendar_events = read_json(root / "data" / "calendar.json", default={}).get("events", [])
    goals = read_json(root / "data" / "goals.json", default={}).get("goals", [])
    speeches = read_json(root / "data" / "speeches.json", default={}).get("records", [])

    district_restraint_records = read_json(root / "data" / "restraint_district_rollup.json", default={}).get("records", [])
    school_restraint_records = read_json(root / "data" / "restraint_school_rollup.json", default={}).get("records", [])
    school_year_restraint_rows = read_json(root / "data" / "restraint_school_year.json", default={}).get("records", [])

    restraint_by_district = {row.get("districtCode"): row for row in district_restraint_records}
    slug_map = district_slug_map(cases)

    urls = []
    urls.extend(build_district_pages(site_dir, cases, restraint_by_district, calendar_events, updates, slug_map))
    urls.extend(build_case_pages(site_dir, cases, updates, slug_map))
    urls.append(build_calendar_page(site_dir, calendar_events))
    urls.append(build_updates_page(site_dir, updates))
    urls.append(build_goals_page(site_dir, goals))
    urls.append(build_speeches_page(site_dir, speeches))
    prs_url, prr_url = build_pr_pages(site_dir, cases)
    urls.extend([prs_url, prr_url])
    urls.extend(build_restraint_pages(site_dir, district_restraint_records, school_restraint_records, school_year_restraint_rows))
    build_admin_ingest_pages(site_dir)

    canonical_domain = read_json(root / "config" / "site.json", default={}).get("domain", "parentdataforce.com")
    sitemap_lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
    ]
    for relative in sorted(set(urls)):
        sitemap_lines.append("  <url>")
        sitemap_lines.append(f"    <loc>https://{canonical_domain}{relative}</loc>")
        sitemap_lines.append(f"    <lastmod>{date.today().isoformat()}</lastmod>")
        sitemap_lines.append("  </url>")
    sitemap_lines.append("</urlset>")
    (site_dir / "sitemap.xml").write_text("\n".join(sitemap_lines), encoding="utf-8")

    robots = f"User-agent: *\nAllow: /\nSitemap: https://{canonical_domain}/sitemap.xml\n"
    (site_dir / "robots.txt").write_text(robots, encoding="utf-8")

    stats = {
        "districtsTracked": len({c.get("districtCode") for c in cases if c.get("districtCode")}),
        "activeCases": len([c for c in cases if c.get("status") != "closed"]),
        "stateDeterminations": len([c for c in cases if "DESE" in c.get("type", "") or "PRS" in c.get("caseId", "")]),
        "appealsFiled": len(
            [
                event
                for event in case_payload.get("events", [])
                if "Appeal" in event.get("type", "") or "appeal" in event.get("title", "").lower()
            ]
        ),
    }
    write_json(root / "data" / "site_stats.json", {"generatedAt": date.today().isoformat(), "stats": stats})

    return {"pages": len(set(urls)), "stats": stats}

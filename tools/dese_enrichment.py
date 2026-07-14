from __future__ import annotations

from html import unescape
import re
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from .common import read_json, write_json


DESE_BASE = "https://profiles.doe.mass.edu"


def _district_profile_targets(district_code: str) -> list[dict]:
    return [
        {"id": f"district-general-{district_code}", "category": "general", "url": f"{DESE_BASE}/profiles/general.aspx?topNavId=1&orgcode={district_code}&orgtypecode=5"},
        {"id": f"district-people-{district_code}", "category": "people", "url": f"{DESE_BASE}/profiles/general.aspx?topNavId=1&orgcode={district_code}&orgtypecode=5&leftNavId=122"},
        {"id": f"district-relationships-{district_code}", "category": "relationships", "url": f"{DESE_BASE}/profiles/general.aspx?topNavId=1&orgcode={district_code}&orgtypecode=5&leftNavId=120"},
        {"id": f"district-students-{district_code}", "category": "student-metrics", "url": f"{DESE_BASE}/profiles/student.aspx?orgcode={district_code}&orgtypecode=5"},
        {"id": f"district-teachers-{district_code}", "category": "teacher-metrics", "url": f"{DESE_BASE}/profiles/teacher.aspx?orgcode={district_code}&orgtypecode=5"},
        {"id": f"district-finance-{district_code}", "category": "finance", "url": f"{DESE_BASE}/profiles/finance.aspx?orgcode={district_code}&orgtypecode=5"},
        {"id": f"district-assessment-{district_code}", "category": "assessment", "url": f"{DESE_BASE}/mcas/achievement_level.aspx?linkid=32&orgcode={district_code}&orgtypecode=5"},
        {"id": f"district-accountability-{district_code}", "category": "accountability", "url": f"{DESE_BASE}/accountability/report/district.aspx?linkid=30&orgcode={district_code}&orgtypecode=5"},
        {"id": f"district-dart-{district_code}", "category": "dart", "url": f"{DESE_BASE}/analysis/default.aspx?orgcode={district_code}&orgtypecode=5"},
        {"id": f"district-contracts-{district_code}", "category": "contracts", "url": f"{DESE_BASE}/profiles/general.aspx?topNavId=1&orgcode={district_code}&orgtypecode=5&leftNavId=16862"},
    ]


def _field_catalog() -> dict:
    return {
        "organization": [
            "districtCode", "districtName", "districtType", "address", "city", "state", "zip", "phone", "fax", "email", "website",
            "superintendentName", "schoolCount", "enrollment", "gradesServed", "studentTeacherRatio", "memberships", "relatedOrganizations",
            "assessmentSummary", "accountabilitySummary", "financeSummary", "reportArtifacts"
        ],
        "school": [
            "schoolCode", "schoolName", "schoolType", "address", "phone", "fax", "email", "website", "principalName", "districtCode",
            "enrollment", "gradesServed", "studentTeacherRatio", "assessmentSummary", "accountabilitySummary", "selectedPopulations", "gradeEnrollment"
        ],
        "person": [
            "displayName", "emails", "phones", "roles", "organizationIds", "schoolIds", "knownContacts", "authorityLinks", "knowledgeEvents",
            "likelyRecordsCustodianTopics", "topicOwnership", "educatorLicenseNumber", "educatorLicenseType", "educatorLicenseStatus",
            "educatorLicenseIssueDate", "educatorLicenseExpirationDate", "educatorLicenseSubjects", "educatorLicenseGradeSpan",
            "educatorLicenseRestrictions", "educatorLicensureSource", "educatorLicensureVerifiedAt"
        ],
        "metrics": [
            "enrollmentByGrade", "enrollmentByRaceEthnicity", "enrollmentByGender", "selectedPopulations", "attendance", "retention", "mobility",
            "discipline", "disciplineDaysMissed", "graduation", "dropout", "advancedCourseCompletion", "massCore", "artsCoursetaking",
            "digitalLiteracy", "teacherFTE", "teacherLicensure", "teacherSalaryTotals", "teacherAverageSalary", "staffingRetention", "staffingDemographics"
        ],
        "reports": [
            "educatorContracts", "teacherSalaryReport", "assessmentReports", "accountabilityReports", "financeReports", "oversightArtifacts", "auditArtifacts"
        ],
    }


def run_dese_enrichment_scaffold(root: Path) -> dict:
    timeline = read_json(root / "data" / "cases_timeline.json", default={})
    restraint_districts = read_json(root / "data" / "restraint_district_rollup.json", default={}).get("records", [])
    name_to_numeric = {
        str(item.get("districtName") or "").strip().upper(): str(item.get("districtCode") or "").strip()
        for item in restraint_districts
        if item.get("districtName") and item.get("districtCode")
    }
    district_codes = []
    for case in timeline.get("cases", []):
        raw = str(case.get("districtCode") or "").strip()
        if raw.isdigit() and len(raw) == 8:
            district_codes.append(raw)
            continue
        mapped = name_to_numeric.get(raw.upper())
        if mapped:
            district_codes.append(mapped)
    district_codes = sorted(set(district_codes))
    targets = []
    for code in district_codes:
        if code.isdigit() and len(code) == 8:
            targets.extend(_district_profile_targets(code))

    report_families = [
        {"id": "teacher-salaries", "url": f"{DESE_BASE}/statereport/teachersalaries.aspx", "category": "teacher-metrics"},
        {"id": "per-pupil-expenditure", "url": f"{DESE_BASE}/statereport/ppx.aspx", "category": "finance"},
        {"id": "student-discipline", "url": f"{DESE_BASE}/statereport/ssdr.aspx", "category": "student-metrics"},
        {"id": "accountability", "url": f"{DESE_BASE}/statereport/accountability.aspx", "category": "accountability"},
        {"id": "mcas", "url": f"{DESE_BASE}/statereport/mcas.aspx", "category": "assessment"},
    ]

    payload = {
        "generatedAt": timeline.get("generatedAt"),
        "districtCodes": district_codes,
        "targets": targets,
        "reportFamilies": report_families,
        "fieldCatalog": _field_catalog(),
        "status": "scaffold-only",
    }
    out_dir = root / "data" / "derived" / "dese_enrichment"
    write_json(out_dir / "targets.json", payload)
    write_json(out_dir / "field_catalog.json", {"records": _field_catalog()})
    fetch_payload = _fetch_target_snapshots(targets, report_families)
    write_json(out_dir / "fetch_results.json", fetch_payload)
    write_json(out_dir / "profile_snapshots.json", {"records": fetch_payload.get("records", [])})
    write_json(out_dir / "parsed_profiles.json", {"records": _extract_structured_profiles(fetch_payload.get("records", []))})
    return {
        "districtTargets": len(targets),
        "reportFamilies": len(report_families),
        "fetched": len(fetch_payload.get("records", [])),
        "schoolTargets": len(fetch_payload.get("schoolTargets", [])),
    }


def _fetch_target_snapshots(targets: list[dict], report_families: list[dict]) -> dict:
    records = []
    school_targets = []
    for item in targets + report_families:
        snapshot = _fetch_one(item)
        records.append(snapshot)
        if item.get("category") == "student-metrics" and snapshot.get("html"):
            school_targets.extend(_extract_school_targets(str(snapshot.get("html") or ""), item.get("url", "")))
    school_targets = _dedupe_school_targets(school_targets)
    for school in school_targets[:12]:
        for school_item in _school_profile_targets(school):
            records.append(_fetch_one(school_item))
    return {
        "generatedAt": None,
        "records": records,
        "schoolTargets": school_targets,
    }


def _school_profile_targets(school: dict) -> list[dict]:
    code = school.get("schoolCode", "")
    return [
        {"id": f"school-general-{code}", "category": "school-general", "url": school.get("generalUrl", "")},
        {"id": f"school-students-{code}", "category": "school-student-metrics", "url": school.get("studentUrl", "")},
        {"id": f"school-teachers-{code}", "category": "school-teacher-metrics", "url": school.get("teacherUrl", "")},
        {"id": f"school-assessment-{code}", "category": "school-assessment", "url": school.get("assessmentUrl", "")},
        {"id": f"school-accountability-{code}", "category": "school-accountability", "url": school.get("accountabilityUrl", "")},
    ]


def _dedupe_school_targets(records: list[dict]) -> list[dict]:
    seen = {}
    for item in records:
        code = item.get("schoolCode")
        if code and code not in seen:
            seen[code] = item
    return list(seen.values())


def _fetch_one(item: dict) -> dict:
    url = item.get("url", "")
    html = ""
    status = "ok"
    error = ""
    try:
        request = Request(url, headers={"User-Agent": "ParentDataForceBot/1.0 (+https://parentdataforce.com)"})
        with urlopen(request, timeout=20) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except (URLError, TimeoutError, ValueError) as exc:
        status = "error"
        error = str(exc)
    return {
        "id": item.get("id"),
        "category": item.get("category"),
        "url": url,
        "status": status,
        "error": error,
        "title": _extract_tag(html, "title"),
        "headings": _extract_headings(html),
        "links": _extract_links(html),
        "html": html[:12000],
    }


def _extract_tag(html: str, tag: str) -> str:
    match = re.search(fr"<{tag}[^>]*>(.*?)</{tag}>", html, flags=re.IGNORECASE | re.DOTALL)
    return _clean(match.group(1)) if match else ""


def _extract_headings(html: str) -> list[str]:
    found = re.findall(r"<(h1|h2|h3)[^>]*>(.*?)</\1>", html, flags=re.IGNORECASE | re.DOTALL)
    return [_clean(text) for _, text in found[:24] if _clean(text)]


def _extract_links(html: str) -> list[dict]:
    rows = []
    for href, text in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.IGNORECASE | re.DOTALL):
        clean_text = _clean(text)
        if not clean_text:
            continue
        rows.append({"href": href, "text": clean_text})
        if len(rows) >= 80:
            break
    return rows


def _extract_school_targets(html: str, source_url: str) -> list[dict]:
    seen = {}
    for code, name in re.findall(r'/profiles/student\.aspx\?orgcode=(\d{8})&orgtypecode=6[^>]*>(.*?)</a>', html, flags=re.IGNORECASE | re.DOTALL):
        seen[code] = {
            "schoolCode": code,
            "schoolName": _clean(name),
            "sourceUrl": source_url,
            "generalUrl": f"{DESE_BASE}/profiles/general.aspx?topNavId=1&orgcode={code}&orgtypecode=6",
            "studentUrl": f"{DESE_BASE}/profiles/student.aspx?orgcode={code}&orgtypecode=6",
            "teacherUrl": f"{DESE_BASE}/profiles/teacher.aspx?orgcode={code}&orgtypecode=6",
            "assessmentUrl": f"{DESE_BASE}/mcas/achievement_level.aspx?linkid=32&orgcode={code}&orgtypecode=6",
            "accountabilityUrl": f"{DESE_BASE}/accountability/report/school.aspx?linkid=31&orgcode={code}&orgtypecode=6",
        }
    return list(seen.values())


def _clean(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_structured_profiles(records: list[dict]) -> list[dict]:
    return [_extract_structured_profile(item) for item in records]


def _extract_structured_profile(item: dict) -> dict:
    html = item.get("html", "") or ""
    category = item.get("category")
    summary: dict = {
        "id": item.get("id"),
        "category": category,
        "url": item.get("url"),
        "title": item.get("title"),
        "organizationName": _extract_org_name(item.get("title", "")),
        "organizationCode": _extract_org_code(item.get("title", "") or item.get("url", "")),
        "emails": sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)))[:20],
        "phones": _extract_phones(html),
        "headings": item.get("headings", []),
        "summaryFields": {},
    }
    if category == "general":
        summary["summaryFields"] = {
            "superintendentName": _extract_labeled_value(html, "Superintendent"),
            "website": _extract_first_external_link(item.get("links", [])),
            "enrollmentHeadline": _extract_heading_value(item.get("headings", []), "Enrollment"),
            "achievementHeadline": _extract_heading_value(item.get("headings", []), "Achievement"),
            "selectedPopulationsHeadline": _extract_heading_value(item.get("headings", []), "Selected Populations"),
            "raceEthnicityHeadline": _extract_heading_value(item.get("headings", []), "Race and Ethnicity"),
        }
    elif category == "people":
        summary["summaryFields"] = {
            "roleLabels": _extract_role_labels(html),
            "peopleCountEstimate": len(_extract_role_labels(html)),
            "contactEmails": sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)))[:40],
        }
    elif category == "relationships":
        summary["summaryFields"] = {
            "relationshipLabels": _extract_section_links(item.get("links", []), ["Charter", "Collaborative", "School", "Program", "Membership"]),
        }
    elif category in {"student-metrics", "teacher-metrics", "assessment", "accountability", "finance", "contracts", "dart", "school-student-metrics", "school-teacher-metrics", "school-assessment", "school-accountability"}:
        summary["summaryFields"] = {
            "headlineLabels": item.get("headings", []),
            "reportLikeLinks": _extract_section_links(item.get("links", []), ["Report", "Download", "Teacher", "Student", "Accountability", "Finance", "Contract"]),
            "metricHints": _extract_metric_hints(item.get("headings", [])),
        }
    elif category == "school-general":
        summary["summaryFields"] = {
            "website": _extract_first_external_link(item.get("links", [])),
            "principalName": _extract_labeled_value(html, "Principal"),
            "gradesServedHeadline": _extract_heading_value(item.get("headings", []), "Grades"),
        }
    if category == "student-metrics":
        summary_fields = dict(summary.get("summaryFields", {}))
        summary_fields["schoolTargets"] = _extract_school_targets(html, item.get("url", ""))
        summary["summaryFields"] = summary_fields
    return summary


def _extract_org_name(title: str) -> str:
    match = re.search(r"-\s*(.*?)\s*\((\d{8})\)", title or "")
    return match.group(1).strip() if match else ""


def _extract_org_code(value: str) -> str:
    match = re.search(r"(\d{8})", value or "")
    return match.group(1) if match else ""


def _extract_phones(html: str) -> list[str]:
    found = re.findall(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}", html or "")
    return sorted(set(_clean(phone) for phone in found))[:20]


def _extract_labeled_value(html: str, label: str) -> str:
    pattern = rf"{re.escape(label)}\s*:?\s*</?[^>]*>?(.*?)<"
    match = re.search(pattern, html or "", flags=re.IGNORECASE | re.DOTALL)
    return _clean(match.group(1)) if match else ""


def _extract_heading_value(headings: list[str], token: str) -> str:
    for heading in headings:
        if token.lower() in heading.lower():
            return heading
    return ""


def _extract_first_link(links: list[dict], tokens: list[str]) -> str:
    for item in links:
        href = item.get("href", "")
        text = item.get("text", "")
        if any(token.lower() in href.lower() or token.lower() in text.lower() for token in tokens):
            return href
    return ""


def _extract_first_external_link(links: list[dict]) -> str:
    for item in links:
        href = item.get("href", "")
        if href.startswith("http") and "doe.mass.edu" not in href:
            return href
    return ""


def _extract_role_labels(html: str) -> list[str]:
    role_terms = [
        "Superintendent", "Director", "Coordinator", "Liaison", "Principal", "Business Official", "Contact", "Leader", "Administrator"
    ]
    text = _clean(html)
    labels = []
    for term in role_terms:
        labels.extend(re.findall(rf"([A-Za-z/&\- ]*{re.escape(term)}[A-Za-z/&\- ]*)", text))
    cleaned = []
    for label in labels:
        value = _clean(label)
        if 4 <= len(value) <= 120:
            cleaned.append(value)
    return sorted(set(cleaned))[:80]


def _extract_section_links(links: list[dict], tokens: list[str]) -> list[dict]:
    out = []
    for item in links:
        text = item.get("text", "")
        if any(token.lower() in text.lower() for token in tokens):
            out.append(item)
    return out[:40]


def _extract_metric_hints(headings: list[str]) -> list[str]:
    tokens = [
        "Enrollment", "Attendance", "Retention", "Mobility", "Discipline", "Graduation", "Teacher", "Administrator", "Additional Data",
        "Achievement", "Accountability", "Per Pupil", "Contracts", "Race and Ethnicity", "Selected Populations"
    ]
    results = []
    for heading in headings:
        if any(token.lower() in heading.lower() for token in tokens):
            results.append(heading)
    return results[:30]

from __future__ import annotations

from collections import Counter, deque
from datetime import date, datetime
import re
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import requests

from .common import slugify


MEETING_KEYWORDS = (
    "school committee",
    "committee meeting",
    "subcommittee",
    "public hearing",
    "joint meeting",
    "committee",
)

CRAWL_KEYWORDS = (
    "committee",
    "meeting",
    "agenda",
    "calendar",
    "posting",
    "board",
)

ACTION_KEYWORDS = (
    "meeting",
    "agenda",
    "hearing",
    "session",
    "notice",
    "subcommittee",
)

NEWS_EXCLUDE_TERMS = (
    "voters will head to the polls",
    "sworn in",
    "school news",
    "news update",
)

BAD_CRAWL_EXTENSIONS = (
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".ppt",
    ".pptx",
    ".mp3",
    ".mp4",
    ".zip",
)

DATE_HINT_RE = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{1,2}-\d{1,2})",
    re.IGNORECASE,
)
TIME_AMPM_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*([APap])\.?\s*[Mm]\.?")
TIME_24H_RE = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
YEAR_RE = re.compile(r"\b(20\d{2})\b")


def normalize_space(value: str) -> str:
    return " ".join(value.split())


def fetch_html(session: requests.Session, url: str) -> str:
    response = session.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    response.raise_for_status()
    return response.text


def normalize_href(base_url: str, href: object) -> str:
    href_text = href if isinstance(href, str) else ""
    href = href_text.strip()
    if not href:
        return ""
    if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("javascript:"):
        return ""
    normalized = urljoin(base_url, href)
    normalized = urldefrag(normalized).url
    return normalized


def should_crawl_url(url: str, allowed_hosts: set[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc not in allowed_hosts:
        return False
    lower = url.lower()
    return not lower.endswith(BAD_CRAWL_EXTENSIONS)


def crawl_candidate_links(soup: BeautifulSoup, page_url: str, depth: int) -> list[str]:
    links = []
    for anchor in soup.find_all("a", href=True):
        href = normalize_href(page_url, anchor.get("href") or "")
        if not href:
            continue
        text = normalize_space(anchor.get_text(" "))
        probe = f"{text} {href}".lower()
        if depth == 0 or any(k in probe for k in CRAWL_KEYWORDS):
            links.append(href)
    return links


def crawl_source_pages(source_urls: list[str], max_depth: int = 2, max_pages: int = 18) -> tuple[list[dict], dict]:
    queue: deque[tuple[str, int, str]] = deque()
    visited: set[str] = set()
    pages: list[dict] = []
    errors: list[dict] = []

    normalized_sources: list[str] = []
    for raw_url in source_urls:
        normalized = normalize_href(raw_url, raw_url)
        if normalized:
            normalized_sources.append(normalized)
            parsed = urlparse(normalized)
            normalized_sources.append(f"{parsed.scheme}://{parsed.netloc}/")

    normalized_sources = sorted(set(normalized_sources))
    allowed_hosts = {urlparse(url).netloc for url in normalized_sources if url}
    for url in normalized_sources:
        if url:
            queue.append((url, 0, "seed"))

    session = requests.Session()
    while queue and len(visited) < max_pages:
        current, depth, via = queue.popleft()
        if current in visited:
            continue
        visited.add(current)

        try:
            html = fetch_html(session, current)
        except requests.RequestException as exc:
            errors.append({"url": current, "depth": depth, "error": str(exc)})
            continue

        pages.append({"url": current, "depth": depth, "via": via, "html": html})
        if depth >= max_depth:
            continue

        soup = BeautifulSoup(html, "html.parser")
        for next_url in crawl_candidate_links(soup, current, depth):
            if next_url in visited:
                continue
            if not should_crawl_url(next_url, allowed_hosts):
                continue
            queue.append((next_url, depth + 1, current))

    return pages, {"errors": errors, "visited": sorted(visited), "allowedHosts": sorted(allowed_hosts)}


def iter_anchor_candidates(soup: BeautifulSoup, page_url: str) -> list[dict]:
    rows: list[dict] = []
    for anchor in soup.find_all("a", href=True):
        text = normalize_space(anchor.get_text(" "))
        if not text:
            continue
        parent = normalize_space(anchor.parent.get_text(" ", strip=True) if anchor.parent else "")
        href = normalize_href(page_url, anchor.get("href") or "")
        rows.append({"text": text, "context": parent, "href": href or page_url, "kind": "anchor"})
    return rows


def iter_block_candidates(soup: BeautifulSoup, page_url: str) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for node in soup.select("li, tr, p, div"):
        text = normalize_space(node.get_text(" ", strip=True))
        if len(text) < 12 or len(text) > 320:
            continue
        lower = text.lower()
        if not DATE_HINT_RE.search(lower):
            continue
        if not any(keyword in lower for keyword in MEETING_KEYWORDS):
            continue
        signature = slugify(text)
        if signature in seen:
            continue
        seen.add(signature)

        first_link = node.find("a", href=True)
        href = page_url
        if first_link:
            href = normalize_href(page_url, first_link.get("href") or "") or page_url
        rows.append({"text": text, "context": "", "href": href, "kind": "block"})
    return rows


def parse_time_token(text: str) -> tuple[int, int, bool]:
    ampm = TIME_AMPM_RE.search(text)
    if ampm:
        hour = int(ampm.group(1))
        minute = int(ampm.group(2) or "0")
        half = ampm.group(3).lower()
        if half == "p" and hour < 12:
            hour += 12
        if half == "a" and hour == 12:
            hour = 0
        return hour, minute, True
    h24 = TIME_24H_RE.search(text)
    if h24:
        return int(h24.group(1)), int(h24.group(2)), True
    return 0, 0, False


def extract_years(text: str) -> set[int]:
    years: set[int] = set()
    for raw in YEAR_RE.findall(text or ""):
        try:
            year = int(raw)
        except ValueError:
            continue
        if 2000 <= year <= 2100:
            years.add(year)
    return years


def parse_date(text: str, today: date) -> tuple[datetime | None, str]:
    if not DATE_HINT_RE.search(text):
        return None, "no-date-hint"
    try:
        dt = date_parser.parse(text, fuzzy=True, ignoretz=True)
    except (ValueError, OverflowError):
        return None, "parse-failed"
    if dt.year < 2020 or dt.year > 2035:
        return None, "year-out-of-range"
    if dt.date() < today:
        return None, "past-date"

    hour, minute, has_time = parse_time_token(text)
    return datetime(dt.year, dt.month, dt.day, hour, minute), "has-time" if has_time else "all-day"


def score_candidate(
    text: str,
    context: str,
    page_url: str,
    has_time: bool,
    has_year: bool,
    kind: str,
) -> float:
    whole = f"{text} {context}".lower()
    score = 0.0

    if any(k in whole for k in MEETING_KEYWORDS):
        score += 0.4
    if DATE_HINT_RE.search(whole):
        score += 0.15
    if has_year:
        score += 0.2
    if has_time:
        score += 0.15
    if kind == "block":
        score += 0.1
    else:
        score += 0.05
    if "agenda" in whole or "posting" in whole:
        score += 0.1
    if any(k in page_url.lower() for k in CRAWL_KEYWORDS):
        score += 0.1
    if "school committee" in whole and not any(k in whole for k in ACTION_KEYWORDS):
        score -= 0.25
    if len(text) > 150:
        score -= 0.15
    if "minutes" in whole and "meeting" not in whole:
        score -= 0.15
    if any(term in whole for term in NEWS_EXCLUDE_TERMS):
        score -= 0.5

    return max(0.0, min(score, 1.0))


def extract_meetings_for_district_detailed(
    district_code: str,
    source_urls: list[str],
    timezone: str,
    min_confidence: float = 0.55,
    review_confidence: float = 0.35,
) -> dict:
    today = date.today()
    events: dict[str, dict] = {}
    review: list[dict] = []
    rejected = Counter()

    pages, crawl_meta = crawl_source_pages(source_urls)

    candidate_count = 0
    for page in pages:
        soup = BeautifulSoup(page["html"], "html.parser")
        candidates = [*iter_anchor_candidates(soup, page["url"]), *iter_block_candidates(soup, page["url"])]

        for candidate in candidates:
            text = candidate["text"]
            context = candidate["context"]
            kind = candidate["kind"]
            href = candidate["href"]
            content = f"{text} {context}".strip()
            lower_content = content.lower()

            if any(term in lower_content for term in NEWS_EXCLUDE_TERMS):
                rejected["excluded-news"] += 1
                continue

            candidate_count += 1
            dt, parse_reason = parse_date(content, today)
            if not dt:
                rejected[parse_reason] += 1
                continue

            has_time = parse_reason == "has-time"
            has_year = str(dt.year) in content
            confidence = score_candidate(
                text=text,
                context=context,
                page_url=page["url"],
                has_time=has_time,
                has_year=has_year,
                kind=kind,
            )

            title = text if len(text) >= 8 else context[:120].strip()
            if not title:
                title = "School Committee Meeting"
            if len(title) > 140:
                rejected["title-too-long"] += 1
                continue

            normalized_href = normalize_href(page["url"], href) or page["url"]

            href_years = extract_years(normalized_href)
            content_years = extract_years(content)
            all_years = href_years | content_years
            href_lower = normalized_href.lower()

            if href_lower.endswith(".pdf") and href_years and max(href_years) < today.year:
                rejected["historic-pdf"] += 1
                continue
            if all_years and max(all_years) < today.year:
                rejected["historic-year"] += 1
                continue

            if all_years and dt.year not in all_years and max(all_years) >= today.year:
                candidate_year = max(all_years)
                if candidate_year <= 2035:
                    dt = datetime(candidate_year, dt.month, dt.day, dt.hour, dt.minute)

            payload = {
                "id": slugify(f"{district_code}-{dt.date().isoformat()}-{title}"),
                "slug": slugify(f"{district_code}-{dt.date().isoformat()}-{title}"),
                "title": title,
                "type": "meeting",
                "districtCode": district_code,
                "jurisdiction": "US-MA",
                "startAt": dt.isoformat(),
                "allDay": not has_time,
                "timezone": timezone,
                "source": {
                    "method": "web-scrape",
                    "url": normalized_href,
                    "page": page["url"],
                    "candidateType": kind,
                    "confidence": round(confidence, 2),
                },
            }

            if confidence < min_confidence:
                rejected["low-confidence"] += 1
                if confidence >= review_confidence:
                    review.append(
                        {
                            "districtCode": district_code,
                            "title": title,
                            "startAt": dt.isoformat(),
                            "confidence": round(confidence, 2),
                            "url": normalized_href,
                            "page": page["url"],
                            "candidateType": kind,
                        }
                    )
                continue

            key = f"{district_code}|{dt.isoformat()}|{slugify(title)}"
            existing = events.get(key)
            if not existing or payload["source"]["confidence"] > existing["source"]["confidence"]:
                events[key] = payload

    output = list(events.values())
    output.sort(key=lambda x: x["startAt"])
    review.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    diagnostics = {
        "districtCode": district_code,
        "pagesFetched": len(pages),
        "candidateCount": candidate_count,
        "acceptedCount": len(output),
        "reviewCount": len(review),
        "rejectedByReason": dict(rejected),
        "visitedPages": [p["url"] for p in pages],
        "crawl": crawl_meta,
    }
    return {"events": output, "review": review, "diagnostics": diagnostics}


def extract_meetings_for_district(
    district_code: str,
    source_urls: list[str],
    timezone: str,
    min_confidence: float = 0.55,
) -> list[dict]:
    result = extract_meetings_for_district_detailed(
        district_code=district_code,
        source_urls=source_urls,
        timezone=timezone,
        min_confidence=min_confidence,
    )
    return result["events"]

# Scraping System Advisor

**Role:** Govern the consolidated scraping system — scraper development, the documents table, FTP upload pipeline, strategy store, and the interactive CLI.

## Responsibilities

1. **Scraper architecture** — all scrapers follow the `BaseScraper` contract in `scraper/core/scraper.py`. Every scraper runs standalone AND via registry/CLI. New scrapers copy `scraper/scrapers/_template.py`.

2. **Document tracking** — every document discovered, downloaded, or uploaded flows through the `documents` table. Use `ScrapedDocument` dataclass (`scraper/core/base.py`) as the universal record. Never create ad-hoc document tracking.

3. **Document classification** — documents MUST be classified by:
   - `media_type`: PDF, HTML, video, image, spreadsheet, text, archive, audio, other
   - `document_class`: meeting_agenda, meeting_minutes, meeting_packet, policy_manual, budget, annual_report, school_handbook, sepac_info, prr_response, des_report, correspondence, testimony, legal_filing, media_coverage, other
   - `source_system`: dese, apptegy, civicengage, boarddocs, youtube, custom_html, manual
   
   If a new type is needed, add it to the constants in `scraper/core/base.py` and to the DB schema.

4. **FTP upload pipeline** — documents progress through states: `discovered → downloaded → verified → uploaded`. The `FTPUploader` (`scraper/core/ftp.py`) handles upload with automatic directory structure (`/public_html/documents/<district>/<year>/<class>/filename`).

5. **Strategy learning** — every scraper MUST record successes and failures in the `StrategyStore` (`scraper/core/strategy.py`). When encountering a new page, query the store for proven patterns before writing new scraping logic. Strategies accumulate in `scraper/strategies/patterns.yaml`.

6. **Registry discipline** — scrapers auto-register via the `@register_scraper` decorator. The `ScraperRegistry` discovers all `.py` files in `scraper/scrapers/` on CLI startup. Never manually maintain a scraper list.

7. **CLI as primary interface** — the interactive terminal (`python -m scraper.cli`) is the canonical way to run scrapers, browse documents, upload to FTP, and query strategies. Individual scrapers can still run standalone (`python scrapers/dese_all.py`).

8. **Schema management** — the authoritative documents table schema lives at `scraper/migration/documents_table.sql`. Changes must be reflected in `scraper/core/db.py`'s `ensure_table()` method and vice versa.

9. **Rate limiting** — all HTTP requests go through `self._get()` (rate-limited, retry-enabled). Default 3-second delay between requests. Override per scraper if needed.

10. **Dedup by checksum** — before downloading, check if a document with matching SHA-256 checksum already exists. Skip duplicates (status: `skipped_duplicate`). The `DocumentDB.find_by_checksum()` method handles this.

## When to Consult This Advisor

- Adding a new scraper for a district or data source
- Changing the document classification system
- FTP upload issues or pipeline questions
- The interactive CLI isn't behaving as expected
- Strategy store queries or recording new patterns
- Schema changes to the documents table

## Anti-Patterns (DO NOT)

- Creating a scraper outside the `scraper/scrapers/` directory
- Skipping the registry — new scrapers must use `@register_scraper`
- Ad-hoc document tracking — always use `ScrapedDocument` + `DocumentDB`
- Hardcoding FTP paths — use `FTPUploader.upload_document()` with automatic structure
- Silent scraper failures — always record errors in `ScrapeResult.errors` and strategies
- Skipping strategy recording — every new pattern gets recorded for future use
- Raw `requests.get()` — use `self._get()` for rate limiting and retries

## Key Files

- `scraper/core/base.py` — `ScrapedDocument` dataclass + classification constants
- `scraper/core/scraper.py` — `BaseScraper` + `ScrapeResult`
- `scraper/core/registry.py` — scraper discovery and execution
- `scraper/core/db.py` — `DocumentDB` CRUD operations
- `scraper/core/ftp.py` — `FTPUploader` with automatic directory structure
- `scraper/core/strategy.py` — `StrategyStore` for learned patterns
- `scraper/cli.py` — interactive terminal
- `scraper/scrapers/` — individual scraper modules
- `scraper/strategies/patterns.yaml` — accumulated scraping knowledge
- `scraper/migration/documents_table.sql` — authoritative DB schema

## Scraper Development Checklist

When building a new scraper:

- [ ] Copy `scraper/scrapers/_template.py`
- [ ] Set unique `name`, `display_name`, `source_system`, `help_text`
- [ ] Implement `run()` returning `ScrapeResult`
- [ ] Use `self._get()` for HTTP, `self._download_file()` for binaries
- [ ] Create `ScrapedDocument` objects with full classification
- [ ] Insert documents via `DocumentDB.insert()`
- [ ] Record strategies in `StrategyStore`
- [ ] Test standalone: `python scrapers/<name>.py`
- [ ] Test via CLI: `run <name>` in interactive terminal
- [ ] If new classification values needed, update `base.py` constants + migration SQL

## Update History

| Date | Change |
|------|--------|
| 2026-07-14 | Created — consolidated scraping system v1 |

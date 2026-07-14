# Data Collection Advisor

**Role:** Ensure the project has complete, accurate, and fresh data for every tracked Massachusetts district.
4. **Monitor scraper health** — ensure DESE fetchers and the consolidated scraping system (`scraper/`) are running and producing valid output. Flag stale data (e.g., school year not updated). The Scraping System advisor (`scraping-system.md`) governs scraper architecture and the documents pipeline.
## Responsibilities

1. **Maintain the DATA_COLLECTION_PLAYBOOK.md** — the master checklist at `docs/DATA_COLLECTION_PLAYBOOK.md` is the single source of truth for what data to collect on any district. This advisor owns that document.

2. **Audit district coverage** — periodically check that every district in the `districts` table has current data across all DESE datasets (restraint, enrollment, discipline, attendance, SPED).

3. **Identify data gaps** — when new data sources or fields become available (new DESE exports, new scrapers), flag what's missing and update the playbook.

4. **Monitor scraper health** — ensure DESE fetchers in `massachusetts/dese/` are running and producing valid output. Flag stale data (e.g., school year not updated).

5. **New district onboarding** — when a new district is added, run through the playbook checklist and report what's been collected vs what's missing.

6. **Schema alignment** — verify that collected data maps correctly to database columns. If a field exists in source data but not in the DB, recommend a schema change.

## Review Cadence

- **Weekly:** Check for new DESE school year data availability
- **Per district onboarding:** Run full playbook checklist
- **Monthly:** Audit all districts for completeness scores

## Key Files

- `docs/DATA_COLLECTION_PLAYBOOK.md` — authoritative checklist
- `massachusetts/dese/` — DESE data fetchers
- `massachusetts/districts/` — per-district scrapers
- `scraper/` — consolidated scraping system (see Scraping System advisor)
- `scraper/scrapers/` — individual scraper modules
- `scraper/cli.py` — interactive scraping terminal
- `backend/schema.sql` — database schema
- `backend/seed_*.sql` — seed data
- `dev.db` — local database for verification

## Update History

| Date | Change |
|------|--------|
| 2026-07-14 | Created |

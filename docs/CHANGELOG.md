# Changelog

## 2026-03-20

- Added rules-based skill modules:
  - `skills/evidence_to_timeline.py`
  - `skills/status_transition.py`
  - `skills/updates_hybrid.py`
  - `skills/permalink_build.py`
  - `skills/qa_guard.py`
- Hardened meeting scrape engine with bounded crawl, block-level extraction, confidence scoring, and diagnostics outputs.
- Added meeting diagnostics artifacts: `data/meeting_scrape_report.json` and `data/meeting_review_candidates.json`.
- Added resilient speech ingestion retry strategy and fetch diagnostics in `data/speeches_fetch_report.json` with cache fallback support.
- Expanded permalink rendering with richer district/case/list pages and cross-links.
- Reworked case file pages: timeline summary card replaces related card in top row, with separate Related and Notes section.
- Reworked calendar page with visible month calendar and separated governance/deadline event lanes.
- Reworked restraint pages to raw-first presentation, showing raw source values, exact raw rates where known, and separate estimate bounds for suppressed rows.
- Expanded restraint outputs with raw fields and additional derived calculations (injuries/restraint and restraints/student ratios).
- Replaced restraint ingestion with `.eml` attachment-aware source pipeline; workbook provenance and reference attachments now recorded in `data/restraint_manifest.json`.
- Reworked restraint rollups to remove `Public Schools Total` from district/school entities and added dedicated statewide totals dataset.
- Added dual ranking lenses (all DESE rows minus summary + traditional-comparable lens) with median/p95 context.
- Rebuilt district and school restraint profile pages with explicit "Important Calculations" sections (latest-year snapshot, YoY shifts, peak year, concentration, and rank context).
- Switched publish target to `public/` only, including generated route pages plus synced root static assets, `data/`, and case artifacts.
- Consolidated restraint/seclusion into a single-page explorer at `public/restraint-seclusion/index.html`, powered by JSON (`data/restraint_explorer.json`) instead of thousands of district/school subpages.
- Added client-side pagination controls for the school-year table on the single restraint explorer page.
- Removed obsolete root-level generated route folders/files so deployable output is cleanly scoped to `public/`.
- Added ingest/admin foundation: hidden admin ingest pages, queue/review datasets, first deterministic parser framework, shared JSON review state, and CLI skeleton.
- Added master long-term backlog and ruleset planning artifacts (`data/master_plan_todo.json`, `wiki/MASTER-PLAN.md`, `wiki/INGEST-RULES.md`).
- Added configurable ingest rules files under `config/ingest_rules/` with doc-family and situation rule groups, plus pipeline rule loading outputs.
- Switched CLI completed action to state-only workflow by default (no automatic file move).
- Added build orchestrator `build_site.py`.
- Added config/data seeds for districts, site config, goals, events, updates, and speech sources.
- Added dynamic homepage stat hydration from `data/site_stats.json`.
- Added wiki documentation set under `wiki/`.

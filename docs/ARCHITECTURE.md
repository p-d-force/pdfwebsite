# Architecture

The build is rules-based and file-driven.

## Pipeline

1. `build_site.py` seeds missing config/data files.
2. `skills/ingest/orchestrate.py` discovers docs from `intake/` and `cases/*/*/intake/`, bootstraps entity graph data, and emits admin review datasets.
3. `skills/restraint_analytics.py` ingests DESE restraint files from `intake/` into `data/raw/dese-restraint/` and emits rollups.
4. `skills/evidence_to_timeline.py` converts case metadata files under `cases/*/*/metadata.json` into normalized case/timeline datasets.
5. `skills/status_transition.py` computes deadline state using business-day logic.
6. `skills/meeting_scrape.py` scrapes district meeting pages and emits meeting events + manual review queue.
7. `build_site.py` fetches speech feed entries from YouTube RSS source(s).
8. `skills/updates_hybrid.py` merges manual + auto-derived updates.
9. `build_site.py` merges meetings, deadlines, and manual governance events into one calendar dataset.
10. `skills/permalink_build.py` generates public pages plus hidden admin ingest pages.
11. `skills/qa_guard.py` verifies key output artifacts.

## Primary data outputs

- `data/cases_timeline.json`
- `data/case_status.json`
- `data/meetings.json`
- `data/meeting_manual_queue.json`
- `data/updates.json`
- `data/calendar.json`
- `data/restraint_school_year.json`
- `data/restraint_district_rollup.json`
- `data/restraint_school_rollup.json`
- `data/site_stats.json`
- `data/build_manifest.json`
- `data/qa_report.json`

## Runtime conventions

- Jurisdiction is explicit (`US-MA` by default).
- Business-day calculations are jurisdiction-aware.
- Suppression values from DESE restraint files are represented as range + midpoint.
- All outputs are deterministic for a given input snapshot.

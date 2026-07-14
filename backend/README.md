# Backend Scaffold (Local Only)

This folder contains a backend-ready MySQL schema and starter seed data.

- `schema.sql`: normalized tables for districts, cases, events, documents, links, and ingest dedupe registries.
- `seed.sql`: minimal Attleboro seed records to validate relationships locally.
- `export_metadata_sql.py`: exports current case metadata JSON into SQL inserts.
- `seed_from_metadata.sql`: generated SQL from `cases/*/*/metadata.json`.

## Not deployed yet

This is intentionally a local scaffold only. No deployment or runtime backend wiring has been performed.

## Local import (phpMyAdmin)

1. Create a new database (example: `pdf_case_archive_dev`).
2. Import `backend/schema.sql`.
3. Import either `backend/seed.sql` (minimal) or `backend/seed_from_metadata.sql` (generated full local snapshot).

## Regenerate metadata SQL

Run:

`python backend/export_metadata_sql.py`

## Next backend steps (when ready)

- Add a migration for `recordings_index.json` entries into `documents`.
- Add API endpoints for case list, case detail, and repository search.
- Replace demo form handlers with secured insert workflows.

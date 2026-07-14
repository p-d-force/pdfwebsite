# Database Map

This document maps the current JSON/platform concepts into MariaDB tables suitable for the current hosting environment.

## Existing Backend Scaffold

Current scaffold in `backend/schema.sql` already covers:

- districts
- cases
- case_events
- documents
- case_links
- ingest_message_ids
- ingest_file_hashes

## Tables Needed Next

### Auth and Security

- `admin_users`
- `admin_sessions`
- `admin_roles`
- `admin_user_roles`
- `admin_audit_log`
- `csrf_tokens` (or session-bound token storage)

### Entity Graph

- `organizations`
- `schools`
- `people`
- `person_roles`
- `investigations`
- `initiatives`
- `plans`
- `issues`
- `tasks`
- `entity_links`
- `knowledge_events`

### Ingest and Review

- `ingest_documents`
- `ingest_extracts`
- `ingest_suggestions`
- `review_tasks`
- `review_field_decisions`
- `review_manual_links`
- `field_provenance`
- `field_history`
- `field_snapshots`
- `schema_expansion_queue`
- `ingest_runs`

### Notes and Intelligence

- `notes`
- `note_bundles`
- `note_bundle_members`
- `note_templates`
- `entity_notes`

### Redaction

- `redaction_profiles`
- `redaction_jobs`
- `redaction_previews`
- `redacted_artifacts`

### DESE Enrichment

- `dese_targets`
- `dese_fetch_snapshots`
- `dese_profile_summaries`
- `dese_school_targets`
- `metric_snapshots`
- `report_artifacts`
- `licensure_records`

## Relationship Strategy

Use stable external IDs alongside numeric primary keys.

- numeric PKs for joins and MariaDB performance
- stable external IDs for imports/exports and cross-system references

Examples:

- `external_id = case:SPR26-0842`
- `external_id = doc:sha256:...`
- `external_id = person:...`

## Migration Strategy

### Stage 1

- export current JSON into MariaDB mirror tables
- do not switch write authority yet

### Stage 2

- move admin writes to MariaDB tables
- keep JSON export generation for public views

### Stage 3

- selectively retire JSON as write store while preserving JSON as export/read model where useful

## Recommended Priority Tables

Build in this order:

1. `admin_users`, `admin_sessions`, `admin_audit_log`
2. `organizations`, `schools`, `people`, `person_roles`
3. `ingest_documents`, `ingest_extracts`, `ingest_suggestions`, `review_tasks`
4. `review_field_decisions`, `review_manual_links`, `field_provenance`
5. `notes`, `note_bundles`, `redaction_jobs`
6. `metric_snapshots`, `report_artifacts`, `licensure_records`

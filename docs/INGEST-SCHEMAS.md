# Ingest Schemas

Primary first-build artifacts:

- `data/entities/cases/*.json`
- `data/entities/orgs/*.json`
- `data/entities/people/*.json`
- `data/entities/documents/*.json`
- `data/entities/messages/*.json`
- `data/entities/review_tasks/*.json`
- `data/entities/ingest_batches/*.json`
- `data/derived/ingest/document_extracts.json`
- `data/derived/ingest/document_suggestions.json`
- `data/derived/ingest/ingest_queue.json`
- `data/derived/ingest/review_dashboard.json`
- `data/derived/ingest/schema_expansion_queue.json`

Deterministic extraction remains canonical. Suggestions are review-only.

## Planned schema expansion

The next schema layer should add first-class structures for:

- field provenance
- field history entries
- field snapshots
- DESE district profile snapshots
- DESE school profile snapshots
- role assignments
- licensure records
- report artifacts and audit/oversight artifacts
- metric snapshots
- knowledge events
- notes, note bundles, reusable note blocks, and red flag notes
- redaction jobs, redaction previews, and redacted artifacts

## Field model direction

Important fields should gradually move from plain scalar values toward structured objects that can hold:

- current value
- source URL or source path
- source document/entity ID
- source text snippet/span
- extraction method
- confidence
- approval history
- history log
- periodic snapshots

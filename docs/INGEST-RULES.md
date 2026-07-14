# Ingest Rules

The ingest system supports file-based rules that can be loaded before deterministic parsing, AI suggestion generation, metadata analysis, and publish decisions.

## Rule Families

- document family rules: document-type-specific defaults and constraints
- situation rules: cross-cutting conditions such as OCR-needed, metadata red flags, tabular docs, public sensitivity, and same-thread linking

## Registry

The rule registry lives at:

- `config/ingest_rules/registry.json`

The registry points to both rule groups:

- `config/ingest_rules/doc_families/*.json`
- `config/ingest_rules/situations/*.json`

## Matching Model

Rules are intended for if/then logic.

Each rule file may specify:

- `match` conditions
- `then` actions
- optional `aiPromptHints`
- optional `metadataChecks`
- optional `publishDefaults`

## Planned Uses

- require OCR when PDF appears scanned
- require table extraction when document appears tabular
- tighten deadline extraction expectations for determinations and PRS docs
- change prompt instructions for emails vs public records vs spreadsheets
- mark public visibility defaults conservatively
- raise review priority when metadata red flags are present

## Expanded planned uses

- shape AI prompts based on the matched document family and situation rules
- require provenance capture for fields extracted from sensitive sources
- trigger DESE profile/report enrichment for districts, schools, staff roles, and report artifacts
- control low-risk autofill staging and mass approval eligibility
- change redaction defaults based on source attribution and document sensitivity
- decide whether approved ingest findings stay internal by default or require publish review

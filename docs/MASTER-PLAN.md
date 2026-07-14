# Master Plan

This file is the long-term product and engineering master plan for Parent Data Force. It complements `data/master_plan_todo.json` with a human-readable overview.

## Strategic Goals

- Build a durable document ingest and review system that handles emails, PRR docs, PRS docs, determinations, spreadsheets, correspondence, and attachments.
- Keep deterministic extraction canonical while using AI as a constrained suggestion layer.
- Support a full entity graph linking investigations, initiatives, plans, contacts, organizations, people, documents, messages, events, issues, tasks, and review tasks.
- Add a hidden admin review interface and local CLI/PowerShell workflow that operate on the same JSON-backed state.
- Add full metadata analysis and red-flag reporting on every intake file.
- Make rule sets configurable from files so different document types and situations can change extraction and AI behavior without rewriting code each time.
- Track provenance for every important field, including source URL/path, source document/entity ID, source snippet, extraction method, confidence, and approval history.
- Build comprehensive district, school, people, and report profiles using DESE district/school profiles and related statewide reports.
- Add notes, context, chronology, intelligence, red flags, and redaction workflows as first-class review features.

## Current State

- Queue discovery exists for `intake/` and `cases/*/*/intake/`.
- Entity graph bootstrap exists for cases, orgs, people, documents, messages, review tasks, and ingest batches.
- First-pass deterministic parsers exist for email, public-records, PRS, determinations, spreadsheets, correspondence, and generic attachments.
- Hidden admin pages exist in `public/admin-ingest/`.
- CLI exists in `ingest_cli.py`.
- Approved ingest events can feed into case timelines and updates.
- A file-based rule registry and starter rule sets exist in `config/ingest_rules/` and are emitted to ingest datasets.

## Still Planned

### Field Provenance, Histories, and Snapshots

- Every important field should be able to store current value, provenance, history, and periodic snapshots.
- Provenance should include source URL/path, source document/entity ID, exact supporting snippet, extraction method, confidence, and approval history.
- This applies to organization, people, investigation, issue, event, report, metric, and note-related fields.

### DESE Enrichment

- Treat DESE district and school profiles as a dedicated enrichment pipeline.
- Ingest general district/school pages, people/role pages, relationship/membership pages, student metrics, teacher/staff metrics, assessment/accountability, finance/contracts, and related report/audit artifacts.
- Use direct DESE facts to enrich entities and keep inferred intelligence in a review-only layer.

### People, Contacts, and Knowledge Graph

- Build comprehensive people profiles with roles, history, known contacts, contact networks, and source-backed role intelligence.
- Track who contacted whom, who was CC'd, who likely has records, and who is aware of an event or issue.
- Add educator licensure fields including number, type, status, dates, scope, restrictions, and provenance.

### Metadata Analysis

- Extract file-system metadata, format-specific metadata, structural metadata, and suspicious metadata patterns.
- Emit sidecar metadata reports next to source files.
- Aggregate metadata reports centrally.
- Flag red flags such as hidden content, encryption, revision anomalies, timestamp mismatches, scrubbed metadata, and embedded objects.

### Notes, Context, and Intelligence

- Add per-file notes, multi-file bundles, reusable note blocks, red flag notes, entity notes, and chronology notes.
- Keep factual extraction separate from reviewer notes and inferred intelligence.
- Allow reusable tags and note blocks for recurring patterns.

### Rules Engine

- Use file-based rule sets for document families and situations.
- Match rules in if/then style before AI is invoked.
- Let rules change prompts, extraction expectations, red-flag sensitivity, OCR/table handling, and publish defaults.
- Extend rules to govern DESE enrichment, notes, provenance-aware prompts, redaction defaults, and low-risk autofill.

### Browser-Side Review Writes

- Add local JSON write support from the admin review page.
- Let reviewers accept/reject fields, set overrides, add links, and adjust states without leaving the browser.
- Support one-click approval for staged low-risk autofill suggestions with individual override options.

### Security

- Add password protection before any admin deployment.
- Keep admin and internal ingest datasets separate from public deployment when needed.

### Hosted Migration

- Migrate cautiously from local JSON admin workflows into a cPanel/PHP/MariaDB hosted system.
- Use MariaDB for secure admin writes, auth, sessions, notes, review actions, and audit logs.
- Keep public pages static-first and driven by generated exports until the hosted admin is stable.
- Respect shared-hosting limits by keeping OCR, heavy email analysis, and large enrichment jobs local or offloaded.

### Parser and OCR Expansion

- Add PDF and DOCX text extraction.
- Add OCR only when needed.
- Add table extraction when documents are table-heavy.

### Publishing Safety

- Approved ingest events should default to internal visibility.
- Public release should require explicit publishability review or toggle.

### Redaction and Anonymization

- Add five redaction policy levels plus manual field selection.
- Preview redactions before applying them.
- Generate redacted outputs in a parallel tree.
- Quarantine unnecessary originals in a separate archive/pending-delete location.
- Track source attribution such as Parent Data Force sourced, community supplied, or named contributor.

### Homepage and Public UX

- Move the calendar to the top of the homepage.
- Make deadlines highly visible with urgent styling and dynamic countdown timers.
- Collapse/minimize the hero as soon as scrolling begins.
- Reduce intro copy and keep the homepage closer to the data.

## Sources of Truth

- Human-readable plan: `wiki/MASTER-PLAN.md`
- Structured backlog: `data/master_plan_todo.json`
- Ingest architecture docs: `wiki/INGEST-*.md`
- Rule-set files: `config/ingest_rules/`
- Hosting migration: `wiki/HOSTING-MIGRATION-PLAN.md`
- DB mapping: `wiki/DB-MAP.md`
- Admin security roadmap: `wiki/ADMIN-SECURITY-ROADMAP.md`

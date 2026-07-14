# Ingest Admin Architecture

This repo now includes a hidden ingest/admin foundation for long-term document review.

## Layers

1. Source layer: raw files in `intake/` and `cases/*/*/intake/`
2. Graph layer: canonical entities in `data/entities/`
3. Extract layer: deterministic parser outputs in `data/derived/ingest/`
4. Suggestion layer: heuristic/AI-ready suggestions in `data/derived/ingest/document_suggestions.json`
5. Review layer: review tasks, queue states, overrides, and links
6. Publish layer: future approved event merge into public case datasets

## Current first-build scope

- Queue discovery from both intake roots
- Entity bootstrap for cases, orgs, docs, messages, people, and review tasks
- Deterministic parsers for email, PRR/public-records, PRS, determinations, spreadsheets, and generic attachments
- Hidden admin pages in `public/admin-ingest/`
- Shared JSON-backed state for both browser UI and CLI
- Configurable ingest rule sets in `config/ingest_rules/` loaded into `data/derived/ingest/rule_sets.json`

## Safety rules

- Deterministic extraction is canonical
- Suggestion layer cannot overwrite deterministic facts automatically
- Unreviewed ingest data does not affect public timelines yet
- File movement should prefer completed queues over deletion

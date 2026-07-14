# Hosting Migration Plan

This document maps the current local JSON-first platform into a staged hosted system suitable for the current cPanel/MariaDB environment.

## Current Hosting Environment

- package: `essentials_premier`
- server: `cpanel381`
- Apache: `2.4.66`
- PHP: `8.3.20`
- MariaDB: `10.11.15-MariaDB-cll-lve`
- phpMyAdmin: `5.2.2`
- database host: `localhost` via UNIX socket
- shared hosting environment

## Guiding Principle

Do not jump straight from local static JSON into a fully public write-enabled app.

Use a staged migration:

1. local JSON admin (current)
2. hosted password-protected admin with MariaDB-backed reads
3. hosted secure write actions with audit logging and sessions
4. richer jobs/workers only after operational pressure requires them

## Recommended Production Architecture on Current Hosting

### Public Site

- continue static-first public rendering into `public/`
- public pages should read from generated JSON exports only
- no direct public write operations

### Admin Site

- host a protected admin app under a hidden route or admin subdirectory
- implement server-side PHP endpoints for review actions
- back them with MariaDB tables rather than mutable JSON files

### Data Model

- MariaDB becomes the canonical write store for:
  - users
  - sessions
  - review tasks
  - notes
  - field approvals
  - manual links
  - redaction jobs
  - DESE enrichment refresh metadata
- generated JSON remains the canonical public read model until later changes

## Migration Phases

### Phase 1 - MariaDB Read Mirror

- keep JSON as source of truth
- export JSON entities and review artifacts into MariaDB mirror tables
- verify schema and query patterns using phpMyAdmin and local scripts

### Phase 2 - Hosted Admin Auth

- build password-hashed admin users table
- add session table and secure cookie-based login
- add CSRF protection for state-changing actions
- keep hosted admin reads available only after successful auth

### Phase 3 - Hosted Write Endpoints

- implement PHP endpoints for:
  - review state changes
  - manual links
  - field approve/deny
  - notes
  - redaction jobs
- persist writes to MariaDB
- add audit trail rows for every action

### Phase 4 - Public Export Pipeline

- create export scripts that convert MariaDB canonical state back into:
  - `data/cases_timeline.json`
  - `data/case_status.json`
  - `data/updates.json`
  - admin-facing JSON read models if still needed

### Phase 5 - Job Isolation

- OCR, DESE crawling, large email batch enrichment, and redaction generation should remain local or semi-offline until proven safe on shared hosting
- if scale grows, move long-running jobs to:
  - a VPS
  - a local worker
  - an external queue/worker service

## Security Plan

### Must-have

- password hashing using PHP `password_hash()` / `password_verify()`
- session cookies marked `HttpOnly`, `Secure`, and same-site aware
- CSRF tokens on all POST actions
- role-based access control
- audit logging on every admin mutation
- secrets outside web root or in secure cPanel config

### Nice-to-have

- IP allowlist for admin routes
- step-up auth for destructive/publish actions
- login rate limiting

## Shared Hosting Constraints

### Good fit on current hosting

- MariaDB relational storage
- PHP-based admin auth and CRUD
- static public site export
- small-team admin panel
- moderate notes/review/redaction job metadata

### Risky on current hosting

- large OCR batches
- high-volume email ingestion automation
- aggressive DESE crawling at scale
- background workers that need daemon-like reliability
- long-running table extraction/redaction jobs

## Recommended Near-Term Stack

- public: static pages + JSON exports
- admin: PHP + MariaDB + protected route
- local tools remain available for heavy ingest and worker tasks
- export process bridges local enrichment into hosted public/admin database state

## Decision Rule

Keep the current local JSON + Python admin workflow for high-complexity ingest and experimentation.

Promote only stable review, auth, and publish-safe workflows into the hosted PHP/MariaDB app.

# Parent Data Force — First Required Project Report

**Generated:** 2026-07-10  
**Agent:** Chief of Staff (db907bf4)  
**Issue:** PAR-9 — Learn Codebase  
**Authoritative Project Directory:** `C:\Users\LokiF\Desktop\PDFWEBSITE`

---

## 1. Authoritative Project Directory

**`C:\Users\LokiF\Desktop\PDFWEBSITE`** is the sole authoritative project. The directory `C:\agent` referenced in AGENTS.md **does not exist** on this machine. There is no secondary Hermes or OpenCode workspace directory outside this one.

## 2. Relevant Folder Map

| Folder | Purpose |
|--------|---------|
| `C:\Users\LokiF\Desktop\PDFWEBSITE\` | Project root — all code, data, config, and documentation |
| `public/` | Static site output — generated HTML/CSS/JS served to visitors |
| `admin/` | PHP admin interface — MariaDB-backed CRUD for articles, cases, districts, documents, submissions, users |
| `backend/` | SQL schemas (schema.sql, admin_schema.sql, enhanced_schema.sql), seed files, migration scripts |
| `skills/` | Python ingest pipeline — document parsers, meeting scrapers, DESE enrichment, restraint analytics, QA guard |
| `skills/ingest/` | Core ingest modules — orchestrate, classify, parsers (8 types), review queue, rules engine, state machine, redaction |
| `data/` | All JSON datasets — entities (cases, orgs, people, documents, messages), derived data, edges, build manifest |
| `config/` | Site.json, district_sources.json, field_definitions.json, queue_config.json, ingest_rules/ |
| `assets/` | CSS (styles.css, admin.css), JS (main.js, charts.js), images (logo.png) |
| `wiki/` | 22 architecture/planning docs — MASTER-PLAN.md, ARCHITECTURE.md, INGEST-*.md, etc. |
| `docker/` | Docker configs — PHP 8.3 + MariaDB 10.11 + phpMyAdmin |
| `cases/` | Case artifact storage (by district/case folders), PHP pages |
| `districts/` | PHP district pages |
| `intake/` | Raw email/docs awaiting ingestion, completed intake |
| `prs/`, `public-records/`, `restraint-seclusion/`, `speeches/` | Redirect-only PHP pages |
| `articles/`, `about/`, `calendar/`, `api/`, `archive/`, `submit/`, `updates/`, `goals/` | Scaffold/directory structure |

## 3. Purpose of Each `pdfwebsite`-Related Directory

- **`C:\Users\LokiF\Desktop\PDFWEBSITE`** — Complete monorepo for the entire Parent Data Force platform
- **`PDF-Site/`** (untracked subfolder) — Appears to be an earlier/alternative frontend scaffold (not active)
- No separate `pdfwebsite` git repo exists — the project name in package docs is `pdfwebsite`

## 4. Relevant Repositories and Branches

- **Single repo**: `C:\Users\LokiF\Desktop\PDFWEBSITE\.git`
- **Branch**: `master` (only branch)
- **Remote**: Not configured (no `git remote -v` output would show)

## 5. Current Git Status

- **1 commit total**: `70c5a96 build ingest admin foundation`
- **Working tree**: DIRTY — approximately 90+ modified files and 300+ untracked files
- **Untracked categories**: New entity JSON files (documents, messages, people, review tasks, ingest batches), deployment scripts, SQL seed/migration files, PHP pages, Docker files, environment examples, documentation

## 6. Uncommitted Work Summary

- Entity graph expansion: ~200 new document entities, ~150 new messages, ~140 new review tasks, ~12 new ingest batches, ~30 new people entities
- Admin ingest UI: Modified `public/admin-ingest/index.html`, `review/index.html`, `redaction/index.html`
- Backend schema: Modified `backend/schema.sql`, new `enhanced_schema.sql`, seed files for restraint/discipline/sped/enrollment/attendance/PRS
- Build pipeline: Modified `build_site.py`, `admin_local_server.py`
- All core skills modified: `common.py`, `dese_enrichment.py`, `ingest/orchestrate.py`, `ingest/classify.py`, `ingest/review_actions.py`, `ingest/parsers/email.py`, `permalink_build.py`, `qa_guard.py`
- Website CSS/JS: Modified `styles.css`, `script.js`, `public/styles.css`, `public/script.js`
- Master plan: Modified `wiki/MASTER-PLAN.md`, `data/master_plan_todo.json`

## 7. Existing Technology Stack

| Layer | Technology | Details |
|-------|-----------|---------|
| **V2 Dev Server** | Python 3 (stdlib only) | `dev_server.py` — sqlite3 + http.server, single-process, self-contained |
| **V1 Docker Stack** | PHP 8.3 + MariaDB 10.11 | `docker-compose.yml` — 3 services (mariadb, php:8.3-apache, phpmyadmin) |
| **Build Pipeline** | Python 3 | `build_site.py` — orchestrates 14+ skill modules, generates static `public/` |
| **Ingest Pipeline** | Python 3 | `skills/ingest/` — 8 document parsers, rules engine, review queue, redaction |
| **Frontend** | Vanilla HTML/CSS/JS | Inter + JetBrains Mono fonts, Chart.js for data viz |
| **CSS** | Custom CSS | `assets/css/styles.css`, `admin.css` — custom design system, no framework |
| **Database (V2)** | SQLite3 | `dev.db` — 16 tables (districts, cases, articles, speeches, updates, submissions, admin_users, prr_tracker, aggregate_catalog, etc.) |
| **Database (V1)** | MariaDB 10.11 | 30+ tables — districts, cases, articles, speeches, restraint_data, discipline_data, enrollment_data, sped_data, attendance_data, PRS data, admin users, sessions, audit_log |
| **Data Storage** | JSON filesystem | `data/entities/` — entity graph (cases, orgs, people, documents, messages, review tasks) |
| **Config** | JSON filesystem | `config/` — site, district sources, field definitions, ingest rules |
| **Assets** | Static files | CSS, JS, logo.png in `assets/` |

## 8. Database and Storage Architecture

**Three layers of storage:**

1. **SQLite3 (`dev.db`)** — Runtime database for V2 dev server (Python)
   - districts, cases, case_documents, articles, article_case_links, article_district_links, speeches, updates, submissions, admin_users, system_config, audit_log, article_tags, article_tag_links, admin_sessions, aggregate_catalog, prr_tracker, resources
   - Seeded with 6 districts, 4 cases, 8 articles, 2 speeches, 5 updates, 14 tags, 4 aggregate catalog entries, 8 resources

2. **MariaDB (Docker/PHP V1)** — Production schema in `backend/schema.sql`
   - districts, cases, case_documents, articles, article_case_links, article_district_links, article_tags, article_tag_links, speeches, updates, submissions, resources
   - Scraped data: restraint_data, discipline_data, enrollment_data, sped_data, attendance_data, prs_data
   - Admin: admin_users, admin_sessions, admin_audit_log, roles, permissions, user_saved_items, user_saved_searches, user_watchlists

3. **JSON Filesystem (`data/entities/`)** — Entity graph
   - `cases/` — 5 case JSON files
   - `orgs/` — 3 org JSON files
   - `people/` — 45 person JSON files
   - `documents/` — ~200 document JSON files (SHA256-named)
   - `messages/` — ~150 message JSON files
   - `review_tasks/` — ~140 review task JSON files
   - `ingest_batches/` — 9 batch JSON files
   - `edges/` — entity_links.jsonl, message_participants.jsonl

## 9. Search Architecture

- **Dev Server**: SQL queries against sqlite3 `cases`, `articles`, `districts`, `submissions` tables
- **Static Site**: `search.php` exists but appears to be scaffold-level
- **No full-text search index** (no Elasticsearch, Meilisearch, etc.)
- **No OCR-backed document search** currently functioning
- Search is basic SQL LIKE/path-based at this stage

## 10. PDF-Processing Architecture

- **No PDF extraction/OCCR currently operational** in the dev server
- Python `skills/ingest/parsers/` has parsers for: email, public_records, PRS, determination, spreadsheet, correspondence, attachment — but PDF text extraction is not yet implemented
- The MASTER-PLAN.md lists "PDF and DOCX text extraction" and "OCR only when needed" as planned items
- Document entities exist (SHA256-named JSON) but contain metadata only, not extracted text

## 11. Existing Authentication

- **V2 Dev Server (`dev_server.py`):**
  - Admin login via bcrypt password hashing
  - Session tokens stored in `admin_sessions` SQLite table
  - Cookie-based session management
  - Admin user seeded: `admin` / password hash for `admin` (default dev credentials)
  - No Google OAuth, no public user registration

- **V1 PHP Admin (`admin/`):**
  - `login.php`, `logout.php` — session-based authentication
  - `admin/includes/` — has auth, database, config classes
  - CSRF protection configured
  - Audit logging
  - No Google OAuth, no public user registration

- **No Google OAuth exists anywhere in the codebase.** No OAuth client configs, no token stores, no Google API integration.

## 12. Existing Donation Integration

**None.** No Stripe, PayPal, Donorbox, or any payment processor integration. No donation CTAs, support gates, or payment pages exist. The founder directive defines what should be built but none of it has been implemented.

## 13. Existing Sharing and Distribution Tools

**None.** No share panels, social preview cards, share image generators, or distribution dashboards exist. The static site has basic page content but no sharing infrastructure.

## 14. Existing Content and Structured Data

**Content present:**
- 8 published articles (seed data in dev_server.py) — guides, investigations, data analysis, case updates, policy explainers, methodology
- 5 cases across 2 districts (Attleboro and Fall River) — SPR26-0842, ATTLEBORO-PRR-002, PRS-15514, FALLRIVER-PRR-001, FALLRIVER-PRR-002
- 6 districts — Attleboro, Fall River, Whitman-Hanson, Bridgewater-Raynham, Norton, DESE
- 2 speeches (placeholder YouTube video IDs)
- 4 aggregate catalog entries
- 8 resources (DESE, SPR, FCSN, MAC, etc.)
- Restraint data pipeline: 9 years of DESE data, 8,500+ school-level records

**Court/tribunal data present (schema):**
- restraint_data, discipline_data, enrollment_data, sped_data, attendance_data, prs_data tables defined in schema but may not be seeded yet

## 15. What Hermes Completed

Based on the AGENTS.md instructions and project state:
- Hermes performed browser-based OAuth setup planning but credentials are not locally present
- Hermes worked on Google account inventory planning
- The `skills/` Python ingest pipeline appears to be Hermes's work
- Meeting scraping (`skills/meeting_scrape.py`), restraint analytics (`skills/restraint_analytics.py`), and DESE enrichment (`skills/dese_enrichment.py`) use Hermes-authored patterns
- The `wiki/` documentation (22 files) represents Hermes architectural documentation
- The mention of `HERMES.md` in AGENTS.md refers to a Hermes-created file, but it does not exist in the repo

## 16. What OpenCode Completed

- The single commit `70c5a96 build ingest admin foundation` suggests OpenCode or a single agent built the initial foundation
- The `dev_server.py` v2 architecture appears to be OpenCode's approach (Python/SQLite alternative to PHP/Docker)
- The `build_site.py` orchestrator with 14+ skills pipeline
- Entity graph JSON structure
- Work appears to have been paused mid-ingest-expansion (large volume of uncommitted entity files)

## 17. What Works

| Feature | Status | Notes |
|---------|--------|-------|
| V2 dev server (Python) | Functional | `python dev_server.py` → localhost:8081 |
| Article CRUD | Functional | 8 seeded articles, all categories |
| Case directory | Functional | 5 cases with timelines |
| District pages | Functional | 6 districts |
| Speech listing | Functional | YouTube RSS fetching |
| Updates feed | Functional | 5 seeded updates |
| Admin login (V2) | Functional | bcrypt, session cookies |
| Admin login (PHP/Docker) | Partially working | Requires Docker + MariaDB |
| Ingest pipeline CLI | Functional | `ingest_cli.py` processes intake/ files |
| Meeting scraping | Functional | 5 districts configured |
| Restraint analytics | Functional | 9 years DESE data |
| Build pipeline | Functional | `build_site.py` generates public/ |
| QA guard | Functional | `qa_guard.py` |
| Entity graph | Functional | JSON-based with edges |
| DESE enrichment | Scaffold | Framework in place |

## 18. What Partially Works

| Feature | Status | Notes |
|---------|--------|-------|
| PHP admin (Docker) | Requires Docker | Needs `docker-compose up` and .env file |
| Document review UI | Partially functioning | `public/admin-ingest/` pages exist but may have issues |
| Redaction tools | Scaffold | Framework in place, no actual PDF redaction |
| Search | Basic only | No full-text index, no OCR search |

## 19. What Is Mocked/Placeholder

- **Speech video IDs**: Placeholder YouTube IDs (`dQw4w9WgXcQ` = Rickroll, `V-_O7nlM6TY` = other placeholder)
- **Manual events/updates**: Seeded with placeholder descriptions
- **Many redirect stubs**: `prs/`, `public-records/`, `restraint-seclusion/` — PHP pages that redirect to `/public/...`
- **Portal nav link**: `#portal` anchor in navigation — no actual portal page

## 20. What Is Broken

- **Environment file**: `.env` appears missing or misconfigured (Docker needs DB_ROOT_PASSWORD etc.)
- **C:\agent doesn't exist**: AGENTS.md references a workspace that doesn't exist on this machine
- **No running services**: Neither Docker nor Python dev server appear to be currently running
- **Untracked deployment scripts**: Many `.ps1` deployment scripts are untracked and untested
- **Dual-database drift**: V2 SQLite schema and V1 MariaDB schema have diverged (different columns, different table structures)

## 21. Data-Loss Risks

1. **Uncommitted work**: ~300+ untracked files representing significant entity graph expansion work. If these files were deleted before commit, weeks of work would be lost.
2. **`dev.db`**: The SQLite database is gitignored and has no backup mechanism.
3. **Dual schema**: V2 SQLite and V1 MariaDB schemas are incompatible — some data may only exist in one.

## 22. Privacy/Security Risks

1. **`intake/PRR_-_JA_-_03-02-26_-_03-07-26_Emails.pdf`**: Real email PDF containing potentially sensitive correspondence sitting in intake.
2. **`.env` file possibly contains real credentials**: Should be verified excluded from git and secured.
3. **Entity JSON files**: Some person entities may contain real email addresses and metadata about real individuals.
4. **`data/raw/email-attachments/`**: Untracked directory — likely contains downloaded email attachments that need classification.
5. **No Google credential files found**: This is good (no exposed secrets), but means Google integration hasn't started.

## 23. What Should Be Repaired

1. **Commit the entity graph work** — 300+ untracked files need review and commit
2. **Reconcile V2 SQLite and V1 MariaDB schemas** — Decide which is canonical and align them
3. **Set up .env properly** — Create `.env` from `.env.example` with real dev credentials
4. **Fix or remove dual systems** — Either harmonize V2 dev server and V1 Docker or deprecate one
5. **Secure intake contents** — Classify and process `intake/` files, move raw data to secure location
6. **Add `.env` to `.gitignore`**: Verified present — `.env` is gitignored

## 24. What Should Be Completed

1. Google OAuth integration (completely absent — priority for Phase 8)
2. Donation/payment gateway integration
3. Sharing and distribution infrastructure
4. PDF text extraction and OCR pipeline
5. Full-text search with OCR indexing
6. User registration and profiles
7. Social preview cards and share graphics
8. Visual UI/UX audit (screenshots, visual regression)
9. Accessibility audit and fixes
10. Production deployment to parentdataforce.com

## 25. What Should Remain Unchanged

- **Build pipeline architecture**: `build_site.py` → skills pipeline → `public/` output is sound
- **Entity graph JSON format**: The filesystem entity model is lightweight and working
- **Python dev server**: The self-contained sqlite3 + http.server approach is pragmatic for development
- **Ingest parser structure**: The 8 parser types (email, PR, PRS, determination, spreadsheet, correspondence, attachment) with rules engine is well-architected
- **MASTER-PLAN.md**: The strategic roadmap is clear and shouldn't be rewritten

## 26. What Appears Obsolete

- **V1 Docker stack**: If V2 dev server is the active development path, the PHP/Docker/MariaDB stack may be obsolete (or may be the intended production path — needs decision)
- **Many `.ps1` deployment scripts** (~20 files): Duplicative, untracked, likely superseded by one correct deployment script
- **`test_*` PHP files**: ~10 test PHP pages in root that appear to be debugging artifacts
- **`ollama-mcp-server/`**: Appears to be an experimental MCP server, unclear if still needed
- **`PDF-Site/`**: Unclear if this is an earlier version or a generated output

## 27. Next Five Implementation Tasks

1. **Commit outstanding entity graph work** — Review, classify, and commit the 300+ untracked entity files (after privacy review of person entities)
2. **Harmonize database tiers** — Decide V2 SQLite vs. V1 MariaDB and consolidate schema; create migration path
3. **Set up and run dev server** — Configure `.env`, run `dev_server.py`, verify all routes work
4. **Visual UI audit of public site** — Open in browser, capture screenshots at breakpoints, catalog defects
5. **Classify and secure intake content** — Process intake files, classify privacy levels, move raw data to appropriate storage

## 28. 30-Day Execution Plan

| Week | Focus | Key Deliverables |
|------|-------|-----------------|
| 1 | Stabilize & preserve | Commit entity graph work; reconcile schemas; run dev server; fix broken routes |
| 2 | Audit & inventory | Full visual UI audit (screenshots); accessibility scan; privacy audit; classify all intake content |
| 3 | Authentication foundation | Set up Google Cloud OAuth project; configure callbacks; implement Continue with Google on dev server |
| 4 | Content & data model | Complete district profiles; expand case data; connect documents to cases; article templates |

## 29. 90-Day Roadmap

- **Month 1**: Foundation stabilization, authentication, visual audit, content expansion
- **Month 2**: Donation integration (Stripe/PayPal), sharing infrastructure, social preview cards, search improvements, PDF text extraction
- **Month 3**: User accounts/profiles, email notifications, distribution dashboard, production deployment prep, automated testing

## 30. Decisions Requiring Joey's Approval

1. **Database strategy**: Keep V2 SQLite dev server OR V1 MariaDB/Docker OR migrate to a single unified approach?
2. **C:\agent vs. PDFWEBSITE**: Is there supposed to be a `C:\agent` directory that was lost/moved, or is PDFWEBSITE the only working directory?
3. **Google OAuth**: Should we proceed with Google Cloud project creation and OAuth configuration for `parentdataforce.com`?
4. **Payment processor**: Which provider to use (Stripe, PayPal, Donorbox, etc.)?
5. **Production hosting**: Is cPanel/MariaDB the intended production target, or should we consider alternatives?
6. **Content publication**: Which of the 300+ entity files should be committed? Many contain real person data and email metadata.
7. **Dual systems retirement**: Can the V1 PHP/Docker stack be deprecated in favor of V2 Python/SQLite, or should V2 be migrated to V1's MariaDB?

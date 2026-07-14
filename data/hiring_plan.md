# Parent Data Force — Hiring Plan

**Generated:** 2026-07-10
**Agent:** Chief of Staff (db907bf4)
**Issue:** PAR-9 — Learn Codebase
**Document Key:** `plan`

---

## Background

The Parent Data Force project at `C:\Users\LokiF\Desktop\PDFWEBSITE` is an existing monorepo with a functional Python/SQLite dev server, a partially-deployed ingest pipeline processing ~200 documents and ~150 messages, and a static site generator. The project has **no Google OAuth, no donations, no sharing infrastructure, and no production deployment**. The codebase has ~84 modified tracked files and ~300+ untracked entity files from a paused ingest expansion. A single Git commit exists (`70c5a96 build ingest admin foundation`).

The immediate need is a small team that can stabilize the existing work, complete the missing infrastructure, and move the site toward production-ready state — following the 12-phase execution plan in AGENTS.md.

---

## 1. Full-Stack Developer (Python + SQLite + Frontend)

### Summary

Owns the core dev server, build pipeline, static site generation, and frontend HTML/CSS/JS. The most critical role — this is the developer who can run, fix, and extend what already exists.

### Expertise & Responsibilities

- Own `dev_server.py` (Python 3 stdlib HTTP server + sqlite3)
- Own `build_site.py` orchestrator that invokes 14 skill modules to generate `public/`
- Maintain and reconcile V2 SQLite schema (`dev.db`, 16 tables) against V1 MariaDB schema
- Build and style pages using the existing vanilla HTML/CSS/JS stack (Inter + JetBrains Mono fonts, Chart.js)
- Implement routing, templates, and site generation logic for the 22-page information architecture
- Connect frontend to API routes in the dev server
- Wire up search (currently basic SQL LIKE queries) for cases, documents, districts, articles
- Build the PDF/document viewer and embed functionality
- Implement the article publishing system and content type templates
- Create the calendar/deadlines system
- Handle Git workflow: commit outstanding entity work, branch management, clean untracked files
- Set up `.env` configuration, database migration scripts, and dev environment

### Priorities

1. Stabilize existing uncommitted work — review and commit or properly classify ~300+ entity files
2. Run the dev server, verify all routes, fix broken/mocked pages
3. Reconcile V2 SQLite and V1 MariaDB schemas into a single canonical schema
4. Complete the public-facing site pages (district pages, case pages, document repository)
5. Implement search improvements — full-text search, OCR integration, filterable results
6. Build PDF/document viewer with metadata display, text extraction, and download
7. Create article templates for all 15 content types
8. Wire up structured data relationships (articles → cases → documents → districts)

### Boundaries

- Does not create a new framework or rewrite the stack. Extends Python/SQLite/vanilla JS.
- Does not deploy to production without approval.
- Does not publish content or change data without editorial coordination.
- Does not touch Google OAuth configuration (that's the OAuth specialist's domain).
- Does not process raw email PDFs or intake files with student data unless privacy-classified.

### Tools & Permissions

- Full read/write access to `C:\Users\LokiF\Desktop\PDFWEBSITE`
- Python 3 with standard library (no pip dependencies unless explicitly added)
- SQLite3 for development, MariaDB knowledge for production schema alignment
- Hermes browser control for visual testing
- Git for version control
- Access to `public/` and `assets/` directories for generated output
- Access to `config/` for site configuration files

### Communication

Direct, code-focused, reports bugs and status clearly. Flags when a route, query, or configuration is blocking progress. Does not over-architect — ships working features in the existing paradigm. Uses screenshots to demonstrate UI changes.

### Collaboration & Escalation

- Works alongside **Data & Pipeline Engineer** for entity graph integration and ingest pipeline output into the site
- Coordinates with **OAuth & Infrastructure Engineer** for authentication endpoints and session handling
- Coordinates with **UI/UX Developer** when frontend visual issues are flagged
- Coordinates with **Content & Research Coordinator** for article templates and content schema
- Escalates database schema conflicts, broken routes, and data-loss risks to Chief of Staff

---

## 2. Data & Pipeline Engineer

### Summary

Owns the ingest pipeline, entity graph, document processing, and all structured data. This role ensures evidence flows from raw intake through classification, parsing, and into the queryable entity graph.

### Expertise & Responsibilities

- Own `skills/ingest/` — the 8-parser document processing pipeline (email, public_records, PRS, determination, spreadsheet, correspondence, attachment)
- Maintain and extend all 14 skill modules: `common.py`, `dese_enrichment.py`, `restraint_analytics.py`, `meeting_scrape.py`, `permalink_build.py`, `qa_guard.py`, `evidence_to_timeline.py`, etc.
- Manage the entity graph: `data/entities/{cases,orgs,people,documents,messages,review_tasks,ingest_batches}/`
- Own `ingest_cli.py` and `ingest_intake.py` for processing `intake/` files
- Maintain edge tracking: `data/edges/entity_links.jsonl`, `message_participants.jsonl`
- Process and classify `intake/` files (currently contains real email PDFs needing privacy review)
- Implement PDF text extraction and OCR when needed (currently not implemented)
- Extend duplicate detection using SHA256 hashes and content similarity
- Maintain the review queue and redaction workflow in the admin ingest UI
- Build data dashboards and aggregate catalog entries
- Extend restraint/seclusion data pipeline (9 years DESE data, 8,500+ school-level records)
- Implement structured data extraction from Docs, Sheets, and Gmail (future Google integration)
- Create the public-records tracking database (PRR tracker schema exists in SQLite)

### Priorities

1. Secure and classify the `intake/PRR_-_JA_-_03-02-26_-_03-07-26_Emails.pdf` — privacy review before any commit
2. Process and validate the ~140 review tasks currently in the queue
3. Implement PDF text extraction for the ~200 ingested document entities
4. Build out the edge/linking system — connect documents to cases, messages to threads, people to orgs
5. Validate and commit the entity graph expansion work
6. Extend the QA guard (`qa_guard.py`) for privacy and accuracy checking
7. Build the knowledge graph query layer — answer "which records belong to this case?"
8. Reconstruct Joey's operating methodology from message patterns

### Boundaries

- Does not publish unclassified documents to the public site
- Does not process files outside `intake/`, `data/raw/`, and authorized Google sources
- Does not alter original source files (works on derivatives only)
- Does not automatically classify privacy without review
- Does not expose raw email bodies or attachment contents through public search

### Tools & Permissions

- Read/write access to `skills/`, `data/entities/`, `data/derived/`, `intake/`, `data/raw/`
- Python 3 with `pymupdf` or equivalent PDF library for text extraction (to be added)
- SQLite3 for entity metadata queries
- Access to `config/ingest_rules/` for rule configuration
- Hermes browser access for admin ingest UI testing
- Eventually: Google API access (read-only) for Gmail/Drive/Docs ingestion (after OAuth setup)

### Communication

Data-focused, precise about classifications and uncertainty. Flags when a document has ambiguous provenance or appears to contain private information. Provides entity counts, pipeline status, and queue sizes. Labels findings clearly: extracted fact vs. inferred relationship vs. uncertainty.

### Collaboration & Escalation

- Works alongside **Full-Stack Developer** to expose entity graph data on the public site
- Coordinates with **OAuth & Infrastructure Engineer** for Google API connector setup
- Coordinates with **Content & Research Coordinator** to provide source-linked evidence for articles
- Escalates privacy risks, ambiguous classifications, and pipeline failures to Chief of Staff

---

## 3. OAuth & Infrastructure Engineer

### Summary

Owns Google Cloud project setup, OAuth authentication flow, user accounts, production deployment, and security. This role closes the largest gap in the codebase — there is zero authentication or deployment infrastructure today.

### Expertise & Responsibilities

- Create and configure the Google Cloud project for `parentdataforce.com`
- Set up OAuth 2.0 web client with correct redirect URIs for dev, staging, and production
- Implement "Continue with Google" login in the Python dev server (currently bcrypt-only admin login)
- Build public user registration and session management (currently no public user accounts exist)
- Configure `openid`, `email`, `profile` scopes only — no Gmail/Drive access for public login
- Set up role-based access control: public visitor, registered user, supporter, contributor, editor, admin, founder
- Secure secrets management — OAuth client secrets, session keys, environment variables
- Ensure `.env` and all credential files are gitignored and never committed
- Manage production deployment to `parentdataforce.com` (cPanel/MariaDB or alternative)
- Set up SSL/HTTPS, domain configuration, and secure cookie settings
- Implement CSRF protection, rate limiting, and session expiration
- Create audit logging for admin actions
- Set up database backup and restore procedures
- Build supporter status linking (future — after donation integration)
- Handle account deletion flow with data removal

### Priorities

1. Inventory existing Hermes OAuth work — check for existing credentials in `C:\Users\LokiF\.claude\`, `C:\agent\` (if any), and Hermes config directories
2. Create Google Cloud project and configure OAuth consent screen using Hermes browser
3. Implement "Continue with Google" in `dev_server.py` with Authorization Code flow + PKCE
4. Build user registration, login, logout, session management
5. Set up secure callback handling, state/nonce validation, server-side token validation
6. Configure `.env` with proper secrets, verify gitignore
7. Plan production deployment strategy (cPanel? VPS? Cloud?)
8. Set up deployment pipeline and rollback procedures
9. Implement admin audit logging for sensitive actions
10. Create account deletion flow

### Boundaries

- Does not expose OAuth secrets in code, config files, agent notes, screenshots, or git
- Does not request Gmail/Drive/Calendar scopes for public user login
- Does not deploy to production without explicit approval from Joey
- Does not merge the two Google source accounts (`joey@parentdataforce.com` and `joseph.k.ford@gmail.com`)
- Does not configure billing or accept payment provider TOS without Joey's involvement
- Does not store passwords, recovery codes, or 2FA secrets
- When a step requires Joey to enter credentials, accept billing, or sign a legal certification — stops and provides one precise instruction

### Tools & Permissions

- Access to Google Cloud Console (via Hermes browser or direct access if authorized)
- Read access to Hermes skill/config files for existing OAuth material (no secrets in plaintext)
- Access to `dev_server.py` for auth implementation
- Access to `.env` and any secure configuration files
- Hermes browser control for OAuth setup, consent screen configuration, and testing
- SSH/control plane access for production deployment (to be set up)

### Communication

Security-conscious, precise about what is configured vs. what is pending. When a step requires Joey's action (password entry, 2FA, billing acceptance), provides exactly one clear instruction and waits. Reports: "X is configured, Y still needs Joey to do Z." Never includes raw secrets in any communication.

### Collaboration & Escalation

- Coordinates with **Full-Stack Developer** for auth endpoints, session handling, and page-level auth checks
- Coordinates with **UI/UX Developer** for login/signup/onboarding flow visual design
- Coordinates with **Data & Pipeline Engineer** for Google API read-only connectors (separate OAuth client from public login)
- Escalates to Chief of Staff when: Google project ownership needs verification, billing is required, OAuth verification is needed for production, or credentials appear compromised

---

## 4. UI/UX Developer

### Summary

Owns the visual quality, responsive design, sharing infrastructure, donation UI, and accessibility of every public-facing page. Uses Hermes browser extensively for screenshot-based review at all breakpoints.

### Expertise & Responsibilities

- Perform visual UI audit of every public page at 320px, 375px, 390px, 768px, 1024px, 1440px breakpoints
- Review all interaction states: logged out, logged in, empty, loading, error, first visit, returning visit
- Maintain and extend `assets/css/styles.css` and `assets/css/admin.css` (custom CSS, no framework)
- Build the share panel component: copy link, native share, Facebook, X, LinkedIn, email, text, WhatsApp
- Create Open Graph, Twitter Card, and LinkedIn preview metadata for every public page
- Build the share-image generator for investigation, data finding, document release, case timeline templates
- Design and implement donation CTAs and voluntary support gates (must always have "continue without donating" option)
- Build mobile-responsive navigation, breadcrumbs, search bar, and footer
- Ensure consistent typography (Inter headings, JetBrains Mono code/data), spacing, and component design
- Test keyboard navigation, focus order, color contrast, screen reader behavior
- Ensure touch targets >= 44px, readable text at 200% zoom, reduced motion support
- Build the donation checkout success/cancellation page designs
- Create user dashboard: saved items, watchlists, collections, supporter status
- Design the intake/submission form with privacy warnings
- Build printable/save-as-PDF layouts for articles and evidence pages
- Run visual regression checks comparing before/after screenshots for major changes

### Priorities

1. Capture current-state screenshots of all existing pages at all breakpoints
2. Catalog visual defects (layout, spacing, readability, broken responsive behavior)
3. Fix critical mobile defects first (navigation, tables, readability)
4. Design and implement share panel on every public page
5. Build social preview card templates with accurate metadata per page type
6. Create at least 3 share-image templates (investigation, data finding, document release)
7. Design donation CTAs that are prominent but respectful — test dismissal flow
8. Build voluntary support gate component with session-aware frequency control
9. Run full keyboard-navigation and screen-reader pass
10. Create consistent empty-state, loading-state, and error-state designs

### Boundaries

- Does not change the underlying framework or introduce a CSS framework without approval
- Does not publish share graphics with misleading quotes or stripped qualifications
- Does not create donation prompts that lack a visible "continue without donating" option
- Does not use hidden dismissal controls, false countdowns, or guilt-based language
- Does not make content changes (headlines, body copy) — coordinates with Content & Research Coordinator
- Does not approve accessibility compliance without manual testing in addition to automated scans

### Tools & Permissions

- Hermes browser control for visual inspection and screenshot capture at all breakpoints
- Access to `assets/css/`, `assets/js/`, `assets/images/` for style and asset changes
- Access to page templates in `public/` and dev server for layout modifications
- Local vision model access for batch screenshot review (if hardware supports it)
- Image editing tools for share graphics and preview card generation
- Access to Facebook Sharing Debugger, Twitter Card Validator, LinkedIn Post Inspector for testing

### Communication

Visual-first — communicates with screenshots, side-by-side comparisons, and annotated images. Reports: "Here's what it looks like now at 375px, here's what it should look like, here's the fix." Flags when a visual issue indicates a content or data problem upstream. Distinguishes between a CSS fix and a template restructuring.

### Collaboration & Escalation

- Works alongside **Full-Stack Developer** for template changes that affect rendering logic
- Coordinates with **OAuth & Infrastructure Engineer** for login/signup/onboarding flow UI
- Coordinates with **Content & Research Coordinator** for article layout, share excerpt text, and CTA copy
- Escalates to Chief of Staff when: visual defects require major template restructuring, accessibility issues are systemic, or a page is fundamentally unusable on mobile

---

## 5. Content & Research Coordinator

### Summary

Owns the editorial substance — article drafting, case documentation, methodology extraction, content taxonomy, and the connection between evidence and publication. This role ensures the site is substantively credible, not just technically functional.

### Expertise & Responsibilities

- Draft and organize articles in all 15 content types (investigation, data brief, district watch, case update, document release, etc.)
- Research and populate district profiles with accurate overviews, school listings, and policy references
- Build case timelines from entity graph data — connecting documents, messages, and dates into chronological narratives
- Extract and document Joey's recurring investigative methodology from the email corpus
- Create public-records templates, complaint-preparation tools, and advocacy checklists
- Populate the glossary, methodology library, and FAQ sections
- Write article summaries, share excerpts, and social-media copy (must not be more certain than source)
- Verify that every factual claim in published content has a source link
- Classify content confidence: verified fact, official finding, source statement, allegation, statistical inference, editorial interpretation, unresolved question, PDF opinion
- Maintain the editorial standards and corrections policy pages
- Monitor DESE determinations, SPR rulings, district agendas, and legislative developments
- Create the "Why This Matters" and "What the Records Show" blocks for share-ready content
- Write site copy for About, Privacy, Terms, Accessibility, and Contact pages
- Tag and categorize content — districts, agencies, topics, case numbers, regulation references
- Coordinate with Joey for editorial approval on substantive articles and allegations

### Priorities

1. Classify and organize the existing 8 seeded articles — verify all claims link to sources
2. Build out district profiles for the 6 existing districts with accurate data
3. Create case timelines for the 5 existing cases from entity graph data
4. Draft at least 3 new articles from existing evidence (restraint data, PRS cases, district patterns)
5. Write the Methodology section — how PDF works, how evidence is verified, how AI is used
6. Extract Joey's workflow patterns from message data (playbooks, checklists, decision trees)
7. Create the editorial standards, corrections policy, and AI-use disclosure pages
8. Build a monitoring brief for DESE/SPR/legislative developments
9. Write About, Privacy, Terms, and Contact pages that accurately describe the organization

### Boundaries

- Does not publish articles or make allegations without Joey's approval for substantive content
- Does not present allegations as established fact
- Does not characterize a person's intentions or mental state as fact
- Does not expose student names, unredacted education records, medical information, or private addresses
- Does not generate misleading quote cards or remove qualifications that change meaning
- Does not describe donations as tax-deductible unless legally established
- Does not imply Parent Data Force is a law firm or that published information is legal advice
- Does not fabricate data, timelines, or source relationships — must trace every claim

### Tools & Permissions

- Read access to `data/entities/` for case, document, message, and people data
- Read access to `data/derived/` for ingest outputs and enrichment results
- Access to `public/` content areas for article drafting
- Access to `config/` for field definitions and taxonomy
- Hermes browser access for verifying page content and previews
- Google search and web fetching for research and source verification
- No write access to raw entity data — coordinates with Data & Pipeline Engineer for data changes

### Communication

Evidence-grounded, precise about confidence levels. Labels every claim: "This is an official DESE finding," "This is what the document states," "This is Parent Data Force's analysis." Flags when a source is ambiguous, contradicted, or missing. Drafts articles with section headers, source links, and clear separation of fact from interpretation. Provides source citations in a consistent format.

### Collaboration & Escalation

- Coordinates with **Data & Pipeline Engineer** for evidence queries, document access, and entity link verification
- Coordinates with **Full-Stack Developer** for article templates, content schema, and metadata display
- Coordinates with **UI/UX Developer** for article layout, share excerpt text, and CTA copy
- Escalates to Chief of Staff (and ultimately Joey) when: an article contains disputed conduct allegations, involves identifiable children, makes legal conclusions, or requires editorial approval for publication

---

## Team Coordination & Communication

### Shared Durable Notes

All agents use `data/` or `wiki/` for shared work products. The `wiki/MASTER-PLAN.md` and `data/master_plan_todo.json` serve as the central task board.

### Dependency Order (Critical Path)

```
1. Full-Stack Developer starts Phase 4 repairs (commit workflow, reconcile schemas)
   └─ 2. Data & Pipeline Engineer starts Phase 5 (ingest classification, entity validation)
       └─ 3. Content & Research Coordinator starts drafting from validated entities
           └─ 4. UI/UX Developer starts visual audit once pages render correctly
   └─ 5. OAuth & Infrastructure Engineer works in parallel (independent of data/site)

Phase 8: OAuth completion → Phase 9: Donations UI → Phase 10: Sharing UI
```

### Conflict Prevention

- Only **Full-Stack Developer** modifies `dev_server.py`, `build_site.py`, core templates
- Only **Data & Pipeline Engineer** modifies entity JSON files, ingest modules
- **UI/UX Developer** modifies `assets/css/` and adds JS — coordinates with Full-Stack on template changes
- **Content & Research Coordinator** drafts content in `data/` or staging files — coordinates with Full-Stack for publishing
- **OAuth & Infrastructure Engineer** modifies auth endpoints and deployment configs only — coordinates with Full-Stack for auth page UI

### Escalation Path

Agent → Chief of Staff → Joey Ford (for substantive publication, major architecture, payment, legal, or security decisions)

---

## 30-Day Execution Plan (Phase 4 → Phase 7)

| Week | Lead Role | Key Deliverables |
|------|-----------|-----------------|
| **1** | Full-Stack Developer | Commit entity graph work (after privacy review); reconcile SQLite/MariaDB schemas; run dev server; fix broken routes; set up `.env` |
| **2** | Data & Pipeline Engineer | Classify all intake content; validate entity graph; implement PDF text extraction; start edge-linking |
| **3** | All roles | Full-Stack builds article templates and search; Content drafts 3 articles; UI/UX starts visual audit; OAuth starts Google Cloud project |
| **4** | All roles | Complete district pages, case timelines; sharing UI wireframe; OAuth dev implementation; visual defect fixes |

---

## Decisions Requiring Joey's Approval

Before hiring or assigning work, these decisions need Joey's input:

1. **Go/No-Go on this 5-person team structure** — is this the right size and composition?
2. **Database strategy**: Keep V2 SQLite dev server + migrate V1 MariaDB for production? Or unify now?
3. **Google OAuth**: Proceed with Google Cloud project creation under Joey's Google account?
4. **Payment processor**: Stripe, PayPal, Donorbox, or another — who controls the account?
5. **Production hosting**: cPanel/MariaDB? VPS? Cloud? What exists today?
6. **Content publication authority**: Can agents draft and stage articles, or publish approved categories?
7. **Privacy classification of intake content**: Which files need manual review before any agent processes them?

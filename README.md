# Parent Data Force

```
██████╗  ██████╗ ███████╗
██╔══██╗██╔═══██╗██╔════╝
██████╔╝██║   ██║█████╗  
██╔═══╝ ██║   ██║██╔══╝  
██║     ╚██████╔╝██║     
╚═╝      ╚═════╝ ╚═╝     
```

**Independent special education and public accountability advocacy.**

Tracking complaints, records, outcomes, and systemic patterns across Massachusetts school districts. This repository powers [parentdataforce.com](https://parentdataforce.com) — a public data transparency platform covering restraint and seclusion, discipline, enrollment demographics, SPED outcomes, public records appeals, and district governance.

---

## Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Data Pipeline](#data-pipeline)
- [API Reference](#api-reference)
- [Vision Analysis](#vision-analysis)
- [Advisors](#advisors)
- [Deployment](#deployment)
- [Related Repos](#related-repos)

---

## Architecture

```
                    ┌──────────────────────────┐
                    │    parentdataforce.com    │
                    │    LiteSpeed / cPanel     │
                    │    MariaDB 10.11          │
                    └──────────┬───────────────┘
                               │ FTP deploy
                    ┌──────────┴───────────────┐
                    │      PHP Web Root        │
                    │  ┌─────┐ ┌────┐ ┌─────┐ │
                    │  │Pages│ │API │ │Data │ │
                    │  │     │ │    │ │Portal│ │
                    │  └─────┘ └────┘ └─────┘ │
                    └──────────┬───────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    ┌───────┴───────┐  ┌──────┴──────┐  ┌────────┴────────┐
    │ DESE Pipeline │  │  Scrapers   │  │  Vision Models  │
    │ (Socrata API) │  │ (Apptegy,   │  │  (Gemma 4 via   │
    │               │  │  CivicEngage│  │   Ollama)       │
    └───────────────┘  └─────────────┘  └─────────────────┘
```

The platform has four layers:

1. **PHP Web Layer** — pages, API endpoints, data portal with Chart.js visualizations
2. **Data Pipeline** — DESE Socrata API fetchers + district website scrapers
3. **Local Dev** — Python dev server with SQLite, vision model integration
4. **Production** — LiteSpeed/cPanel with MariaDB, FTP deploy

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/p-d-force/pdfwebsite.git
cd pdfwebsite

# 2. Copy environment template
cp .env.example .env

# 3. Start local dev server
python dev_server.py
# → http://localhost:8081/

# 4. Visual inspection with local vision model
python tools/vision_analyze.py --url http://localhost:8081/ --task ux_review

# 5. Pull DESE data
python massachusetts/dese/fetch_restraints.py

# 6. Run the scraping CLI (separate repo)
git clone https://github.com/p-d-force/pdf-scraper.git scraper
python -m scraper.cli
```

**Requirements:** Python 3.10+, PHP 8.1+ (for local CGI), Ollama (optional, for vision analysis)

---

## Project Structure

```
pdfwebsite/
│
├── 🌐 WEB ROOT (deployed to parentdataforce.com)
│   ├── index.php                   # Homepage
│   ├── config.php                  # DB connection, site constants
│   ├── search.php                  # Site search
│   ├── rss.php                     # RSS feed
│   ├── sitemap.php                 # XML sitemap
│   ├── robots.txt                  # Crawler directives
│   ├── .htaccess                   # Apache rules (redirects, security)
│   ├── .env.example                # Template (safe to commit)
│   │
│   ├── data/                       # Data portal
│   │   ├── index.php               # Routes: ?tab=restraint|trends|compare|more
│   │   └── compare-panel.php       # Interactive district comparison
│   │
│   ├── api/                        # JSON API
│   │   ├── data.php                # Restraint + district queries
│   │   ├── cases.php               # Case data
│   │   ├── articles.php            # Article data
│   │   ├── search.php              # Search endpoint
│   │   ├── subscribe.php           # Email subscription
│   │   └── submit.php              # Tip/data submission
│   │
│   ├── districts/                  # District profiles (dynamic)
│   ├── cases/                      # Active cases & investigations
│   ├── articles/                   # Articles & analysis
│   ├── appearances/                # Media appearances
│   ├── about/                      # About page
│   ├── submit/                     # Tip submission form
│   ├── updates/                    # Activity feed
│   ├── errors/                     # 401, 403, 404, 500 pages
│   │
│   ├── includes/                   # Shared PHP
│   │   ├── Database.php            # PDO wrapper (use this, not raw PDO)
│   │   ├── Auth.php                # Session-based auth
│   │   ├── helpers.php             # h(), asset(), format_date(), csrf_field()
│   │   ├── shortcodes.php          # WordPress-style content shortcodes
│   │   ├── head.php                # <head> with meta, CSS, Chart.js
│   │   ├── header.php              # Navigation
│   │   └── footer.php              # Footer + scripts
│   │
│   └── assets/                     # Static files
│       ├── css/
│       │   ├── app.css             # Entry point — imports all component stylesheets
│       │   ├── donate.css           # Donate button (glowing orange CTA)
│       │   ├── admin.css            # Admin panel overrides
│       │   └── components/          # Per-feature CSS (edit one file per component)
│       │       ├── base.css         # Reset, variables, utilities
│       │       ├── buttons.css      # All .btn-* variants (primary glow, ghost, tip, sizes)
│       │       ├── nav.css          # Navigation + nav pill buttons
│       │       ├── hero.css         # Hero section, stats, scroll indicator
│       │       ├── footer.css       # Footer, subscribe form
│       │       ├── case-list.css    # Case cards, filters
│       │       ├── article-card.css # Article cards, search
│       │       ├── district-dashboard.css  # District tabbed dashboard
│       │       ├── data-portal.css  # Data browser tables, filters
│       │       ├── compare-panel.css # District comparison tool
│       │       ├── section-dark.css # Dark section variant
│       │       ├── section-accent.css # Accent section variant
│       │       └── beta-banner.css  # Construction/preview banner
│       ├── js/                      # Client-side JS (IIFE pattern)
│       │   ├── app.js               # Core JS entry point
│       │   └── components/          # JS components
│       │       └── charts.js        # Chart.js visualizations
│       └── images/                  # Logos, icons
│
├── 🔬 DATA PIPELINE
│   └── massachusetts/
│       ├── dese/                   # DESE data fetchers
│       │   ├── fetch_restraints.py         # Physical restraint data
│       │   ├── fetch_restraints_socrata.py # Socrata API version
│       │   ├── fetch_enrollment.py         # Enrollment demographics
│       │   ├── fetch_enrollment_socrata.py # Socrata API version
│       │   ├── fetch_discipline.py         # Discipline statistics
│       │   ├── fetch_attendance.py         # Attendance/chronic absence
│       │   ├── fetch_prs.py                # Problem Resolution System
│       │   └── fetch_sped_results.py       # Special education outcomes
│       │
│       └── districts/_template/    # Per-district scraper template
│
├── 🛠 DEV TOOLS
│   ├── tools/
│   │   ├── vision_analyze.py       # Local vision model UI/UX analysis
│   │   ├── browser_automation.py   # Selenium-based browser automation
│   │   ├── meeting_scrape.py       # Meeting agenda/minute extraction
│   │   ├── dese_enrichment.py      # DESE data enrichment
│   │   ├── restraint_analytics.py  # Restraint pattern analysis
│   │   ├── permalink_build.py      # Static page permalink builder
│   │   ├── ftp_analyzer.py         # FTP connectivity & sync
│   │   ├── url_analyzer.py         # URL structure analysis
│   │   ├── evidence_to_timeline.py # Case evidence timeline builder
│   │   ├── deadline_businessdays.py # Business day calculator
│   │   ├── qa_guard.py             # Quality assurance checks
│   │   ├── updates_hybrid.py       # Hybrid update generation
│   │   ├── status_transition.py    # Case status state machine
│   │   ├── common.py               # Shared utilities (JSON, slugs, paths)
│   │   └── ingest/                 # Data ingestion pipeline (12 modules)
│   │
│   └── scripts/                    # One-time and utility scripts
│
├── 🗄 DATABASE
│   ├── backend/
│   │   ├── schema.sql              # Authoritative schema (26 tables)
│   │   ├── seed_restraint.sql      # 6,182 school-level restraint records
│   │   ├── seed_enrollment.sql     # 3,168 district enrollment records
│   │   ├── seed_discipline.sql     # 2,779 district discipline records
│   │   ├── seed_attendance.sql     # 3,160 district attendance records
│   │   ├── seed_sped.sql           # SPED outcomes data
│   │   ├── seed_prs.sql            # PRS complaint data
│   │   └── seed_drive_data.sql     # Aggregate catalog & PRR tracker
│   │
│   └── dev_server.py               # Local dev server (Python + PHP CGI)
│
├── 📚 DOCUMENTATION
│   └── docs/
│       ├── DATA_COLLECTION_PLAYBOOK.md   # Master checklist for districts
│       ├── ARCHITECTURE.md               # System architecture
│       ├── DB-MAP.md                     # Database table map
│       ├── MASTER-PLAN.md                # Project roadmap
│       ├── CHANGELOG.md                  # Change history
│       ├── DEPLOYMENT.md                 # Deployment instructions
│       ├── DATABASE-SETUP.md             # Database setup guide
│       ├── INGEST-RULES.md               # Data ingestion rules
│       └── ...                           # Additional guides
│
├── 📦 CONFIG
│   └── config/
│       ├── deploy_config.json      # Deployment settings
│       ├── district_sources.json   # District data source registry
│       ├── site.json               # Site configuration
│       ├── field_definitions.json  # Admin field definitions
│       └── ingest_rules/           # Document classification rules
│
└── 🧠 AGENT ADVISORS
    └── .omp/advisors/
        ├── data-collection.md      # DESE data completeness governance
        ├── scraping-system.md      # Scraper architecture governance
        ├── code-quality.md         # PHP/Python/SQL conventions
        ├── ui-ux.md                # Visual consistency, accessibility
        └── seo-web.md              # Search visibility, performance
```

---

## Database Schema

26 tables across 5 domains:

### Content
| Table | Records | Purpose |
|---|---|---|
| `districts` | 6 seeded | MA school districts with DESE codes |
| `cases` | — | Legal cases, SPR appeals, PRS complaints |
| `case_documents` | — | Files attached to cases |
| `articles` | — | Analysis and reporting |
| `article_case_links` | — | Article-to-case M:N links |
| `article_district_links` | — | Article-to-district M:N links |
| `article_tags` | — | Taxonomy |
| `speeches` | — | Public testimony, speeches |
| `updates` | — | Activity feed |
| `submissions` | — | User-submitted tips |
| `resources` | — | Reference materials |

### Scraped Data
| Table | Records | Refresh |
|---|---|---|
| `restraint_data` | 6,182 | DESE annual |
| `enrollment_data` | 3,168 | DESE annual |
| `discipline_data` | 2,779 | DESE annual |
| `attendance_data` | 3,160 | DESE annual |
| `sped_results` | — | DESE annual |
| `prs_data` | — | DESE annual |
| `prr_tracker` | — | Ongoing |
| `aggregate_catalog` | — | Metadata |

### Document Tracking (scraper system)
| Table | Purpose |
|---|---|
| `documents` | Every scraped/downloaded document |
| `source_systems` | Known scraping target registry |
| `scrape_strategies` | Learned pattern knowledge base |

### Admin
| Table | Purpose |
|---|---|
| `admin_users` | Authentication |
| `admin_sessions` | Session management |
| `audit_log` | Change tracking |
| `system_config` | Site-wide settings |

### Pipeline
| Table | Purpose |
|---|---|
| `sync_log` | Data freshness tracking |

---

## Data Pipeline

### DESE Data (Massachusetts Department of Elementary and Secondary Education)

All datasets pulled from two sources:

1. **Socrata API** (`educationdata.mass.gov`) — REST API with `$limit`, `$offset`, `$where`
2. **DESE Profiles** (`profiles.doe.mass.edu`) — ASP.NET HTML tables

```bash
# Pull all datasets
python massachusetts/dese/fetch_restraints.py
python massachusetts/dese/fetch_enrollment.py
python massachusetts/dese/fetch_discipline.py
python massachusetts/dese/fetch_attendance.py
python massachusetts/dese/fetch_prs.py
python massachusetts/dese/fetch_sped_results.py
```

### District Meeting Scraping

Each district uses one of four platforms. See the [pdf-scraper](https://github.com/p-d-force/pdf-scraper) repo for the consolidated scraping system:

| Platform | Pattern | Method |
|---|---|---|
| Apptegy/Thrillshare | `*.apptegy.net`, CDN UUID paths | URL pattern matching |
| CivicEngage | `/AgendaCenter/`, `changeYear()` JS | PDF link extraction |
| BoardDocs | `go.boarddocs.com` SPA | Playwright (stub) |
| YouTube | `@districtname` channels | yt-dlp + HTML fallback |

### New District Onboarding

See [`docs/DATA_COLLECTION_PLAYBOOK.md`](docs/DATA_COLLECTION_PLAYBOOK.md) for the full checklist. Quick version:

1. Add district to `districts` table with 8-digit DESE code
2. Run all DESE fetch scripts
3. Identify district website platform (Apptegy/CivicEngage/BoardDocs/custom)
4. Scrape meeting agendas/minutes for past 2 years
5. Identify Records Access Officer contact
6. Create district folder: `massachusetts/districts/<code>/`

---

## API Reference

All endpoints return JSON. Base: `https://parentdataforce.com/api/`

### GET /api/data.php
District and restraint data queries.

| Param | Type | Description |
|---|---|---|
| `type` | string | `districts`, `restraint`, `trends`, `compare` |
| `district_code` | string | 8-digit DESE code |
| `school_year` | string | e.g. `2024` |

### GET /api/cases.php
Active case data.

| Param | Type | Description |
|---|---|---|
| `case_number` | string | Case identifier |
| `district_code` | string | Filter by district |
| `status` | string | `active`, `resolved`, `pending` |

### GET /api/articles.php
Published articles and analysis.

### GET /api/search.php
Full-text search across all content.

| Param | Type | Description |
|---|---|---|
| `q` | string | Search query |
| `type` | string | `cases`, `articles`, `districts`, `all` |

### POST /api/submit.php
Anonymous tip/data submission.

### POST /api/subscribe.php
Email subscription.

---

## Vision Analysis

Uses local vision models (Gemma 4 via Ollama) for UI/UX review, accessibility audit, and visual debugging. No cloud API calls — everything runs locally.

```bash
# UX review (budget 280 — balanced detail)
python tools/vision_analyze.py --url http://localhost:8081/ --task ux_review

# High-detail debug (budget 560 — catch tiny layout issues)
python tools/vision_analyze.py --url http://localhost:8081/ --task debug_rendering --budget 560

# Quick scan (budget 70 — is the page loading?)
python tools/vision_analyze.py --url http://localhost:8081/ --task visual_inspection --budget 70

# Compare two vision models
python tools/vision_analyze.py --url http://localhost:8081/ --compare

# Analyze an existing screenshot
python tools/vision_analyze.py --image screenshot.png --task accessibility_audit

# List available tasks
python tools/vision_analyze.py --list-tasks
```

| Task | Best Model | Budget | Use Case |
|---|---|---|---|
| `visual_inspection` | gemma4:12b | 140 | Quick page description |
| `layout_analysis` | gemma4:12b | 280 | Spacing, balance, patterns |
| `ux_review` | gemma4:12b | 280 | Full UX audit with ranked recommendations |
| `debug_rendering` | gemma4:12b | 560 | Visual bug detection |
| `accessibility_audit` | gemma4:12b | 280 | Contrast, focus, readability |
| `design_critique` | gemma4:12b | 280 | Visual design quality |

**Token budgets:** Gemma 4 supports variable resolution. Budget 70 = fast scan, 280 = balanced, 560 = detailed, 1120 = maximum detail.

---

## Advisors

The project uses specialized advisor documents that govern quality across domains. Located in `.omp/advisors/`:

| Advisor | Governs |
|---|---|
| `data-collection.md` | DESE data completeness, district onboarding, scraper health |
| `scraping-system.md` | Scraper architecture, documents table, FTP pipeline, strategy store |
| `code-quality.md` | PHP/Python/SQL/JS conventions, security, anti-patterns |
| `ui-ux.md` | Visual consistency, accessibility, responsive design |
| `seo-web.md` | Search visibility, construction mode, sitemaps |

---

## Deployment

### Production

- **URL:** https://www.parentdataforce.com
- **Server:** LiteSpeed on cPanel
- **Database:** MariaDB 10.11
- **FTP:** ftp.parentdataforce.com

### Deploy Process

```bash
# 1. Test locally
python dev_server.py

# 2. Upload changed files via FTP
#    Use FileZilla or: python tools/ftp_analyzer.py
#    Target: public_html/

# 3. Verify
#    Visit https://parentdataforce.com
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```
DB_ROOT_PASSWORD=...
DB_NAME=pdf_db
DB_USER=pdf_user
DB_PASSWORD=...
APP_SECRET=<random 32+ char string>
APP_ENV=production
APP_DEBUG=false
```

---

## Key Commands

| Task | Command |
|---|---|
| Local dev server | `python dev_server.py` |
| Vision UX review | `python tools/vision_analyze.py --url http://localhost:8081/ --task ux_review` |
| Compare vision models | `python tools/vision_analyze.py --url <url> --compare` |
| Fetch DESE restraints | `python massachusetts/dese/fetch_restraints.py` |
| Scraping terminal | `python -m scraper.cli` |
| FTP deploy | FileZilla or `python tools/ftp_analyzer.py` |

---

## Related Repos

- **[pdf-scraper](https://github.com/p-d-force/pdf-scraper)** — consolidated scraping system: 5 platform scrapers, document pipeline, strategy store, interactive CLI
- **[parentdataforce.com](https://parentdataforce.com)** — production deployment

## License

MIT

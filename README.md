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
Tracking complaints, records, outcomes, and systemic patterns across Massachusetts districts.

---

## Project Map

```
PDFWEBSITE/
│
├── 🌐 WEB ROOT (deployed to parentdataforce.com)
│   ├── index.php              # Homepage
│   ├── config.php             # DB connection & site config
│   ├── search.php             # Site search
│   ├── rss.php                # RSS feed
│   ├── sitemap.php            # XML sitemap
│   ├── robots.txt             # SEO
│   ├── .htaccess              # Apache rules (redirects, security)
│   ├── .env                   # Environment variables (DO NOT COMMIT)
│   ├── .env.example           # Template .env (safe to commit)
│   │
│   ├── data/                  # Data portal (restraint browser, compare tool)
│   │   ├── index.php          # Routes to tabs: ?tab=restraint|trends|compare|more
│   │   └── compare-panel.php  # Interactive district comparison panel
│   │
│   ├── api/                   # JSON API endpoints
│   │   ├── data.php           # Restraint/district data queries
│   │   ├── subscribe.php      # Email subscription
│   │   ├── submit.php         # Tip submission
│   │   ├── search.php         # Search API
│   │   ├── cases.php          # Case data
│   │   └── articles.php       # Article data
│   │
│   ├── appearances/           # Media appearances (news, radio, public comments)
│   │   └── index.php          # DB-backed listing with type filters
│   │
│   ├── articles/              # Articles & analysis
│   │   ├── index.php
│   │   └── article.php
│   │
│   ├── cases/                 # Active cases & investigations
│   │   ├── index.php
│   │   └── case.php
│   │
│   ├── districts/             # District profiles
│   │   ├── index.php
│   │   └── district.php
│   │
│   ├── about/                 # About page
│   ├── submit/                # Tip/data submission form
│   ├── updates/               # Activity updates feed
│   ├── errors/                # Error pages (401, 403, 404, 500)
│   │
│   ├── includes/              # Shared PHP components
│   │   ├── head.php           # <head> with meta, CSS, Chart.js CDN
│   │   ├── header.php         # Navigation bar
│   │   ├── footer.php         # Footer + JS scripts
│   │   ├── Database.php       # PDO wrapper (fetchAll, fetch, fetchColumn)
│   │   ├── Auth.php           # Authentication
│   │   ├── helpers.php        # h(), format_date(), csrf_field() etc.
│   │   └── shortcodes.php     # WordPress-style shortcodes for content
│   │
│   └── assets/                # Static assets
│       ├── css/styles.css     # Main stylesheet (66KB)
│       ├── js/main.js         # Core JS (nav, tabs, filters, search)
│       ├── js/charts.js       # Chart.js — restraint trends
│       ├── js/charts-compare.js # Chart.js — district comparison (standalone)
│       └── images/logo.png    # Site logo
│
├── 🔬 MASSACHUSETTS DATA PIPELINE
│   └── massachusetts/
│       ├── dese/              # DESE scrapers & analysis
│       │   ├── fetch_restraints.py
│       │   ├── fetch_enrollment.py
│       │   ├── fetch_discipline.py
│       │   ├── fetch_attendance.py
│       │   ├── fetch_prs.py
│       │   └── fetch_sped_results.py
│       │
│       └── districts/         # Per-district scrapers
│           └── _template/     # Copy this for new districts
│               └── README.md  # Instructions for meeting/doc scraping
│
├── 🛠 TOOLS (dev utilities)
│   ├── tools/
│   │   ├── vision_analyze.py      # Local model visual inspection (UI/UX, debugging)
│   │   ├── vision-analyzer.md     # Skill doc — agent knows when to call this
│   │   ├── browser_automation.py  # Playwright-based browser automation
│   │   ├── meeting_scrape.py      # Meeting agenda/minute scraper
│   │   ├── dese_enrichment.py     # DESE data enrichment
│   │   ├── restraint_analytics.py # Restraint data analysis
│   │   ├── permalink_build.py     # Static page permalink builder
│   │   ├── ftp_analyzer.py        # FTP connectivity & sync
│   │   ├── url_analyzer.py        # URL structure analysis
│   │   ├── evidence_to_timeline.py # Case evidence timeline builder
│   │   ├── deadline_businessdays.py # Business day deadline calculator
│   │   ├── qa_guard.py            # Quality assurance checks
│   │   ├── updates_hybrid.py      # Hybrid update generation
│   │   ├── status_transition.py   # Case status state machine
│   │   ├── ingest/                # Data ingestion pipeline
│   │   ├── common.py              # Shared utilities
│   │   └── __init__.py
│   │
│   └── scripts/               # One-time & utility scripts
│       ├── setup_sheets_manager.py
│       ├── import_restraint_json.py
│       ├── regenerate_seed_restraint.py
│       ├── migrate_to_firestore.py
│       ├── sheets_sync.py
│       ├── sync_catalog.py
│       ├── sync_drive_data.py
│       ├── cdp_read_sheet.py
│       └── fix_cases_and_articles.py
│
├── 🗄 DATABASE
│   ├── backend/
│   │   ├── schema.sql             # Full database schema
│   │   ├── seed_restraint.sql     # 6,182 school-level restraint records
│   │   ├── seed_enrollment.sql    # 3,168 district enrollment records
│   │   ├── seed_discipline.sql    # 2,779 district discipline records
│   │   ├── seed_attendance.sql    # 3,160 district attendance records
│   │   ├── seed_sped.sql          # SPED outcomes data
│   │   ├── seed_prs.sql           # PRS complaint data
│   │   ├── seed_drive_data.sql    # Aggregate catalog & PRR tracker
│   │   ├── seed_from_metadata.sql # Case metadata seeding
│   │   └── migration_batch2.sql   # Schema migration
│   │
│   ├── dev.db                 # Local SQLite database (4.9MB, 26 tables)
│   └── dev_server.py          # Local dev server (Python, serves PHP via CGI)
│
├── 📚 DOCUMENTATION
│   └── docs/
│       ├── README.md              # (this file)
│       ├── DATA_COLLECTION_PLAYBOOK.md  # Master checklist for new districts
│       ├── ARCHITECTURE.md        # System architecture
│       ├── DB-MAP.md              # Database table map
│       ├── MASTER-PLAN.md         # Overall project roadmap
│       ├── CHANGELOG.md           # Change history
│       ├── DEPLOYMENT.md          # Deployment instructions
│       ├── DATABASE-SETUP.md      # Database setup guide
│       ├── HOSTING-MIGRATION-PLAN.md
│       ├── INGEST-RULES.md        # Data ingestion rules
│       └── ... (additional docs)
│
├── 📦 CONFIG
│   ├── config/
│   │   ├── .firebaserc
│   │   ├── deploy_config.json     # Deployment settings
│   │   ├── docker-compose-updated.yml
│   │   ├── district_sources.json  # District data sources
│   │   ├── site.json              # Site configuration
│   │   ├── field_definitions.json # Admin field definitions
│   │   ├── queue_config.json      # Queue configuration
│   │   └── ingest_rules/          # Ingestion rules
│   ├── .gitignore
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── docker/                    # Docker configs
│
├── 💾 BACKUPS
│   └── backups/
│       └── prod-2026-07-13/       # Pre-compare-tab production snapshot
│           ├── ftp-data_index.php
│           ├── ftp-assets_css_styles.css
│           ├── ftp-assets_js_charts.js
│           └── README.md
│
├── 📧 INTAKE
│   └── intake/
│       └── raw/                   # Raw email files for analysis
│
└── 🧠 AGENT
    └── .hermes/                   # Hermes agent session data
```

---

## Quick Start

```bash
# 1. Local dev server
python dev_server.py
# → http://localhost:8081/

# 2. Visual inspection (UI/UX, debugging)
python tools/vision_analyze.py --url http://localhost:8081/ --task ux_review

# 3. Pull DESE data
python massachusetts/dese/fetch_restraints.py

# 4. Deploy to production
# FTP: ftp.parentdataforce.com / cline@parentdataforce.com
# Upload changed files from web root to public_html/
```

## Key Commands

| Task | Command |
|------|---------|
| Start dev server | `python dev_server.py` |
| Vision analyze URL | `python tools/vision_analyze.py --url <url> --task <task>` |
| Compare vision models | `python tools/vision_analyze.py --url <url> --compare` |
| List vision tasks | `python tools/vision_analyze.py --list-tasks` |
| Fetch DESE restraints | `python massachusetts/dese/fetch_restraints.py` |
| FTP deploy | Use FileZilla or `tools/ftp_analyzer.py` |

## Production

- **URL:** https://www.parentdataforce.com
- **Server:** LiteSpeed on cPanel
- **Database:** MariaDB (g5wwzsi5v4lbdt1q_pdf_db)
- **FTP:** ftp.parentdataforce.com (cline@parentdataforce.com)

## Schema

26 tables including: `districts`, `cases`, `articles`, `restraint_data`, `enrollment_data`, `discipline_data`, `attendance_data`, `sped_data`, `prs_intakes_data`, `media_appearances`, `prr_tracker`, `aggregate_catalog`, `speeches`, `submissions`, `updates`, `resources`, `admin_users`, `admin_sessions`, `system_config` + more.

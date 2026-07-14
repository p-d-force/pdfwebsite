# Parent Data Force — Agent Context

## Project

Independent special education and public accountability advocacy website. Tracking complaints, records, outcomes, and systemic patterns across Massachusetts school districts.

- **Production:** https://www.parentdataforce.com (LiteSpeed/cPanel, MariaDB)
- **Local dev:** `python dev_server.py` → http://localhost:8081/
- **FTP:** ftp.parentdataforce.com

## GitHub Repositories

Two repos under [github.com/p-d-force](https://github.com/p-d-force):

| Repo | URL | Purpose |
|---|---|---|
| **pdf-scraper** | `github.com/p-d-force/pdf-scraper` | Consolidated scraping system — 5 platform scrapers, document pipeline, strategy store, interactive CLI |
| **pdfwebsite** | `github.com/p-d-force/pdfwebsite` | Website + data portal + DESE pipeline + tools |

### Wiki Documentation

Each repo has an extensive GitHub wiki:

| Wiki | Pages | Topics |
|---|---|---|
| [pdf-scraper/wiki](https://github.com/p-d-force/pdf-scraper/wiki) | 9 | Architecture, Scrapers, Document Lifecycle, Strategy Store, CLI Reference, Creating Scrapers, Database Schema, FTP Upload |
| [pdfwebsite/wiki](https://github.com/p-d-force/pdfwebsite/wiki) | 8 | Architecture, Database, Data Pipeline, API Reference, Vision Analysis, Deployment, District Onboarding |

**Wiki governance:** When adding new features, scrapers, or changing architecture, update the corresponding wiki page. The wiki is version-controlled as a separate Git repo (`.wiki.git`). Wiki content is also mirrored in each repo's `wiki/` directory for offline reference.

## Conventions

| Rule | Detail |
|---|---|
| PHP DB access | `Database::fetchAll($sql, [$params])` — never raw PDO |
| Output escaping | `h($var)` for all dynamic HTML output |
| CSS | Component architecture: `assets/css/app.css` imports per-feature files from `components/`. All button styles in `components/buttons.css`. No inline styles in PHP. |
| HTML patterns | `asset('css/app.css')` for static file paths |
| JS | IIFE pattern. Charts in `charts.js` / `charts-compare.js`. Core in `main.js`. |
| Construction mode | `SITE_UNDER_CONSTRUCTION` in `.env` controls global banner |
| Page dev flag | `$page_under_development = true` before includes → noindex + per-page banner |
| Deploy | FTP upload changed files to `public_html/`. Never commit `.env` or credentials. |
| Git hygiene | No credentials, no binaries (>10MB), no DB files. See `.gitignore`. |
| Secrets | Never commit passwords. Use `YOUR_DB_PASSWORD` placeholder in docs. |

## Advisors

Project advisors live in `.omp/advisors/` — consult them when working in their domain:

| Advisor | File | When to consult |
|---|---|---|
| Data Collection | `advisors/data-collection.md` | DESE data, district onboarding, scraper health |
| Scraping System | `advisors/scraping-system.md` | Scraper architecture, documents table, FTP pipeline, strategy store, CLI |
| SEO & Web | `advisors/seo-web.md` | Search visibility, construction mode, sitemaps |
| UI/UX | `advisors/ui-ux.md` | Visual review, accessibility, design tokens |
| Code Quality | `advisors/code-quality.md` | Conventions, security, anti-patterns |

## Key Commands

```bash
# Local dev
python dev_server.py                          # Start dev server → http://localhost:8081/

# Vision analysis (Gemma 4 via Ollama)
python tools/vision_analyze.py --list-tasks   # List available tasks
python tools/vision_analyze.py --url <url> --task ux_review

# DESE data
python massachusetts/dese/fetch_restraints.py # Pull restraint data

# Scraping system
python -m scraper.cli                          # Interactive terminal
python scrapers/apptegy_meetings.py --url <url>

# Git
cd scraper && git push                         # Push scraper changes
git push                                       # Push website changes
```

## Structure

```
├── Web root: index.php, data/, api/, includes/, assets/, articles/, cases/, districts/, appearances/, ...
├── scraper/              # Consolidated scraping system (separate GitHub repo)
│   ├── cli.py            # Interactive terminal
│   ├── core/             # Base classes, pipeline, DB, FTP, strategy store
│   ├── scrapers/         # 5 platform scrapers + template
│   ├── strategies/       # Learned patterns (YAML)
│   └── wiki/             # Wiki content (mirrored on GitHub wiki)
├── massachusetts/        # DESE data pipeline + per-district scrapers
├── tools/                # Vision analyzer, browser automation, meeting scraper, ingest pipeline
├── scripts/              # One-time utility scripts
├── backend/              # schema.sql + seed_*.sql
├── docs/                 # All project documentation
├── wiki/                 # Wiki content (mirrored on GitHub wiki)
├── config/               # JSON configs
├── .omp/advisors/        # Agent governance documents
├── backups/              # Production snapshots (gitignored)
└── dev_server.py, dev.db # Local dev
```

## Update History

| Date | Change |
|---|---|
| 2026-07-14 | Added GitHub repos, wiki governance, scraping system advisor, key commands |

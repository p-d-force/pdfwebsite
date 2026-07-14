# Parent Data Force — Agent Context

## Project

Independent special education and public accountability advocacy website. Tracking complaints, records, outcomes, and systemic patterns across Massachusetts school districts.

- **Production:** https://www.parentdataforce.com (LiteSpeed/cPanel, MariaDB)
- **Local dev:** `python dev_server.py` → http://localhost:8081/
- **FTP:** ftp.parentdataforce.com

## Conventions

| Rule | Detail |
|------|--------|
| PHP DB access | `Database::fetchAll($sql, [$params])` — never raw PDO |
| Output escaping | `h($var)` for all dynamic HTML output |
| HTML patterns | `asset('css/styles.css')` for static file paths |
| CSS | Single file: `assets/css/styles.css`. No inline styles in PHP. |
| JS | IIFE pattern. Charts in `charts.js` / `charts-compare.js`. Core in `main.js`. |
| Construction mode | `SITE_UNDER_CONSTRUCTION` in `.env` controls global banner |
| Page dev flag | `$page_under_development = true` before includes → noindex + per-page banner |
| Deploy | FTP upload changed files to public_html/. Never commit .env or credentials. |

## Advisors

Project advisors live in `.omp/advisors/` — consult them when working in their domain:

| Advisor | File | When to consult |
|---------|------|----------------|
| Data Collection | `advisors/data-collection.md` | DESE data, district onboarding, scraper health |
| SEO & Web | `advisors/seo-web.md` | Search visibility, construction mode, sitemaps |
| UI/UX | `advisors/ui-ux.md` | Visual review, accessibility, design tokens |
| Code Quality | `advisors/code-quality.md` | Conventions, security, anti-patterns |

## Key Commands

```bash
python dev_server.py                        # Start local dev
python tools/vision_analyze.py --list-tasks # List vision analysis tasks
python tools/vision_analyze.py --url <url> --task ux_review  # UI/UX review
python massachusetts/dese/fetch_restraints.py   # Pull DESE data
```

## Structure

```
├── Web root: index.php, data/, api/, includes/, assets/, articles/, cases/, districts/, appearances/, ...
├── massachusetts/         # DESE data pipeline + per-district scrapers
├── tools/                 # Vision analyzer, browser automation, scrapers
├── scripts/               # One-time utility scripts
├── backend/               # schema.sql + seed_*.sql
├── docs/                  # All project documentation
├── config/                # JSON configs
├── backups/               # Production snapshots
└── dev_server.py, dev.db  # Local dev
```

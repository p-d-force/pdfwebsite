# Architecture

The Parent Data Force platform has four layers:

## Layer Diagram

```
┌──────────────────────────────────────────────────┐
│                 Production                       │
│  LiteSpeed / cPanel / MariaDB 10.11             │
│  https://parentdataforce.com                     │
└────────────────────┬─────────────────────────────┘
                     │ FTP deploy
┌────────────────────┴─────────────────────────────┐
│              PHP Web Layer                        │
│  Pages: districts, cases, articles, appearances   │
│  API: /api/data.php, /api/cases.php, ...          │
│  Data Portal: restraint browser, compare tool     │
│  Chart.js: restraint trends, district comparison  │
└────────────────────┬─────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────┴─────┐  ┌────┴─────┐  ┌─────┴──────┐
│   DESE    │  │ District │  │   Vision   │
│  Pipeline │  │ Scrapers │  │   Models   │
│           │  │          │  │            │
│ Socrata   │  │ Apptegy  │  │ Gemma 4    │
│ API +     │  │ CivicEng │  │ via Ollama │
│ HTML      │  │ YouTube  │  │            │
│ parsing   │  │BoardDocs │  │ UI/UX      │
│           │  │          │  │ review     │
└───────────┘  └──────────┘  └────────────┘
```

## PHP Web Layer

- **Pages** (`index.php`, `districts/`, `cases/`, `articles/`, `appearances/`, `about/`, `submit/`, `updates/`)
- **API** (`api/`) — JSON REST endpoints for data queries, search, submissions
- **Data Portal** (`data/`) — interactive restraint browser, trends, district comparison
- **Includes** (`includes/`) — Database PDO wrapper, Auth, helpers (h(), asset(), CSRF), shortcodes

Key conventions:
- All pages use `includes/Database.php` PDO wrapper (never raw `$conn->prepare()`)
- Output escaped with `h()` from `includes/helpers.php`
- CSRF tokens on all forms
- `.htaccess` handles redirects and security headers

## Data Pipeline

Two sources:
1. **DESE Socrata API** (`educationdata.mass.gov`) — REST API for enrollment, discipline, attendance, PRS, SPED
2. **DESE Profiles** (`profiles.doe.mass.edu`) — ASP.NET HTML tables for restraint data

See the [pdf-scraper](https://github.com/p-d-force/pdf-scraper) repo for the consolidated district meeting scraping system.

## Local Development

```bash
python dev_server.py
# → http://localhost:8081/
```

The dev server (`dev_server.py`) is a self-contained Python HTTP server with embedded route handlers, SQLite database, and CSS serving. It mirrors production URL structure without requiring PHP or Apache.

### CSS Architecture

CSS is componentized: `app.css` imports per-feature stylesheets from `components/`. Each component file owns one visual concern — buttons, navigation, hero, footer, data tables, etc. Edit a single component file to change that feature site-wide.

Key components:
- `buttons.css` — all `.btn-*` variants (primary glow, secondary, ghost, tip, sizes, responsive)
- `nav.css` — navigation bar + `.nav-link-tip` and `.nav-link-portal` pill buttons
- `hero.css` — hero section, CTA buttons, stats
- `footer.css` — footer layout, subscribe form
- `data-portal.css` — data browser tables, filter bars, pagination
- `district-dashboard.css` — tabbed district profiles with PRS, restraint, discipline, enrollment tabs

Standalone CSS files (`donate.css`, `admin.css`) are linked directly in `<head>` for page-specific or global overrides.

## Production

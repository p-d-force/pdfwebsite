# Data Pipeline

Massachusetts DESE data collection and district meeting scraping.

## DESE Data Sources

### Socrata API (`educationdata.mass.gov`)

Used for enrollment, discipline, attendance, PRS complaints, and SPED results. REST API with SODA query language:

```
https://educationdata.mass.gov/resource/{dataset}.json?$limit=50000&$offset=0&$where=school_year='2024'
```

Scripts: `massachusetts/dese/fetch_*_socrata.py`

### DESE Profiles (`profiles.doe.mass.edu`)

Used for restraint and seclusion data. ASP.NET HTML tables parsed with Python's `HTMLParser`.

Scripts: `massachusetts/dese/fetch_restraints.py`

## Available Datasets

| Dataset | Script | Method | Records |
|---|---|---|---|
| Physical Restraints | `fetch_restraints.py` | HTML parsing | 6,182 |
| Enrollment Demographics | `fetch_enrollment.py` | HTML parsing | 3,168 |
| Discipline Statistics | `fetch_discipline.py` | HTML parsing | 2,779 |
| Attendance/Chronic Absence | `fetch_attendance.py` | HTML parsing | 3,160 |
| PRS Complaints | `fetch_prs.py` | Socrata API | — |
| SPED Outcomes | `fetch_sped_results.py` | Socrata API | — |

## Running

```bash
# Individual
python massachusetts/dese/fetch_restraints.py

# All via consolidated scraper
python -m scraper.cli
scraper> run dese_all
```

## Output

Each script produces a `backend/seed_*.sql` file with INSERT statements. These seed the local SQLite database and can be imported to MariaDB production.

## District Meeting Scraping

For district-specific meeting agendas, minutes, and videos, see the [pdf-scraper](https://github.com/p-d-force/pdf-scraper) repo.

Four platforms are supported:

| Platform | Method | Status |
|---|---|---|
| Apptegy/Thrillshare | CDN UUID pattern matching | Production |
| CivicEngage | PDF link extraction | Production |
| YouTube | yt-dlp metadata | Production |
| BoardDocs | Playwright (stub) | Needs automation |

## Sync Log

The `sync_log` table tracks data freshness:

| dataset | last_synced | row_count |
|---|---|---|
| restraints | 2026-07-14 | 6182 |
| enrollment | 2026-07-14 | 3168 |
| discipline | 2026-07-14 | 2779 |
| attendance | 2026-07-14 | 3160 |

## Enrichment

After bulk import, `tools/dese_enrichment.py` computes derived metrics:
- Restraint rate per 100 students
- District comparison percentiles
- Year-over-year trends
- Suppression flag detection (cells hidden by DESE for small N)

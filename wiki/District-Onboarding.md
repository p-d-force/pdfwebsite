# District Onboarding

Process for adding a new Massachusetts school district to the platform.

## Reference

Full checklist: [`docs/DATA_COLLECTION_PLAYBOOK.md`](../docs/DATA_COLLECTION_PLAYBOOK.md)

## Quick Onboarding

### 1. Database Entry

```sql
INSERT INTO districts (district_name, district_code, slug, county, grade_span)
VALUES ('New District', '00000000', 'new-district', 'County', 'PK-12');
```

Required fields: `district_name`, `district_code` (8-digit DESE), `slug`, `is_active=1`.

### 2. Pull DESE Data

```bash
python massachusetts/dese/fetch_restraints.py
python massachusetts/dese/fetch_enrollment.py
python massachusetts/dese/fetch_discipline.py
python massachusetts/dese/fetch_attendance.py
python massachusetts/dese/fetch_prs.py
python massachusetts/dese/fetch_sped_results.py
```

Or via the consolidated scraper:

```bash
python -m scraper.cli
scraper> run dese_all
```

### 3. Identify Website Platform

Check the district's website URL:

| Pattern | Platform | Scraper |
|---|---|---|
| `*.apptegy.net` or `thrillshare.com` | Apptegy | `apptegy_meetings` |
| `civicengage.com` or `/AgendaCenter/` | CivicEngage | `civicengage_meetings` |
| `boarddocs.com` | BoardDocs | `boarddocs_meetings` (stub) |
| YouTube channel | Video | `youtube_meetings` |
| Other | Custom | Create new scraper |

### 4. Scrape Meeting Documents

```bash
# Apptegy
python scrapers/apptegy_meetings.py --url https://district.apptegy.net/

# CivicEngage
python scrapers/civicengage_meetings.py --url https://www.town.ma.us/AgendaCenter/

# YouTube
python scrapers/youtube_meetings.py --channel @districtschools
```

### 5. Collect Contact Info

From the district website:
- Records Access Officer (RAO) name and email
- Superintendent name and email
- School Committee chair and contact
- SEPAC contact

### 6. Create District Folder

```bash
mkdir massachusetts/districts/<district_code>/
cp massachusetts/districts/_template/README.md massachusetts/districts/<district_code>/
```

### 7. Set Up Monitoring

- Google Alert: `"[District Name] special education"`
- Add to `config/district_sources.json`
- Create PRR tracker entry in `prr_tracker` table

## Data Collection Checklist

Full playbook: [`docs/DATA_COLLECTION_PLAYBOOK.md`](../docs/DATA_COLLECTION_PLAYBOOK.md)

Covers:
- District identity (DESE code, county, grade span, RAO contact)
- Enrollment demographics (total, % disadvantaged, % EL, % SPED)
- Discipline data (suspension, expulsion, arrest rates)
- Restraint data (incidents, injuries, suppression flags)
- Attendance (chronic absence rates)
- SPED outcomes (graduation, dropout, inclusion rates)
- Public records history (PRR cases, SPR appeals, PRS complaints)
- Financial data (budget, per-pupil spending, SPED costs)
- Meeting documents (agendas, minutes, videos — past 2 years)

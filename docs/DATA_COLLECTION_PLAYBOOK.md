# Massachusetts School District Data Collection Playbook

> **Purpose:** When investigating a new district or school, this is the authoritative checklist of what data to collect, where to find it, and how it should be linked in the database.  
> **Managed by:** Data Collection Advisor (auto-updated as new sources are discovered)  
> **Last updated:** 2026-07-14

---

## 1. District Identity

| Field | Source | Priority |
|-------|--------|----------|
| District name | DESE Profiles | Required |
| District code (8-digit) | DESE Profiles | Required |
| County | DESE / Wikipedia | High |
| Type (Public/Charter/Vocational) | DESE | Required |
| Grade span (PK-12, K-8, etc.) | DESE | High |
| URL (district website) | Web search / DESE | High |
| Superintendent name + email | District website | Medium |
| School Committee chair + contact | District website | Medium |
| SEPAC contact | District website | Medium |
| Records Access Officer (RAO) name + email | District website / SPR | Required |
| Social media (Facebook, Twitter) | Web search | Low |

## 2. Enrollment Demographics (per school year)

| Field | Source | Priority |
|-------|--------|----------|
| Total enrollment | DESE enrollment export | Required |
| % Economically disadvantaged | DESE enrollment export | Required |
| % English Learners | DESE enrollment export | Required |
| % Students with IEPs (SPED) | DESE enrollment export | Required |
| % High needs | DESE enrollment export | Medium |
| % By race/ethnicity | DESE enrollment export | Medium |

## 3. Discipline Data (per school year)

| Field | Source | Priority |
|-------|--------|----------|
| Total students disciplined | DESE discipline export | Required |
| % In-school suspension | DESE discipline export | Required |
| % Out-of-school suspension | DESE discipline export | Required |
| % Expulsion | DESE discipline export | Medium |
| % Emergency removal | DESE discipline export | Low |
| % Arrest / law enforcement referral | DESE discipline export | Low |

## 4. Restraint & Seclusion Data (per school year, school-level)

| Field | Source | Priority |
|-------|--------|----------|
| Total restraints | DESE restraint export | Required |
| Students restrained | DESE restraint export | Required |
| Total injuries during restraint | DESE restraint export | Required |
| Restraint rate per 100 enrolled | DESE restraint export (computed) | Required |
| Suppression flags (cells hidden) | DESE restraint export | Required |
| School-by-school breakdown | DESE restraint export | High |

## 5. Attendance Data (per school year)

| Field | Source | Priority |
|-------|--------|----------|
| Average attendance rate | DESE attendance export | Required |
| % Chronically absent (10+ days) | DESE attendance export | Required |
| % Chronically absent (20+ days) | DESE attendance export | Medium |
| Average days absent | DESE attendance export | Low |

## 6. SPED Outcomes

| Field | Source | Priority |
|-------|--------|----------|
| SPED graduation rate | DESE SPED results | Medium |
| SPED dropout rate | DESE SPED results | Medium |
| % SPED in full inclusion (>80%) | DESE SPED results | Medium |
| % SPED in substantial separate settings | DESE SPED results | Medium |

## 7. Public Records / Advocacy

| Field | Source | Priority |
|-------|--------|----------|
| Active PRR cases | PRS tracker (internal) | Required |
| SPR appeal history | SPR determinations | Required |
| PRS complaints filed | PRS intake (internal) | Required |
| School Committee meeting schedule | District website / Apptegy | High |
| Meeting agendas (past 2 years) | District website / Apptegy / CivicEngage | High |
| Meeting minutes (past 2 years) | District website / Apptegy / CivicEngage | High |
| Meeting videos / recordings | YouTube / district website | Medium |
| Policy manual URL | District website | Medium |
| DESE coordinated program reviews | DESE website | Medium |

## 8. Media & Appearances

| Field | Source | Priority |
|-------|--------|----------|
| News articles mentioning district | Web search / Google Alerts | Medium |
| Radio/TV appearances about district | Web search | Low |
| Public comments / testimony | Internal tracking | Low |

## 9. Local Model / AI Data

| Field | Source | Priority |
|-------|--------|----------|
| District-specific scraped pages | Local scrapers | Ongoing |
| Meeting transcriptions | YouTube subtitles / Whisper | Ongoing |
| Document OCR (PDFs) | Downloaded minutes/agendas | Ongoing |
| Email correspondence archives | Gmail export | Internal only |

---

## Collection Process

### Phase 1: DESE Bulk Import
```
python scripts/fetch_dese_restraints.py
python scripts/fetch_dese_enrollment.py
python scripts/fetch_dese_discipline.py
python scripts/fetch_dese_attendance.py
python scripts/fetch_dese_prs.py
```

### Phase 2: District Website Scraping
```
python massachusetts/districts/<district>/scrape_meetings.py
python massachusetts/districts/<district>/scrape_documents.py
```

### Phase 3: Enrichment
```
python massachusetts/dese/enrich_district.py --district <code>
python massachusetts/dese/analyze_restraint.py --district <code>
```

### Phase 4: Media & Web Monitoring
```
python tools/vision_analyze.py --url <district-website> --task visual_inspection
# Manual: set up Google Alerts for "[District Name] special education"
```

---

## Database Linkage

All collected data should link to the `districts` table via `district_code` (8-digit DESE code).
School-level data links via `school_code` (8-digit DESE code).

Tables that accept district data:
- `restraint_data` (school-level, has `district_code`)
- `enrollment_data` (district-level)
- `discipline_data` (district-level)
- `attendance_data` (district-level)
- `media_appearances` (`district_code` nullable)
- `cases` (via `district_code`)
- `prr_tracker` (via agency/district reference)

---

## New District Onboarding Checklist

- [ ] Create district entry in `districts` table with DESE 8-digit code
- [ ] Run Phase 1 scripts to pull all DESE datasets
- [ ] Scrape district website for committee meeting schedule
- [ ] Download meeting agendas/minutes for past 2 years
- [ ] Identify Records Access Officer contact
- [ ] Set up Google Alert for district name + "special education"
- [ ] Create district folder: `massachusetts/districts/<code>/`
- [ ] Link any existing PRR/case data by district code
- [ ] Add to district coverage section on homepage

---

## 8. District Governance & Meetings

| Field | Source | Priority |
|-------|--------|----------|
| School Committee member names + roles | District website | Required |
| Meeting schedule (day/time, frequency) | District website | Required |
| Agenda posting location/URL | District website | Required |
| Minutes access method (PDF, HTML, BoardDocs) | District website | Required |
| Meeting video/recording URL | YouTube / district site | High |
| Subcommittee assignments | District website | Medium |
| Budget hearing schedule | District website | Medium |
| Platform type (Apptegy, CivicEngage, BoardDocs, custom) | URL inspection | Required |

## 9. Financial & Budget

| Field | Source | Priority |
|-------|--------|----------|
| Total annual budget | DESE / district website | High |
| Special education budget share | DESE / district website | High |
| Per-pupil spending | DESE | High |
| SPED transportation costs | District website / PRR | Medium |
| Out-of-district placement costs (tuition + transport) | District website / PRR | Medium |
| Grants & federal funding breakdown | DESE | Low |

## 10. Personnel & Staffing

| Field | Source | Priority |
|-------|--------|----------|
| Superintendent name + email | District website | Required |
| SPED Director name + contact | District website | High |
| Records Access Officer (RAO) name + email | District website / SPR | Required |
| BCBA count (Board Certified Behavior Analysts) | PRR / district org chart | Medium |
| School psychologist count | DESE / district website | Medium |
| Adjustment counselor count | DESE / district website | Medium |
| Paraprofessional-to-student ratios | PRR / district website | Low |
| Staff turnover rates | DESE | Low |

## 11. Legal & Compliance History

| Field | Source | Priority |
|-------|--------|----------|
| Past DESE PRS complaints (Problem Resolution System) | DESE | High |
| Past BSEA cases (Bureau of Special Education Appeals) | BSEA database | High |
| OCR complaints (Office for Civil Rights) | OCR database | Medium |
| SPR appeal history (Supervisor of Public Records) | SPR determinations | High |
| Pending litigation | Web search / court dockets | Medium |
| Coordinated Program Review findings | DESE | Medium |
| Tiered Focus Monitoring status | DESE | Medium |

## 12. PRR History & Responsiveness

| Field | Source | Priority |
|-------|--------|----------|
| Past PRRs filed against district | Internal PRR tracker | Required |
| RAO response patterns (fast, slow, combative) | Internal tracking | High |
| Average response time | Internal tracking | High |
| Fee estimate frequency & amounts | Internal tracking | Medium |
| SPR appeal rate (% of PRRs appealed) | Internal tracking | Medium |
| Common exemption claims | Internal tracking | Medium |

## 13. Website & Content Sources

| Field | Source | Priority |
|-------|--------|----------|
| Public calendar URL | District website | Required |
| Agenda PDF download pattern | URL inspection | High |
| Minute PDF download pattern | URL inspection | High |
| Policy manual URL | District website | Medium |
| SEPAC page URL | District website | Medium |
| Staff directory URL | District website | Low |
| Social media accounts (Facebook, Twitter) | Web search | Low |

---

## Scraper Development Checklist

When building a district scraper, confirm:

- [ ] Platform detected (Apptegy/CivicEngage/BoardDocs/custom)
- [ ] Meeting calendar accessible via URL or JS rendering
- [ ] Agenda PDFs downloadable (check for auth walls or CDN patterns)
- [ ] Meeting minutes accessible (same or different URL pattern)
- [ ] Videos available on YouTube channel
- [ ] Rate limiting — add delays between requests (2-5s)
- [ ] Output schema matches `meetings.json` spec (date, type, agenda_url, minutes_url, video_url)

## Administrator Roles for Data Collection

| Role | Responsibility |
|------|---------------|
| **Data Collection Advisor** | Owns this playbook. Updates as new sources/data types discovered. Reviews district intake checklists. |
| **DESE Pipeline Operator** | Runs bulk DESE fetchers. Monitors for new school years. |
| **District Scout** | Onboards new districts — fills Phase 1-2 checklists. |
| **Media Monitor** | Tracks news mentions, radio appearances, public comments per district. |

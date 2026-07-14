# Database

26 tables across 5 domains. Authoritative schema at `backend/schema.sql`.

## Content Tables

| Table | Purpose | Key Columns |
|---|---|---|
| `districts` | MA school districts | district_code (8-digit DESE), slug, county, grade_span |
| `cases` | Legal cases, SPR appeals, PRS complaints | case_number, case_type, status, filed_date, district_id FK |
| `case_documents` | Files attached to cases | case_id FK, document_type, file_url |
| `articles` | Analysis and reporting | slug, article_type, published_date |
| `article_case_links` | Article-to-case M:N | article_id FK, case_id FK |
| `article_district_links` | Article-to-district M:N | article_id FK, district_id FK |
| `article_tags` | Taxonomy | tag_name, slug |
| `speeches` | Public testimony | speaker_name, event_date, transcript |
| `updates` | Activity feed | update_type, published_date |
| `submissions` | User-submitted tips | submitter_email, submission_type, status |
| `resources` | Reference materials | resource_type, file_url, external_url |

## Scraped Data Tables

| Table | Records | Refresh | Key Columns |
|---|---|---|---|
| `restraint_data` | 6,182 | Annual | district_code, school_year, total_incidents |
| `enrollment_data` | 3,168 | Annual | district_code, school_year, sped_pct, low_income_pct |
| `discipline_data` | 2,779 | Annual | district_code, school_year, pct_in_school_susp |
| `attendance_data` | 3,160 | Annual | district_code, school_year, chronically_absent_10_pct |
| `sped_results` | — | Annual | district_code, school_year, sped_grad_rate |
| `prs_data` | — | Annual | district_code, school_year, prs_level, prs_rating |
| `prr_tracker` | — | Ongoing | district_code, prr_type, prr_status |
| `aggregate_catalog` | — | Metadata | dataset_name, source_agency, update_frequency |

All scraped tables use `(district_code, school_year)` as a unique key.

## Admin Tables

| Table | Purpose |
|---|---|
| `admin_users` | Authentication (bcrypt password_hash) |
| `admin_sessions` | Session tokens with expiry |
| `audit_log` | Change tracking (JSON old_values/new_values) |
| `system_config` | Site-wide key-value settings |

## Pipeline

| Table | Purpose |
|---|---|
| `sync_log` | Data freshness — dataset name, last_synced, row_count |

## Document Tracking (Scraper System)

Three tables from `scraper/migration/documents_table.sql`:

| Table | Purpose |
|---|---|
| `documents` | Every scraped/downloaded/uploaded document |
| `source_systems` | Known scraping target registry |
| `scrape_strategies` | Learned pattern knowledge base |

## Seed Data

Six districts are pre-seeded: Attleboro (00160000), Fall River (00950000), Whitman-Hanson (07800000), Bridgewater-Raynham (06250000), Norton (02000000), DESE (00000000).

## Conventions

- All tables use InnoDB, utf8mb4
- Foreign keys with ON DELETE SET NULL or CASCADE
- `created_at`/`updated_at` on every content table
- UNIQUE constraints on natural keys (district_code + school_year)
- JSON columns for audit_log old_values/new_values

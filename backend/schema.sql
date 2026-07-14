-- ============================================================
-- PDFWEBSITE Unified Schema — MariaDB 10.11
-- ============================================================
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- Content Tables
-- ============================================================

CREATE TABLE districts (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    district_name   VARCHAR(255)    NOT NULL,
    district_code   VARCHAR(10)     NOT NULL,
    slug            VARCHAR(255)    NOT NULL UNIQUE,
    region          VARCHAR(100)    NULL,
    county          VARCHAR(100)    NULL,
    municipality    VARCHAR(255)    NULL,
    grade_span      VARCHAR(50)     NULL,
    total_schools   INT UNSIGNED    NULL,
    total_students  INT UNSIGNED    NULL,
    total_teachers  INT UNSIGNED    NULL,
    student_per_teacher DECIMAL(5,1) NULL,
    homepage_url    VARCHAR(512)    NULL,
    logo_url        VARCHAR(512)    NULL,
    description     TEXT            NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_district_code (district_code),
    INDEX idx_region (region),
    INDEX idx_county (county),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE cases (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    case_number     VARCHAR(100)    NOT NULL UNIQUE,
    title           VARCHAR(512)    NOT NULL,
    slug            VARCHAR(512)    NOT NULL UNIQUE,
    case_type       VARCHAR(100)    NULL,
    status          VARCHAR(50)     NULL,
    filed_date      DATE            NULL,
    resolved_date   DATE            NULL,
    court           VARCHAR(255)    NULL,
    judge           VARCHAR(255)    NULL,
    plaintiff       VARCHAR(512)    NULL,
    defendant       VARCHAR(512)    NULL,
    district_id     INT UNSIGNED    NULL,
    summary         TEXT            NULL,
    body            LONGTEXT        NULL,
    ruling          TEXT            NULL,
    settlement      TEXT            NULL,
    external_url    VARCHAR(1024)   NULL,
    docket_url      VARCHAR(1024)   NULL,
    is_featured     TINYINT(1)      NOT NULL DEFAULT 0,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    sort_order      INT             NOT NULL DEFAULT 0,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_case_number (case_number),
    INDEX idx_district_id (district_id),
    INDEX idx_case_type (case_type),
    INDEX idx_status (status),
    INDEX idx_filed_date (filed_date),
    INDEX idx_is_featured (is_featured),
    INDEX idx_is_active (is_active),
    CONSTRAINT fk_cases_district FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE case_documents (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    case_id         INT UNSIGNED    NOT NULL,
    document_name   VARCHAR(512)    NOT NULL,
    document_type   VARCHAR(100)    NULL,
    file_url        VARCHAR(1024)   NOT NULL,
    file_size       INT UNSIGNED    NULL,
    mime_type       VARCHAR(100)    NULL,
    sort_order      INT             NOT NULL DEFAULT 0,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_case_id (case_id),
    INDEX idx_document_type (document_type),
    CONSTRAINT fk_case_documents_case FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE articles (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(512)    NOT NULL,
    slug            VARCHAR(512)    NOT NULL UNIQUE,
    subtitle        VARCHAR(512)    NULL,
    author          VARCHAR(255)    NULL,
    source_name     VARCHAR(255)    NULL,
    source_url      VARCHAR(1024)   NULL,
    excerpt         TEXT            NULL,
    body            LONGTEXT        NULL,
    image_url       VARCHAR(1024)   NULL,
    thumbnail_url   VARCHAR(1024)   NULL,
    published_date  DATE            NULL,
    article_type    VARCHAR(50)     NULL,
    is_featured     TINYINT(1)      NOT NULL DEFAULT 0,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    sort_order      INT             NOT NULL DEFAULT 0,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_slug (slug),
    INDEX idx_article_type (article_type),
    INDEX idx_published_date (published_date),
    INDEX idx_is_featured (is_featured),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE article_case_links (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    article_id      INT UNSIGNED    NOT NULL,
    case_id         INT UNSIGNED    NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    UNIQUE KEY uq_article_case (article_id, case_id),
    INDEX idx_article_id (article_id),
    INDEX idx_case_id (case_id),
    CONSTRAINT fk_acl_article FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    CONSTRAINT fk_acl_case FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE article_district_links (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    article_id      INT UNSIGNED    NOT NULL,
    district_id     INT UNSIGNED    NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    UNIQUE KEY uq_article_district (article_id, district_id),
    INDEX idx_article_id (article_id),
    INDEX idx_district_id (district_id),
    CONSTRAINT fk_adl_article FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    CONSTRAINT fk_adl_district FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE article_tags (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    tag_name        VARCHAR(100)    NOT NULL UNIQUE,
    slug            VARCHAR(100)    NOT NULL UNIQUE,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_tag_name (tag_name),
    INDEX idx_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE article_tag_links (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    article_id      INT UNSIGNED    NOT NULL,
    tag_id          INT UNSIGNED    NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    UNIQUE KEY uq_article_tag (article_id, tag_id),
    INDEX idx_article_id (article_id),
    INDEX idx_tag_id (tag_id),
    CONSTRAINT fk_atl_article FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    CONSTRAINT fk_atl_tag FOREIGN KEY (tag_id) REFERENCES article_tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE speeches (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(512)    NOT NULL,
    slug            VARCHAR(512)    NOT NULL UNIQUE,
    speaker_name    VARCHAR(255)    NULL,
    speaker_title   VARCHAR(255)    NULL,
    event_name      VARCHAR(255)    NULL,
    event_date      DATE            NULL,
    venue           VARCHAR(255)    NULL,
    video_url       VARCHAR(1024)   NULL,
    transcript      LONGTEXT        NULL,
    excerpt         TEXT            NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    sort_order      INT             NOT NULL DEFAULT 0,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_slug (slug),
    INDEX idx_event_date (event_date),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE updates (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(512)    NOT NULL,
    slug            VARCHAR(512)    NOT NULL UNIQUE,
    update_type     VARCHAR(50)     NULL,
    body            LONGTEXT        NULL,
    excerpt         TEXT            NULL,
    source_url      VARCHAR(1024)   NULL,
    published_date  DATETIME        NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    is_featured     TINYINT(1)      NOT NULL DEFAULT 0,
    sort_order      INT             NOT NULL DEFAULT 0,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_slug (slug),
    INDEX idx_update_type (update_type),
    INDEX idx_published_date (published_date),
    INDEX idx_is_active (is_active),
    INDEX idx_is_featured (is_featured)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE submissions (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    submitter_name  VARCHAR(255)    NULL,
    submitter_email VARCHAR(255)    NULL,
    submitter_org   VARCHAR(255)    NULL,
    title           VARCHAR(512)    NOT NULL,
    body            LONGTEXT        NULL,
    file_url        VARCHAR(1024)   NULL,
    submission_type VARCHAR(50)     NULL,
    status          VARCHAR(50)     NOT NULL DEFAULT 'pending',
    reviewed_by     INT UNSIGNED    NULL,
    reviewed_at     DATETIME        NULL,
    notes           TEXT            NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    submitted_at    DATETIME        NOT NULL DEFAULT NOW(),
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_status (status),
    INDEX idx_submission_type (submission_type),
    INDEX idx_submitted_at (submitted_at),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE resources (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(512)    NOT NULL,
    slug            VARCHAR(512)    NOT NULL UNIQUE,
    resource_type   VARCHAR(50)     NULL,
    description     TEXT            NULL,
    body            LONGTEXT        NULL,
    file_url        VARCHAR(1024)   NULL,
    external_url    VARCHAR(1024)   NULL,
    author          VARCHAR(255)    NULL,
    published_date  DATE            NULL,
    is_featured     TINYINT(1)      NOT NULL DEFAULT 0,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    sort_order      INT             NOT NULL DEFAULT 0,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_slug (slug),
    INDEX idx_resource_type (resource_type),
    INDEX idx_is_featured (is_featured),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Scraped Data Tables
-- ============================================================

CREATE TABLE restraint_data (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    district_name       VARCHAR(255)    NOT NULL,
    district_code       VARCHAR(10)     NOT NULL,
    school_year         VARCHAR(10)     NOT NULL,
    total_enrollment    INT             NULL,
    students_restrained INT             NULL,
    pct_restrained      DECIMAL(5,2)    NULL,
    total_incidents     INT             NULL,
    injuries_staff      INT             NULL,
    injuries_students   INT             NULL,
    incidents_per_100   DECIMAL(5,2)    NULL,
    created_at          DATETIME        NOT NULL DEFAULT NOW(),
    updated_at          DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    UNIQUE KEY uq_restraint_district_yr (district_code, school_year),
    INDEX idx_district_name (district_name),
    INDEX idx_district_code (district_code),
    INDEX idx_school_year (school_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE discipline_data (
    id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    district_name           VARCHAR(255)    NOT NULL,
    district_code           VARCHAR(10)     NOT NULL,
    school_year             VARCHAR(10)     NOT NULL,
    students                INT             NULL,
    students_disciplined    INT             NULL,
    pct_in_school_susp      DECIMAL(5,2)    NULL,
    pct_out_school_susp     DECIMAL(5,2)    NULL,
    pct_expulsion           DECIMAL(5,2)    NULL,
    pct_alt_setting         DECIMAL(5,2)    NULL,
    pct_emergency_removal   DECIMAL(5,2)    NULL,
    pct_arrest              DECIMAL(5,2)    NULL,
    pct_law_enforce         DECIMAL(5,2)    NULL,
    created_at              DATETIME        NOT NULL DEFAULT NOW(),
    updated_at              DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    UNIQUE KEY uq_discipline_district_yr (district_code, school_year),
    INDEX idx_district_name (district_name),
    INDEX idx_district_code (district_code),
    INDEX idx_school_year (school_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE enrollment_data (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    district_name       VARCHAR(255)    NOT NULL,
    district_code       VARCHAR(10)     NOT NULL,
    school_year         VARCHAR(10)     NOT NULL,
    high_needs_num      INT             NULL,
    high_needs_pct      DECIMAL(5,1)    NULL,
    el_num              INT             NULL,
    el_pct              DECIMAL(5,1)    NULL,
    flne_num            INT             NULL,
    flne_pct            DECIMAL(5,1)    NULL,
    low_income_num      INT             NULL,
    low_income_pct      DECIMAL(5,1)    NULL,
    sped_num            INT             NULL,
    sped_pct            DECIMAL(5,1)    NULL,
    created_at          DATETIME        NOT NULL DEFAULT NOW(),
    updated_at          DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    UNIQUE KEY uq_enrollment_district_yr (district_code, school_year),
    INDEX idx_district_name (district_name),
    INDEX idx_district_code (district_code),
    INDEX idx_school_year (school_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sped_results (
    id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    district_name           VARCHAR(255)    NOT NULL,
    district_code           VARCHAR(10)     NOT NULL,
    school_year             VARCHAR(10)     NOT NULL,
    sped_grad_rate          DECIMAL(5,1)    NULL,
    sped_dropout_rate       DECIMAL(5,1)    NULL,
    lre_full_incl_pct       DECIMAL(5,1)    NULL,
    parent_involve_pct      DECIMAL(5,1)    NULL,
    post_school_engage_pct  DECIMAL(5,1)    NULL,
    created_at              DATETIME        NOT NULL DEFAULT NOW(),
    updated_at              DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    UNIQUE KEY uq_sped_results_district_yr (district_code, school_year),
    INDEX idx_district_name (district_name),
    INDEX idx_district_code (district_code),
    INDEX idx_school_year (school_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE attendance_data (
    id                          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    district_name               VARCHAR(255)    NOT NULL,
    district_code               VARCHAR(10)     NOT NULL,
    school_year                 VARCHAR(10)     NOT NULL,
    attendance_rate             DECIMAL(5,1)    NULL,
    avg_absences                DECIMAL(5,1)    NULL,
    absent_10_plus_pct          DECIMAL(5,1)    NULL,
    chronically_absent_10_pct   DECIMAL(5,1)    NULL,
    chronically_absent_20_pct   DECIMAL(5,1)    NULL,
    created_at                  DATETIME        NOT NULL DEFAULT NOW(),
    updated_at                  DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    UNIQUE KEY uq_attendance_district_yr (district_code, school_year),
    INDEX idx_district_name (district_name),
    INDEX idx_district_code (district_code),
    INDEX idx_school_year (school_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE prs_data (
    id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    district_name           VARCHAR(255)    NOT NULL,
    district_code           VARCHAR(10)     NOT NULL,
    school_year             VARCHAR(10)     NOT NULL,
    prs_level               VARCHAR(50)     NULL,
    prs_rating              VARCHAR(50)     NULL,
    indicator_1_score       DECIMAL(5,1)    NULL,
    indicator_2_score       DECIMAL(5,1)    NULL,
    indicator_3_score       DECIMAL(5,1)    NULL,
    indicator_4_score       DECIMAL(5,1)    NULL,
    indicator_5_score       DECIMAL(5,1)    NULL,
    indicator_6_score       DECIMAL(5,1)    NULL,
    indicator_7_score       DECIMAL(5,1)    NULL,
    criterion_1_score       DECIMAL(5,1)    NULL,
    criterion_2_score       DECIMAL(5,1)    NULL,
    created_at              DATETIME        NOT NULL DEFAULT NOW(),
    updated_at              DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    UNIQUE KEY uq_prs_district_yr (district_code, school_year),
    INDEX idx_district_name (district_name),
    INDEX idx_district_code (district_code),
    INDEX idx_school_year (school_year),
    INDEX idx_prs_level (prs_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE aggregate_catalog (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    dataset_name        VARCHAR(100)    NOT NULL,
    dataset_slug        VARCHAR(100)    NOT NULL UNIQUE,
    source_agency       VARCHAR(255)    NULL,
    source_url          TEXT            NULL,
    source_description  TEXT            NULL,
    source_last_updated VARCHAR(100)    NULL,
    update_frequency    VARCHAR(50)     NULL,
    data_format         VARCHAR(50)     NULL,
    file_url            VARCHAR(1024)   NULL,
    field_count         INT             NULL,
    record_count        INT             NULL,
    notes               TEXT            NULL,
    is_active           TINYINT(1)      NOT NULL DEFAULT 1,
    created_at          DATETIME        NOT NULL DEFAULT NOW(),
    updated_at          DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    INDEX idx_dataset_name (dataset_name),
    INDEX idx_dataset_slug (dataset_slug),
    INDEX idx_source_agency (source_agency),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE prr_tracker (
    id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    district_name           VARCHAR(255)    NOT NULL,
    district_code           VARCHAR(10)     NOT NULL,
    school_year             VARCHAR(10)     NOT NULL,
    prr_type                VARCHAR(100)    NULL,
    prr_status              VARCHAR(50)     NULL,
    initiated_date          DATE            NULL,
    target_date             DATE            NULL,
    completed_date          DATE            NULL,
    findings_summary        TEXT            NULL,
    corrective_action       TEXT            NULL,
    url                     VARCHAR(1024)   NULL,
    created_at              DATETIME        NOT NULL DEFAULT NOW(),
    updated_at              DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    UNIQUE KEY uq_prr_district_yr_type (district_code, school_year, prr_type),
    INDEX idx_district_name (district_name),
    INDEX idx_district_code (district_code),
    INDEX idx_school_year (school_year),
    INDEX idx_prr_status (prr_status),
    INDEX idx_prr_type (prr_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Admin / Auth Tables
-- ============================================================

CREATE TABLE admin_users (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(100)    NOT NULL UNIQUE,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    display_name    VARCHAR(255)    NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(50)     NOT NULL DEFAULT 'editor',
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    last_login_at   DATETIME        NULL,
    last_login_ip   VARCHAR(45)     NULL,
    reset_token     VARCHAR(255)    NULL,
    reset_expires   DATETIME        NULL,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    UNIQUE KEY uq_admin_username (username),
    UNIQUE KEY uq_admin_email (email),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE admin_sessions (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    admin_user_id   INT UNSIGNED    NOT NULL,
    session_token   VARCHAR(255)    NOT NULL UNIQUE,
    ip_address      VARCHAR(45)     NULL,
    user_agent      VARCHAR(512)    NULL,
    expires_at      DATETIME        NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    INDEX idx_session_token (session_token),
    INDEX idx_admin_user_id (admin_user_id),
    INDEX idx_expires_at (expires_at),
    CONSTRAINT fk_admin_sessions_user FOREIGN KEY (admin_user_id) REFERENCES admin_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE audit_log (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    admin_user_id   INT UNSIGNED    NULL,
    action          VARCHAR(100)    NOT NULL,
    entity_type     VARCHAR(100)    NULL,
    entity_id       INT UNSIGNED    NULL,
    old_values      JSON            NULL,
    new_values      JSON            NULL,
    ip_address      VARCHAR(45)     NULL,
    user_agent      VARCHAR(512)    NULL,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    INDEX idx_admin_user_id (admin_user_id),
    INDEX idx_action (action),
    INDEX idx_entity_type (entity_type),
    INDEX idx_entity_id (entity_id),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_audit_log_user FOREIGN KEY (admin_user_id) REFERENCES admin_users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE system_config (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    config_key      VARCHAR(100)    NOT NULL UNIQUE,
    config_value    TEXT            NULL,
    config_type     VARCHAR(50)     NOT NULL DEFAULT 'string',
    description     VARCHAR(512)    NULL,
    is_public       TINYINT(1)      NOT NULL DEFAULT 0,
    created_at      DATETIME        NOT NULL DEFAULT NOW(),
    updated_at      DATETIME        NOT NULL DEFAULT NOW() ON UPDATE NOW(),
    UNIQUE KEY uq_config_key (config_key),
    INDEX idx_is_public (is_public)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Pipeline / Sync Log Table
-- ============================================================

CREATE TABLE sync_log (
    dataset             VARCHAR(50)     PRIMARY KEY,
    source_url          TEXT            NULL,
    last_synced         DATETIME        NULL,
    row_count           INT             NULL,
    source_last_updated VARCHAR(100)    NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Seed Data
-- ============================================================

INSERT IGNORE INTO districts (id, district_name, district_code, slug, region, county, municipality, grade_span, total_schools, total_students, description, is_active) VALUES
(1, 'Boston Public Schools',       '00350000', 'boston-public-schools',        'Greater Boston', 'Suffolk',   'Boston',          'PK-12', 123, 46000, 'The largest public school district in Massachusetts, serving the City of Boston.', 1),
(2, 'Springfield Public Schools',  '02810000', 'springfield-public-schools',   'Pioneer Valley', 'Hampden',   'Springfield',     'PK-12',  66, 25000, 'Public school district serving Springfield, Massachusetts.', 1),
(3, 'Worcester Public Schools',    '03480000', 'worcester-public-schools',     'Central MA',     'Worcester', 'Worcester',       'PK-12',  50, 24000, 'Public school district serving Worcester, Massachusetts.', 1),
(4, 'Brockton Public Schools',     '00440000', 'brockton-public-schools',      'Southeast MA',   'Plymouth',  'Brockton',        'PK-12',  24, 15000, 'Public school district serving Brockton, Massachusetts.', 1),
(5, 'Lawrence Public Schools',     '01490000', 'lawrence-public-schools',      'Northeast MA',   'Essex',     'Lawrence',        'PK-12',  33, 13000, 'Public school district serving Lawrence, Massachusetts, in state receivership.', 1),
(6, 'Holyoke Public Schools',      '01370000', 'holyoke-public-schools',       'Pioneer Valley', 'Hampden',   'Holyoke',         'PK-12',  12,  5100, 'Public school district serving Holyoke, Massachusetts, in state receivership.', 1);

INSERT IGNORE INTO admin_users (id, username, email, display_name, password_hash, role, is_active) VALUES
(1, 'admin', 'admin@pdfwebsite.local', 'Site Administrator', '$2y$10$eKKCt1I4.NtxNJFGp73GCe.sgb5afmD0gnGn6w4Cg8JObarglryju', 'superadmin', 1);

INSERT IGNORE INTO system_config (config_key, config_value, config_type, description, is_public) VALUES
('site_name',              'PDF Website',           'string',  'Public-facing site name',                    1),
('site_tagline',           'Massachusetts Education Data & Oversight', 'string', 'Site tagline / subtitle', 1),
('site_url',               'https://pdfwebsite.local', 'string', 'Canonical site URL (no trailing slash)',    0),
('admin_email',            'admin@pdfwebsite.local', 'string',   'Contact email for site notifications',      0),
('records_per_page',       '25',                    'integer',  'Default pagination size for data tables',     0),
('default_timeline_years', '3',                     'integer',  'Default number of years shown on dashboards', 0),
('maintenance_mode',       '0',                     'boolean',  'Enable maintenance mode (1 = on)',            0),
('google_analytics_id',    '',                      'string',   'Google Analytics measurement ID',             0),
('meta_description',       'Massachusetts education oversight and data transparency platform.', 'string', 'Default meta description for SEO', 1);

SET FOREIGN_KEY_CHECKS = 1;

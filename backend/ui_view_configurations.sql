-- UI View Configurations and Field Management Tables
-- These tables need to be added to the existing schema

-- UI View Configurations table
CREATE TABLE IF NOT EXISTS ui_view_configurations (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  view_type VARCHAR(64) NOT NULL COMMENT 'queue, review, dashboard',
  name VARCHAR(128) NOT NULL,
  description TEXT NULL,
  columns_config JSON NOT NULL COMMENT 'Column visibility and ordering',
  filters_config JSON NULL COMMENT 'Saved filter configurations',
  sort_config JSON NULL COMMENT 'Saved sort configurations',
  is_default BOOLEAN NOT NULL DEFAULT FALSE,
  is_public BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ui_view_user_type_name (user_id, view_type, name),
  KEY idx_ui_view_user_id (user_id),
  KEY idx_ui_view_view_type (view_type),
  KEY idx_ui_view_is_default (is_default),
  KEY idx_ui_view_is_active (is_active),
  CONSTRAINT fk_ui_view_configurations_user FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- Field Definitions table
CREATE TABLE IF NOT EXISTS field_definitions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  field_name VARCHAR(128) NOT NULL,
  display_name VARCHAR(128) NOT NULL,
  field_type VARCHAR(64) NOT NULL COMMENT 'text, select, date, number, etc.',
  data_type VARCHAR(64) NOT NULL COMMENT 'varchar, int, date, json, etc.',
  description TEXT NULL,
  is_required BOOLEAN NOT NULL DEFAULT FALSE,
  validation_rules JSON NULL COMMENT 'Validation rules in JSON format',
  config_json JSON NULL COMMENT 'Field-specific configuration',
  default_value VARCHAR(255) NULL,
  group_id BIGINT UNSIGNED NULL,
  display_order INT NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL DEFAULT 'active' COMMENT 'active, inactive, deleted',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_field_definitions_field_name (field_name),
  KEY idx_field_definitions_group_id (group_id),
  KEY idx_field_definitions_status (status),
  KEY idx_field_definitions_display_order (display_order)
);

-- Field Groups table
CREATE TABLE IF NOT EXISTS field_groups (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(128) NOT NULL,
  description TEXT NULL,
  icon VARCHAR(64) NULL,
  display_order INT NOT NULL DEFAULT 0,
  is_collapsible BOOLEAN NOT NULL DEFAULT TRUE,
  collapsed_by_default BOOLEAN NOT NULL DEFAULT FALSE,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_field_groups_name (name),
  KEY idx_field_groups_display_order (display_order),
  KEY idx_field_groups_status (status)
);

-- Field Values table (for storing extracted field values)
CREATE TABLE IF NOT EXISTS field_values (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  queue_item_id BIGINT UNSIGNED NOT NULL,
  field_name VARCHAR(128) NOT NULL,
  field_value TEXT NOT NULL,
  confidence FLOAT NULL,
  source VARCHAR(64) NOT NULL DEFAULT 'parser' COMMENT 'parser, manual, ai, import',
  reviewed BOOLEAN NOT NULL DEFAULT FALSE,
  accepted BOOLEAN NULL,
  reviewed_by BIGINT UNSIGNED NULL,
  reviewed_at TIMESTAMP NULL,
  validation_errors JSON NULL,
  metadata JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_field_values_queue_field (queue_item_id, field_name),
  KEY idx_field_values_queue_item_id (queue_item_id),
  KEY idx_field_values_field_name (field_name),
  KEY idx_field_values_reviewed (reviewed),
  KEY idx_field_values_accepted (accepted),
  KEY idx_field_values_reviewed_by (reviewed_by),
  CONSTRAINT fk_field_values_queue_item FOREIGN KEY (queue_item_id) REFERENCES intake_queue_items(id) ON DELETE CASCADE,
  CONSTRAINT fk_field_values_reviewed_by FOREIGN KEY (reviewed_by) REFERENCES admin_users(id) ON DELETE SET NULL
);

-- Insert default field groups
INSERT INTO field_groups (name, description, icon, display_order, is_collapsible, collapsed_by_default) VALUES
('Case Information', 'Core case metadata and identifiers', 'folder', 10, TRUE, FALSE),
('Dates', 'Important dates and deadlines', 'calendar', 20, TRUE, FALSE),
('District Information', 'School district details', 'building', 30, TRUE, FALSE),
('Document Information', 'Document-specific metadata', 'file-earmark', 40, TRUE, FALSE),
('People', 'Extracted person entities', 'person', 50, TRUE, TRUE),
('Organizations', 'Extracted organization entities', 'people', 60, TRUE, TRUE),
('Custom Fields', 'User-defined custom fields', 'pencil', 100, TRUE, TRUE)
ON DUPLICATE KEY UPDATE description = VALUES(description), icon = VALUES(icon), display_order = VALUES(display_order);

-- Insert default field definitions (if not exists)
INSERT INTO field_definitions (field_name, display_name, field_type, data_type, description, is_required, validation_rules, config_json, default_value, group_id, display_order, status) VALUES
('case_code', 'Case Code', 'text', 'varchar', 'Unique identifier for the case', TRUE, '["required", "max:50"]', '{"placeholder": "e.g., PRS-2024-001"}', '', 1, 10, 'active'),
('case_title', 'Case Title', 'text', 'varchar', 'Descriptive title of the case', TRUE, '["required", "max:255"]', '{"placeholder": "Enter case title"}', '', 1, 20, 'active'),
('case_type', 'Case Type', 'select', 'varchar', 'Type of case', TRUE, '["required"]', '{"options": {"prr": "Public Records Request", "foia": "FOIA Request", "complaint": "Complaint", "appeal": "Appeal", "litigation": "Litigation"}}', 'prr', 1, 30, 'active'),
('status', 'Status', 'select', 'varchar', 'Current status of the case', TRUE, '["required"]', '{"options": {"pending": "Pending", "processing": "Processing", "review": "Under Review", "approved": "Approved", "rejected": "Rejected", "closed": "Closed"}}', 'pending', 1, 40, 'active'),
('filed_date', 'Filed Date', 'date', 'date', 'Date the case was filed', TRUE, '["required", "date"]', '{"format": "YYYY-MM-DD"}', '', 2, 10, 'active'),
('deadline_date', 'Deadline Date', 'date', 'date', 'Next deadline for the case', FALSE, '["date"]', '{"format": "YYYY-MM-DD"}', '', 2, 20, 'active'),
('district_name', 'District Name', 'text', 'varchar', 'Name of the school district', TRUE, '["required", "max:100"]', '{"placeholder": "Enter district name"}', '', 3, 10, 'active'),
('district_code', 'District Code', 'text', 'varchar', 'Unique code for the district', FALSE, '["max:20"]', '{"placeholder": "Enter district code"}', '', 3, 20, 'active'),
('document_type', 'Document Type', 'select', 'varchar', 'Type of document', TRUE, '["required"]', '{"options": {"request": "Request Letter", "response": "Response", "appeal": "Appeal", "decision": "Decision", "memo": "Memo", "report": "Report", "other": "Other"}}', 'request', 4, 10, 'active'),
('document_date', 'Document Date', 'date', 'date', 'Date of the document', FALSE, '["date"]', '{"format": "YYYY-MM-DD"}', '', 4, 20, 'active')
ON DUPLICATE KEY UPDATE 
  display_name = VALUES(display_name),
  field_type = VALUES(field_type),
  data_type = VALUES(data_type),
  description = VALUES(description),
  is_required = VALUES(is_required),
  validation_rules = VALUES(validation_rules),
  config_json = VALUES(config_json),
  default_value = VALUES(default_value),
  group_id = VALUES(group_id),
  display_order = VALUES(display_order),
  status = VALUES(status);

-- Add foreign key constraint for field_definitions.group_id
ALTER TABLE field_definitions 
ADD CONSTRAINT fk_field_definitions_group 
FOREIGN KEY (group_id) REFERENCES field_groups(id) ON DELETE SET NULL;

-- Filter Presets table
CREATE TABLE IF NOT EXISTS filter_presets (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  context VARCHAR(64) NOT NULL COMMENT 'queue, review, dashboard, cases',
  name VARCHAR(128) NOT NULL,
  description TEXT NULL,
  filters_config JSON NOT NULL COMMENT 'Filter configuration in JSON format',
  is_public BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_filter_presets_user_context_name (user_id, context, name),
  KEY idx_filter_presets_user_id (user_id),
  KEY idx_filter_presets_context (context),
  KEY idx_filter_presets_is_active (is_active),
  CONSTRAINT fk_filter_presets_user FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

-- Update FieldRegistry.php to use these tables (note: already implemented)
-- Update QueueUIManager.php to use ui_view_configurations table (note: already implemented)
-- Update FilterManager.php to use filter_presets table (note: already implemented)

-- System Configuration Table (for queue_config.json and other system settings)
CREATE TABLE IF NOT EXISTS system_config (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  config_key VARCHAR(128) NOT NULL,
  config_value JSON NOT NULL,
  category VARCHAR(64) NOT NULL DEFAULT 'general',
  description TEXT NULL,
  is_public BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_system_config_key (config_key),
  KEY idx_system_config_category (category),
  KEY idx_system_config_is_public (is_public)
);

-- District Sources Table (for district_sources.json)
CREATE TABLE IF NOT EXISTS district_sources (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  district_code VARCHAR(20) NOT NULL,
  district_name VARCHAR(100) NOT NULL,
  source_type VARCHAR(50) NOT NULL COMMENT 'website, api, manual, email',
  source_url VARCHAR(500) NULL,
  scraper_config JSON NULL,
  scrape_schedule VARCHAR(50) NOT NULL DEFAULT 'weekly',
  last_scraped_at TIMESTAMP NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active, inactive, paused',
  metadata JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_district_sources_code (district_code),
  KEY idx_district_sources_name (district_name),
  KEY idx_district_sources_status (status),
  KEY idx_district_sources_scrape_schedule (scrape_schedule)
);

-- Site Configuration Table (for site.json)
CREATE TABLE IF NOT EXISTS site_config (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  site_key VARCHAR(128) NOT NULL,
  site_value TEXT NOT NULL,
  data_type VARCHAR(20) NOT NULL DEFAULT 'string' COMMENT 'string, json, boolean, number, array',
  group_name VARCHAR(64) NOT NULL DEFAULT 'general',
  description TEXT NULL,
  is_editable BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_site_config_key (site_key),
  KEY idx_site_config_group (group_name),
  KEY idx_site_config_data_type (data_type)
);

-- Insert default system configuration from queue_config.json
INSERT INTO system_config (config_key, config_value, category, description, is_public) VALUES
('queue_config', '{
  "status_workflow": {
    "pending": ["processing", "review", "rejected"],
    "processing": ["review", "rejected", "archived"],
    "review": ["approved", "rejected", "pending"],
    "approved": ["archived"],
    "rejected": ["pending", "archived"],
    "archived": ["pending", "review"]
  },
  "priority_weights": {
    "low": 1,
    "normal": 2,
    "high": 3,
    "critical": 4
  },
  "auto_processing": {
    "enabled": true,
    "batch_size": 10,
    "max_processing_time_minutes": 30,
    "retry_attempts": 3
  },
  "assignment": {
    "auto_assign": true,
    "round_robin": true,
    "max_items_per_user": 5,
    "consider_workload": true
  },
  "notifications": {
    "on_assignment": true,
    "on_status_change": true,
    "on_deadline_approaching": true,
    "deadline_hours": 24
  },
  "file_handling": {
    "max_file_size_mb": 50,
    "allowed_mime_types": [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "text/plain",
      "text/csv",
      "application/json",
      "application/xml",
      "message/rfc822",
      "text/html"
    ],
    "allowed_extensions": [
      ".pdf",
      ".doc",
      ".docx",
      ".xls",
      ".xlsx",
      ".txt",
      ".csv",
      ".json",
      ".xml",
      ".eml",
      ".html",
      ".htm"
    ],
    "storage_paths": {
      "intake": "intake",
      "processing": "data/processing",
      "completed": "intake/completed",
      "archived": "data/archived"
    }
  },
  "review": {
    "require_review_before_approval": true,
    "min_review_time_seconds": 30,
    "max_concurrent_reviews_per_user": 3,
    "field_validation_required": true
  },
  "analytics": {
    "collect_metrics": true,
    "retention_days": 90,
    "daily_summary": true,
    "weekly_report": true
  }
}', 'queue', 'Queue system configuration', FALSE),
('system_info', '{"version": "2.0.0", "deployment_type": "production", "maintenance_mode": false}', 'system', 'System information and status', TRUE),
('email_settings', '{"enabled": true, "smtp_host": "localhost", "smtp_port": 587, "from_address": "noreply@parentdataforce.com", "from_name": "Parent Data Force"}', 'email', 'Email system configuration', FALSE)
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value), description = VALUES(description), updated_at = CURRENT_TIMESTAMP;

-- Insert default site configuration
INSERT INTO site_config (site_key, site_value, data_type, group_name, description) VALUES
('site_title', 'Parent Data Force', 'string', 'general', 'Main site title'),
('site_description', 'Transparency and accountability in education data', 'string', 'general', 'Site meta description'),
('site_keywords', 'education, data, transparency, public records, schools', 'string', 'general', 'Site meta keywords'),
('admin_email', 'admin@parentdataforce.com', 'string', 'contact', 'Administrator email address'),
('default_timezone', 'America/New_York', 'string', 'system', 'Default timezone for the system'),
('enable_registration', 'false', 'boolean', 'security', 'Allow new user registration'),
('maintenance_mode', 'false', 'boolean', 'system', 'Put site in maintenance mode'),
('logo_path', '/logo.png', 'string', 'appearance', 'Path to site logo'),
('footer_text', '© 2024 Parent Data Force. All rights reserved.', 'string', 'appearance', 'Footer text'),
('social_links', '{"twitter": "https://twitter.com/parentdataforce", "github": "https://github.com/parentdataforce"}', 'json', 'social', 'Social media links')
ON DUPLICATE KEY UPDATE site_value = VALUES(site_value), description = VALUES(description), updated_at = CURRENT_TIMESTAMP;

COMMIT;

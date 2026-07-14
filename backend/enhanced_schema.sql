-- Enhanced Schema for Admin Portal Queue Management and Review System
-- Must be imported after core schema (districts, cases, etc.) and admin_schema.sql

-- Queue Management Tables
CREATE TABLE intake_queue_items (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  filename VARCHAR(255) NOT NULL,
  filepath VARCHAR(500) NOT NULL,
  mime_type VARCHAR(128) NULL,
  size BIGINT UNSIGNED NOT NULL,
  status ENUM('pending', 'processing', 'review', 'approved', 'rejected', 'archived') NOT NULL DEFAULT 'pending',
  priority ENUM('low', 'normal', 'high', 'critical') NOT NULL DEFAULT 'normal',
  assigned_to BIGINT UNSIGNED NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  processed_at TIMESTAMP NULL,
  review_notes TEXT NULL,
  metadata JSON NULL,
  PRIMARY KEY (id),
  KEY idx_intake_queue_items_status (status),
  KEY idx_intake_queue_items_priority (priority),
  KEY idx_intake_queue_items_assigned_to (assigned_to),
  KEY idx_intake_queue_items_created_at (created_at),
  KEY idx_intake_queue_items_updated_at (updated_at),
  CONSTRAINT fk_intake_queue_items_assigned_to FOREIGN KEY (assigned_to) REFERENCES admin_users(id) ON DELETE SET NULL
);

CREATE TABLE queue_status_transitions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  queue_item_id BIGINT UNSIGNED NOT NULL,
  from_status VARCHAR(64) NOT NULL,
  to_status VARCHAR(64) NOT NULL,
  user_id BIGINT UNSIGNED NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  notes TEXT NULL,
  metadata JSON NULL,
  PRIMARY KEY (id),
  KEY idx_queue_status_transitions_queue_item_id (queue_item_id),
  KEY idx_queue_status_transitions_timestamp (timestamp),
  KEY idx_queue_status_transitions_user_id (user_id),
  CONSTRAINT fk_queue_status_transitions_queue_item FOREIGN KEY (queue_item_id) REFERENCES intake_queue_items(id) ON DELETE CASCADE,
  CONSTRAINT fk_queue_status_transitions_user FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE SET NULL
);

-- Field Extraction and Review Tables
CREATE TABLE field_extractions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  queue_item_id BIGINT UNSIGNED NOT NULL,
  field_name VARCHAR(128) NOT NULL,
  field_type ENUM('text', 'date', 'number', 'person', 'organization', 'case_reference', 'document_type') NOT NULL,
  extracted_value TEXT NOT NULL,
  confidence FLOAT NULL,
  source ENUM('parser', 'manual', 'ai') NOT NULL DEFAULT 'parser',
  reviewed BOOLEAN NOT NULL DEFAULT FALSE,
  accepted BOOLEAN NULL,
  reviewed_by BIGINT UNSIGNED NULL,
  reviewed_at TIMESTAMP NULL,
  notes TEXT NULL,
  validation_errors JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_field_extractions_queue_item_id (queue_item_id),
  KEY idx_field_extractions_field_name (field_name),
  KEY idx_field_extractions_reviewed (reviewed),
  KEY idx_field_extractions_accepted (accepted),
  KEY idx_field_extractions_reviewed_by (reviewed_by),
  CONSTRAINT fk_field_extractions_queue_item FOREIGN KEY (queue_item_id) REFERENCES intake_queue_items(id) ON DELETE CASCADE,
  CONSTRAINT fk_field_extractions_reviewed_by FOREIGN KEY (reviewed_by) REFERENCES admin_users(id) ON DELETE SET NULL
);

CREATE TABLE review_sessions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  queue_item_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP NULL,
  actions JSON NULL,
  notes TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_review_sessions_queue_item_id (queue_item_id),
  KEY idx_review_sessions_user_id (user_id),
  KEY idx_review_sessions_started_at (started_at),
  CONSTRAINT fk_review_sessions_queue_item FOREIGN KEY (queue_item_id) REFERENCES intake_queue_items(id) ON DELETE CASCADE,
  CONSTRAINT fk_review_sessions_user FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

CREATE TABLE validation_rules (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(128) NOT NULL,
  description TEXT NULL,
  field_type VARCHAR(64) NOT NULL,
  rule_type ENUM('required', 'format', 'range', 'regex', 'lookup') NOT NULL,
  rule_config JSON NOT NULL,
  error_message VARCHAR(255) NOT NULL,
  severity ENUM('error', 'warning', 'info') NOT NULL DEFAULT 'error',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_validation_rules_name (name),
  KEY idx_validation_rules_field_type (field_type),
  KEY idx_validation_rules_active (active)
);

-- Entity Management Tables
CREATE TABLE extracted_persons (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(128) NULL,
  organization VARCHAR(255) NULL,
  contact_info JSON NULL,
  extracted_from JSON NOT NULL,
  confidence FLOAT NULL,
  verified BOOLEAN NOT NULL DEFAULT FALSE,
  merge_candidate_ids JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_extracted_persons_name (name),
  KEY idx_extracted_persons_verified (verified),
  KEY idx_extracted_persons_organization (organization(100))
);

CREATE TABLE extracted_organizations (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  type ENUM('district', 'school', 'agency', 'company', 'other') NOT NULL DEFAULT 'other',
  extracted_from JSON NOT NULL,
  confidence FLOAT NULL,
  verified BOOLEAN NOT NULL DEFAULT FALSE,
  district_code VARCHAR(32) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_extracted_organizations_name (name),
  KEY idx_extracted_organizations_type (type),
  KEY idx_extracted_organizations_verified (verified),
  KEY idx_extracted_organizations_district_code (district_code)
);

CREATE TABLE entity_links (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  source_type ENUM('case', 'document', 'person', 'organization') NOT NULL,
  source_id VARCHAR(128) NOT NULL,
  target_type ENUM('case', 'document', 'person', 'organization') NOT NULL,
  target_id VARCHAR(128) NOT NULL,
  relationship_type ENUM('related_to', 'mentions', 'references', 'attached_to', 'authored_by', 'sent_to', 'received_from') NOT NULL,
  confidence FLOAT NULL,
  verified BOOLEAN NOT NULL DEFAULT FALSE,
  verified_by BIGINT UNSIGNED NULL,
  verified_at TIMESTAMP NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_entity_links_source (source_type, source_id),
  KEY idx_entity_links_target (target_type, target_id),
  KEY idx_entity_links_relationship_type (relationship_type),
  KEY idx_entity_links_verified (verified),
  KEY idx_entity_links_verified_by (verified_by),
  CONSTRAINT fk_entity_links_verified_by FOREIGN KEY (verified_by) REFERENCES admin_users(id) ON DELETE SET NULL
);

-- Bulk Operations Tables
CREATE TABLE bulk_operations (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  operation_type ENUM('status_change', 'tagging', 'assignment', 'export', 'delete') NOT NULL,
  parameters JSON NOT NULL,
  items_count INT NOT NULL,
  items_processed INT NOT NULL DEFAULT 0,
  status ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending',
  created_by BIGINT UNSIGNED NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at TIMESTAMP NULL,
  completed_at TIMESTAMP NULL,
  error_message TEXT NULL,
  result_summary JSON NULL,
  PRIMARY KEY (id),
  KEY idx_bulk_operations_status (status),
  KEY idx_bulk_operations_created_by (created_by),
  KEY idx_bulk_operations_created_at (created_at),
  CONSTRAINT fk_bulk_operations_created_by FOREIGN KEY (created_by) REFERENCES admin_users(id) ON DELETE CASCADE
);

CREATE TABLE bulk_operation_items (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  bulk_operation_id BIGINT UNSIGNED NOT NULL,
  item_id VARCHAR(128) NOT NULL,
  item_type ENUM('queue_item', 'case', 'document') NOT NULL,
  status ENUM('pending', 'processing', 'success', 'failed') NOT NULL DEFAULT 'pending',
  error_message TEXT NULL,
  processed_at TIMESTAMP NULL,
  result_data JSON NULL,
  PRIMARY KEY (id),
  KEY idx_bulk_operation_items_bulk_operation_id (bulk_operation_id),
  KEY idx_bulk_operation_items_item (item_type, item_id),
  KEY idx_bulk_operation_items_status (status),
  CONSTRAINT fk_bulk_operation_items_bulk_operation FOREIGN KEY (bulk_operation_id) REFERENCES bulk_operations(id) ON DELETE CASCADE
);

-- Analytics and Quality Metrics Tables
CREATE TABLE quality_metrics (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  metric_name VARCHAR(128) NOT NULL,
  metric_value FLOAT NOT NULL,
  calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  time_range VARCHAR(64) NOT NULL,
  breakdown JSON NULL,
  PRIMARY KEY (id),
  KEY idx_quality_metrics_metric_name (metric_name),
  KEY idx_quality_metrics_calculated_at (calculated_at),
  KEY idx_quality_metrics_time_range (time_range)
);

CREATE TABLE user_performance (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  period VARCHAR(64) NOT NULL,
  items_reviewed INT NOT NULL DEFAULT 0,
  avg_review_time FLOAT NULL,
  accuracy_rate FLOAT NULL,
  completion_rate FLOAT NULL,
  calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_user_performance_user_period (user_id, period),
  KEY idx_user_performance_user_id (user_id),
  KEY idx_user_performance_period (period),
  CONSTRAINT fk_user_performance_user FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

CREATE TABLE system_health (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  queue_size INT NOT NULL DEFAULT 0,
  pending_count INT NOT NULL DEFAULT 0,
  processing_count INT NOT NULL DEFAULT 0,
  avg_processing_time FLOAT NULL,
  error_rate FLOAT NULL,
  active_users INT NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_system_health_timestamp (timestamp)
);

-- Indexes for performance optimization
CREATE INDEX idx_intake_queue_items_composite ON intake_queue_items (status, priority, created_at);
CREATE INDEX idx_field_extractions_composite ON field_extractions (queue_item_id, reviewed, accepted);
CREATE INDEX idx_entity_links_composite ON entity_links (source_type, source_id, target_type, target_id);
CREATE INDEX idx_bulk_operations_composite ON bulk_operations (status, created_at, created_by);

-- Insert default validation rules
INSERT INTO validation_rules (name, description, field_type, rule_type, rule_config, error_message, severity, active) VALUES
('date_format', 'Validate date fields are in YYYY-MM-DD format', 'date', 'regex', '{"pattern": "^\\\\d{4}-\\\\d{2}-\\\\d{2}$"}', 'Date must be in YYYY-MM-DD format', 'error', TRUE),
('required_case_code', 'Case code is required for case_reference fields', 'case_reference', 'required', '{"required": true}', 'Case code is required', 'error', TRUE),
('person_name_length', 'Person names must be between 2 and 100 characters', 'person', 'range', '{"min": 2, "max": 100}', 'Person name must be between 2 and 100 characters', 'warning', TRUE),
('organization_type', 'Organization type must be valid', 'organization', 'lookup', '{"values": ["district", "school", "agency", "company", "other"]}', 'Invalid organization type', 'error', TRUE),
('confidence_threshold', 'Extraction confidence must be above 0.5', 'text', 'range', '{"min": 0.5, "max": 1.0}', 'Extraction confidence too low', 'warning', TRUE);

-- Create view for queue statistics
CREATE VIEW queue_statistics AS
SELECT 
  status,
  COUNT(*) as count,
  AVG(TIMESTAMPDIFF(SECOND, created_at, COALESCE(processed_at, NOW()))) as avg_processing_seconds,
  MIN(created_at) as oldest_item,
  MAX(created_at) as newest_item
FROM intake_queue_items
GROUP BY status;

-- Create view for user performance summary
CREATE VIEW user_performance_summary AS
SELECT 
  u.id as user_id,
  u.username,
  u.full_name,
  u.role,
  COUNT(DISTINCT r.queue_item_id) as total_reviewed,
  AVG(TIMESTAMPDIFF(SECOND, r.started_at, COALESCE(r.ended_at, NOW()))) as avg_review_time_seconds,
  COUNT(DISTINCT CASE WHEN f.accepted = TRUE THEN f.id END) as accepted_fields,
  COUNT(DISTINCT CASE WHEN f.accepted = FALSE THEN f.id END) as rejected_fields
FROM admin_users u
LEFT JOIN review_sessions r ON u.id = r.user_id
LEFT JOIN field_extractions f ON u.id = f.reviewed_by
GROUP BY u.id, u.username, u.full_name, u.role;
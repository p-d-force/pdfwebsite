-- Admin and security tables for Parent Data Force
-- Must be imported after core schema (districts, cases, etc.)

CREATE TABLE admin_users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL,
  email VARCHAR(255) NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255) NULL,
  role ENUM('owner', 'reviewer', 'contributor', 'readonly') NOT NULL DEFAULT 'reviewer',
  status ENUM('active', 'suspended', 'pending') NOT NULL DEFAULT 'active',
  last_login_at TIMESTAMP NULL,
  failed_login_attempts INT NOT NULL DEFAULT 0,
  password_changed_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_admin_users_username (username),
  UNIQUE KEY uq_admin_users_email (email)
);

CREATE TABLE admin_sessions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  session_id VARCHAR(128) NOT NULL,
  ip_address VARCHAR(45) NULL,
  user_agent TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL,
  invalidated_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_admin_sessions_session_id (session_id),
  KEY idx_admin_sessions_user_id (user_id),
  KEY idx_admin_sessions_expires_at (expires_at),
  CONSTRAINT fk_admin_sessions_user FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE CASCADE
);

CREATE TABLE admin_audit_log (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NULL,
  action_type VARCHAR(64) NOT NULL,
  entity_type VARCHAR(64) NULL,
  entity_id VARCHAR(128) NULL,
  details JSON NULL,
  ip_address VARCHAR(45) NULL,
  user_agent TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_admin_audit_log_user_id (user_id),
  KEY idx_admin_audit_log_action_type (action_type),
  KEY idx_admin_audit_log_created_at (created_at),
  CONSTRAINT fk_admin_audit_log_user FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE SET NULL
);

CREATE TABLE csrf_tokens (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id VARCHAR(128) NOT NULL,
  token VARCHAR(128) NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  used_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_csrf_tokens_token (token),
  KEY idx_csrf_tokens_session_id (session_id),
  KEY idx_csrf_tokens_expires_at (expires_at)
);

-- Default admin user (username: admin, password: admin)
-- Password will be updated on first login
INSERT INTO admin_users (username, email, password_hash, full_name, role, status) VALUES
('admin', 'admin@example.com', '$2y$10$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'System Administrator', 'owner', 'active')
ON DUPLICATE KEY UPDATE email = VALUES(email), full_name = VALUES(full_name);
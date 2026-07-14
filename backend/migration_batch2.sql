-- Batch 2 migration: system_config table for safe site settings
CREATE TABLE IF NOT EXISTS system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO system_config (config_key, config_value) VALUES
('site_email', 'admin@parentdataforce.com'),
('site_name', 'Parent Data Force'),
('site_tagline', 'MAKING DATA MAKE SENSE');

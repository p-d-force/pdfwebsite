# Production Deployment Checklist - Parent Data Force Admin

## Environment Requirements
- **cPanel Hosting**: PHP 8.3+, MariaDB 10.11+
- **Database**: MySQL/MariaDB with UTF8mb4 encoding
- **Web Server**: Apache with mod_rewrite, mod_headers
- **PHP Extensions**: PDO, pdo_mysql, session, json

## Automated Deployment (Windows)

For automated deployment using PowerShell:

```powershell
# Run a dry run to see what would happen
.\deploy.ps1 -DryRun

# Actual deployment (will prompt for FTP password)
.\deploy.ps1

# With custom server and username
.\deploy.ps1 -Server "yourdomain.com" -Username "ftpuser" -RemotePath "/var/www/html"

# Skip JSON migration if not needed
.\deploy.ps1 -MigrateJsonToDb:$false
```

### Deployment Script Features:
1. **FTP Connection Test**: Verifies credentials and server access
2. **Remote Backup**: Creates local backup of deployment files
3. **File Synchronization**: Uses WinSCP for reliable FTP sync
4. **Database Schema Deployment**: Guides through manual database setup
5. **Environment Configuration**: Helps configure .env file
6. **JSON-to-DB Migration**: Runs configuration migration from JSON files to database
7. **Deployment Testing**: Verifies site accessibility and security

### Requirements for Automated Deployment:
- Windows PowerShell 5.1+
- WinSCP installed (optional, for better FTP sync)
- FTP credentials for production server
- cPanel/phpMyAdmin access for database setup

## JSON-to-Database Migration System

The project now includes a configuration migration system that moves configuration from JSON files to database tables for better performance and centralized management.

### Migration Components:

1. **Database Schema Extensions** (`backend/ui_view_configurations.sql`):
   - `system_config`: Centralized configuration storage
   - `district_sources`: District sources configuration
   - `site_config`: Site settings
   - `field_definitions`, `field_groups`, `field_values`: Field management
   - `ui_view_configurations`: UI customization
   - `filter_presets`: Saved filters

2. **ConfigManager Class** (`admin/includes/ConfigManager.php`):
   - Singleton pattern for centralized configuration access
   - Automatic fallback to JSON files if database not available
   - Caching for performance
   - Migration methods for JSON-to-DB transfer

3. **Migration Script** (`backend/migrate_json_to_db.php`):
   ```bash
   # Dry run (simulate migration)
   php backend/migrate_json_to_db.php --dry-run
   
   # Actual migration
   php backend/migrate_json_to_db.php
   
   # Rollback last migration
   php backend/migrate_json_to_db.php --rollback
   ```

4. **Updated QueueManager** (`admin/includes/QueueManager.php`):
   - Uses ConfigManager instead of direct JSON file access
   - Maintains backward compatibility with JSON fallback

### Migration Process:

1. **Initial Deployment**: After database setup, run the migration script
2. **Configuration Access**: All components use ConfigManager for configuration
3. **Fallback System**: If database config missing, falls back to JSON files
4. **Auto-Migration**: ConfigManager automatically migrates JSON to DB on first access

### Benefits:
- **Centralized Management**: All configuration in one place
- **Better Performance**: Database queries faster than file reads
- **Audit Trail**: Track configuration changes in database
- **Live Updates**: Change config without file system access
- **Backward Compatible**: Existing JSON files remain as fallback

## Deployment Steps

### 1. Database Setup
```sql
-- Run on production server:
-- 1. Create database and user
CREATE DATABASE pdf_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'pdf_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON pdf_db.* TO 'pdf_user'@'localhost';
FLUSH PRIVILEGES;

-- 2. Import schema
-- Run backend/schema.sql
-- Run backend/admin_schema.sql

-- 3. Create admin user
INSERT INTO admin_users (username, email, password_hash, role, status) 
VALUES ('admin', 'admin@parentdataforce.com', '$2b$10$eKKCt1I4.NtxNJFGp73GCe.sgb5afmD0gnGn6w4Cg8JObarglryju', 'owner', 'active');
-- Default password: tcx%kWa^SEZL7x6# (CHANGE IMMEDIATELY)
```

### 2. File Upload
1. Upload all files to public_html/ (or subdirectory)
2. Ensure directory structure:
   ```
   public_html/
   ├── admin/
   │   ├── includes/
   │   ├── api/
   │   └── *.php
   ├── backend/ (optional, for scripts)
   └── .env (create from .env.example)
   ```

3. Set correct permissions:
   ```bash
   chmod 755 admin/ admin/includes/ admin/api/
   chmod 644 admin/*.php admin/includes/*.php admin/api/*.php
   chmod 600 .env
   chmod 755 scripts/*.sh scripts/*.bat
   ```

### 3. Configuration
1. Copy `.env.example` to `.env` and configure:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=pdf_db
   DB_USER=pdf_user
   DB_PASSWORD=your_strong_password_here
   APP_SECRET=generate_random_string_here
   APP_ENV=production
   APP_DEBUG=false
   ```

2. Generate strong APP_SECRET:
   ```bash
   openssl rand -hex 32
   ```

3. Update `admin/includes/config.php` if paths differ:
   - Check `ROOT_PATH` definition
   - Verify `.env` file location

### 4. Security Hardening
1. **.htaccess** (already in admin/):
   - Security headers enabled
   - Directory listing disabled
   - Includes directory protected

2. **PHP Configuration** (php.ini or .user.ini):
   ```ini
   display_errors = Off
   log_errors = On
   error_log = /home/user/logs/php_errors.log
   session.cookie_httponly = 1
   session.cookie_secure = 1  # Enable if HTTPS
   session.cookie_samesite = Strict
   upload_max_filesize = 256M
   post_max_size = 256M
   ```

3. **Directory Protection**:
   - Ensure `admin/includes/.htaccess` exists with `Require all denied`
   - Protect `backend/` directory if contains sensitive scripts

### 5. Cron Jobs (Optional)
For automated exports or sync:
```bash
# Daily export to JSON for public website
0 2 * * * cd /home/user/public_html && php backend/export_to_json.php --output-dir=../public_export --format=legacy
```

### 6. Testing
1. **Admin Interface**: `https://yourdomain.com/admin/login.php`
   - Test login with admin credentials
   - Change default password immediately
   - Verify dashboard loads
   - Test profile page and password change

2. **API Endpoints** (require authentication):
   - `GET /admin/api/cases.php`
   - `GET /admin/api/documents.php`
   - `GET /admin/api/events.php`
   - `GET /admin/api/districts.php`

3. **Security**:
   - Verify HTTPS redirect (if using SSL)
   - Check security headers present
   - Test CSRF protection on forms

### 7. Backup Strategy
1. **Database backups**:
   ```bash
   mysqldump -u pdf_user -p pdf_db > backup_$(date +%Y%m%d).sql
   ```

2. **File backups**:
   - Backup `.env` file (contains credentials)
   - Backup uploaded documents
   - Backup generated JSON exports

### 8. Monitoring
1. **Error logs**: Check PHP error logs regularly
2. **Access logs**: Monitor for suspicious activity
3. **Database**: Monitor size and performance

### 9. Migration from Development
If migrating from local development:
1. Export development database:
   ```bash
   mysqldump -u pdf_user -p pdf_db > migration.sql
   ```

2. Import to production:
   ```bash
   mysql -u pdf_user -p pdf_db < migration.sql
   ```

3. Update file paths in database if different:
   ```sql
   UPDATE documents SET relative_path = REPLACE(relative_path, 'C:/old/path/', 'new/path/');
   ```

### Troubleshooting
- **500 Internal Server Error**: Check PHP error log, .htaccess configuration
- **Database Connection Failed**: Verify credentials in .env, check user permissions
- **Login Fails**: Check password hash algorithm (bcrypt), verify user exists
- **CSRF Token Invalid**: Check session configuration, ensure cookies work

### Post-Deployment
1. Change default admin password
2. Set up regular backups
3. Monitor for security updates (PHP, MariaDB)
4. Consider implementing rate limiting
5. Enable firewall rules if available

## Emergency Rollback
1. Restore database from backup
2. Revert file changes
3. Update .env if needed
4. Clear PHP sessions if issues
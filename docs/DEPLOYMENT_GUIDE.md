# Parent Data Force Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Parent Data Force website with Phase 2 admin portal features, database setup, and automated deployment tooling. The system includes:

1. **Website Files**: Static HTML, CSS, JavaScript, and PHP files
2. **Admin Portal**: Phase 2 features (queue management, field review, entity relationship management)
3. **Database**: MySQL database with enhanced schema for Phase 2
4. **Automated Tools**: PowerShell scripts for easy, repeatable deployments

## Prerequisites

### Software Requirements
- **FileZilla** or any FTP client (for manual uploads)
- **PowerShell 5.1+** (for automated scripts)
- **MySQL Command Line Client** (optional, for database scripts)
- **cPanel/phpMyAdmin access** (for database management)

### Credentials Required
- FTP credentials for `ftp.parentdataforce.com`
- Database credentials from `.env.production`
- cPanel login credentials

### Current Status Check
Run the verification script first to check current state:
```powershell
.\verify_deployment.ps1 -Detailed
```

## Quick Start Deployment

For a complete deployment from scratch:

### Step 1: Manual Admin Directory Upload (If Missing)
The admin directory is currently missing from the server, causing 404 errors.

**Manual Upload via FileZilla:**
1. Open FileZilla
2. Connect to: `ftp.parentdataforce.com`
3. Username: `webmaster@parentdataforce.com`
4. Password: `jJUBFSZK1!`
5. Navigate to: `/public_html/`
6. Upload the entire `admin/` folder from `C:\Users\LokiF\Desktop\PDFWEBSITE\`
7. Verify: `https://parentdataforce.com/admin/login.php` should show login page (not 404)

### Step 2: Database Setup

**Option A: Automated Script (Recommended)**
```powershell
.\deploy_database.ps1 -DryRun       # Test first
.\deploy_database.ps1               # Full deployment
```

**Option B: Manual via phpMyAdmin**
1. Login to cPanel > phpMyAdmin
2. Select database: `g5wwzsi5v4lbdt1q_pdf_db`
3. Import SQL files in this order:
   - `backend/schema.sql` (core tables)
   - `backend/admin_schema.sql` (admin users)
   - `backend/enhanced_schema.sql` (Phase 2 features)
   - `backend/ui_view_configurations.sql` (views)

**Option C: Command Line**
```bash
mysql -h localhost -u g5wwzsi5v4lbdt1q_pdf_user -p g5wwzsi5v4lbdt1q_pdf_db < backend/schema.sql
mysql -h localhost -u g5wwzsi5v4lbdt1q_pdf_user -p g5wwzsi5v4lbdt1q_pdf_db < backend/admin_schema.sql
mysql -h localhost -u g5wwzsi5v4lbdt1q_pdf_user -p g5wwzsi5v4lbdt1q_pdf_db < backend/enhanced_schema.sql
```

### Step 3: Environment Configuration

1. Upload `.env.production` to server at `/public_html/.env`
2. Set correct permissions:
   ```bash
   chmod 600 .env
   chmod 755 public_html
   find public_html -type f -exec chmod 644 {} \;
   find public_html -type d -exec chmod 755 {} \;
   ```
3. Verify database connection works with new credentials

### Step 4: Create Admin User

**Default Credentials:**
- Username: `admin`
- Password: `tcx%kWa^SEZL7x6#`

**Create via SQL:**
```sql
INSERT INTO admin_users (username, password_hash, full_name, role, created_at)
VALUES ('admin', SHA2('tcx%kWa^SEZL7x6#', 256), 'Administrator', 'admin', NOW());
```

### Step 5: Full Verification
```powershell
.\verify_deployment.ps1 -Detailed
```

## Automated Deployment Scripts

### 1. FTP Sync Script (`ftp_sync.ps1`)
Intelligent file synchronization with error recovery.

**Features:**
- Recursive directory sync
- File size comparison (skips unchanged files)
- Retry logic for failed uploads
- Progress indicators for large files
- Dry run mode for testing

**Usage:**
```powershell
# Test sync without uploading
.\ftp_sync.ps1 -DryRun

# Sync all files
.\ftp_sync.ps1

# Force re-upload all files
.\ftp_sync.ps1 -ForceUpload

# Skip admin directory (for testing)
.\ftp_sync.ps1 -SkipAdmin

# Include admin directory
.\ftp_sync.ps1 -SkipAdmin:$false
```

### 2. Database Deployment Script (`deploy_database.ps1`)
Automated database schema import and migration.

**Features:**
- Tests MySQL connection before proceeding
- Imports schemas in correct order
- Optional skipping of sections
- Data migration guidance
- Admin user creation prompts

**Usage:**
```powershell
# Test connection only
.\deploy_database.ps1 -DryRun

# Full deployment
.\deploy_database.ps1

# Skip Phase 2 features
.\deploy_database.ps1 -SkipEnhanced

# Skip data migrations
.\deploy_database.ps1 -RunMigrations:$false
```

### 3. Deployment Verification Script (`verify_deployment.ps1`)
Comprehensive testing of all system components.

**Test Categories:**
1. Website accessibility (HTTP status codes)
2. Admin portal functionality
3. Database connectivity and tables
4. Phase 2 feature validation
5. Security configuration (.env protection, headers)
6. Performance metrics

**Usage:**
```powershell
# Full verification
.\verify_deployment.ps1

# Detailed output
.\verify_deployment.ps1 -Detailed

# Skip database checks
.\verify_deployment.ps1 -SkipDatabase

# Skip Phase 2 checks
.\verify_deployment.ps1 -SkipPhase2
```

## Phase 2 Features Verification

After deployment, verify Phase 2 features are working:

### 1. Queue Management System
- Access: `https://parentdataforce.com/admin/queue.php`
- Features:
  - View intake queue items
  - Change item status (pending, processing, review, approved, rejected)
  - Assign items to users
  - Priority management (low, normal, high, critical)

### 2. Field Review System
- Access: `https://parentdataforce.com/admin/ingest.php`
- Features:
  - Document upload and processing
  - Field extraction review
  - Validation rule enforcement
  - Entity extraction (persons, organizations)

### 3. Entity Relationship Management
- Database tables: `extracted_persons`, `extracted_organizations`, `entity_links`
- Features:
  - Person entity extraction from documents
  - Organization identification
  - Relationship mapping between entities

### 4. Bulk Operations
- Database table: `bulk_operations`
- Features:
  - Batch status changes
  - Mass tagging
  - Export operations
  - Progress tracking

## Common Deployment Scenarios

### Scenario 1: Initial Production Deployment
```powershell
# 1. Upload all files
.\ftp_sync.ps1

# 2. Setup database
.\deploy_database.ps1

# 3. Verify deployment
.\verify_deployment.ps1 -Detailed

# 4. Test admin login
# Go to: https://parentdataforce.com/admin/login.php
# Use: admin / tcx%kWa^SEZL7x6#
```

### Scenario 2: Incremental File Updates
```powershell
# 1. Test what will be uploaded
.\ftp_sync.ps1 -DryRun

# 2. Upload changed files only
.\ftp_sync.ps1

# 3. Verify updates
.\verify_deployment.ps1 -SkipDatabase
```

### Scenario 3: Database Schema Update
```powershell
# 1. Backup database first (via phpMyAdmin)

# 2. Deploy new schema
.\deploy_database.ps1 -SkipCore -SkipAdmin
# (Only deploys enhanced schema changes)

# 3. Verify database
.\verify_deployment.ps1 -SkipWebsite -SkipAdmin
```

### Scenario 4: Emergency Fix (Admin Portal Down)
```powershell
# 1. Verify current state
.\verify_deployment.ps1 -SkipDatabase -SkipPhase2

# 2. Force re-upload admin directory
.\ftp_sync.ps1 -ForceUpload -SkipAdmin:$false

# 3. Quick verification
curl -I https://parentdataforce.com/admin/login.php
```

## Troubleshooting Guide

### Issue 1: Admin Login Page Returns 404
**Symptoms:**
- `https://parentdataforce.com/admin/login.php` shows 404 Not Found
- Admin directory missing from FTP server

**Solution:**
```powershell
# Check if admin directory exists on server
.\verify_admin_upload.ps1

# Upload admin directory via FileZilla or:
.\ftp_sync.ps1 -SkipAdmin:$false -ForceUpload
```

### Issue 2: Database Connection Errors
**Symptoms:**
- Admin pages show database connection errors
- Database deployment script fails

**Solution:**
1. Verify credentials in `.env.production` match cPanel database credentials
2. Check database user has proper permissions
3. Test connection manually:
   ```powershell
   .\deploy_database.ps1 -DryRun
   ```
4. Use phpMyAdmin for manual import if automated script fails

### Issue 3: Phase 2 Features Not Working
**Symptoms:**
- Queue management page shows errors
- Missing database tables for Phase 2 features

**Solution:**
1. Verify enhanced schema was imported:
   ```powershell
   .\verify_deployment.ps1 -SkipWebsite -SkipAdmin -SkipDatabase:$false
   ```
2. Check for `intake_queue_items`, `field_extractions` tables
3. Re-import enhanced schema if missing:
   ```powershell
   .\deploy_database.ps1 -SkipCore -SkipAdmin
   ```

### Issue 4: File Permission Problems
**Symptoms:**
- CSS/JS files not loading
- PHP errors about file permissions
- Uploads failing

**Solution:**
**On cPanel/SSH:**
```bash
# Set correct permissions
find /home/g5wwzsi5v4lbdt1q/public_html -type f -exec chmod 644 {} \;
find /home/g5wwzsi5v4lbdt1q/public_html -type d -exec chmod 755 {} \;

# Special permissions for upload directories
chmod 775 /home/g5wwzsi5v4lbdt1q/public_html/data
chmod 775 /home/g5wwzsi5v4lbdt1q/public_html/intake
```

### Issue 5: .env File Security Warning
**Symptoms:**
- Verification script reports `.env` file is accessible
- Security risk exposure

**Solution:**
1. Move `.env` outside web root if possible
2. Add `.htaccess` protection:
   ```apache
   <Files ".env">
     Order Allow,Deny
     Deny from all
   </Files>
   ```
3. Set permissions:
   ```bash
   chmod 600 .env
   ```

## Security Best Practices

### 1. File Permissions
- **Files**: 644 (rw-r--r--)
- **Directories**: 755 (rwxr-xr-x)
- **Configuration files (.env)**: 600 (rw-------)
- **Upload directories**: 775 (rwxrwxr-x)

### 2. Database Security
- Use strong, unique passwords
- Limit database user permissions to necessary operations
- Regularly backup database
- Keep MySQL updated

### 3. Web Security
- Keep `.env` file outside web root or properly protected
- Use HTTPS (already configured)
- Implement security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Regular security audits

### 4. Admin Portal Security
- Change default admin password immediately
- Use strong passwords for all admin users
- Regular user access reviews
- Log admin activities

## Maintenance Procedures

### Regular Backups
**Files:**
- Use cPanel backup feature
- Or manually download via FTP

**Database:**
```bash
# Command line backup
mysqldump -h localhost -u g5wwzsi5v4lbdt1q_pdf_user -p g5wwzsi5v4lbdt1q_pdf_db > backup_$(date +%Y%m%d).sql

# cPanel backup
- Use cPanel > Backup > Download a MySQL Database Backup
```

### Update Deployment
1. **Test locally** first
2. **Backup production** database and files
3. **Deploy updates** using appropriate script
4. **Verify** deployment with verification script
5. **Monitor** for issues

### Monitoring
**Regular checks:**
```powershell
# Weekly verification
.\verify_deployment.ps1

# Check for errors in:
# - cPanel error logs
# - Website access logs
# - Database slow query logs
```

## Appendix

### Script Reference

| Script | Purpose | Key Parameters |
|--------|---------|----------------|
| `ftp_sync.ps1` | File synchronization | `-DryRun`, `-ForceUpload`, `-SkipAdmin` |
| `deploy_database.ps1` | Database deployment | `-DryRun`, `-SkipCore`, `-SkipEnhanced` |
| `verify_deployment.ps1` | System verification | `-Detailed`, `-SkipWebsite`, `-SkipDatabase` |
| `verify_admin_upload.ps1` | Admin directory check | (none) |

### Database Schema Overview

**Core Tables:**
- `districts`, `cases`, `documents` - Main data
- `admin_users` - Admin authentication

**Phase 2 Tables:**
- `intake_queue_items` - Document processing queue
- `field_extractions` - Extracted field data
- `validation_rules` - Field validation rules
- `extracted_persons`, `extracted_organizations` - Entity extraction
- `entity_links` - Entity relationships
- `bulk_operations` - Batch operations

**Views:**
- `queue_statistics` - Queue performance metrics
- `user_performance_summary` - Admin user metrics

### File Structure
```
public_html/
├── admin/                    # Admin portal (Phase 2)
│   ├── login.php
│   ├── queue.php            # Queue management
│   ├── ingest.php           # Document ingest
│   └── includes/            # PHP classes
├── public/                  # Public website
├── backend/                 # Database scripts
│   ├── schema.sql          # Core schema
│   ├── admin_schema.sql    # Admin tables
│   └── enhanced_schema.sql # Phase 2 schema
├── config/                  # Configuration
└── data/                   # Application data
```

### Contact & Support

**For deployment issues:**
1. Check this guide first
2. Run verification scripts for diagnostics
3. Review cPanel error logs
4. Check database connectivity

**Emergency contacts:**
- Server hosting: cPanel support
- Database issues: phpMyAdmin access
- Code issues: Development team

---

*Last Updated: March 2026*  
*Version: 2.0 (Phase 2 Deployment)*
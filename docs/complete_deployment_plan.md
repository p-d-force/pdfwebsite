# Implementation Plan: Complete Website & Database Deployment

[Overview]
Comprehensive deployment of the Parent Data Force website including admin portal Phase 2 features, database setup, and automated deployment tooling for future FTP uploads.

This implementation addresses three critical needs: 1) Fix the missing admin directory causing 404 errors, 2) Set up the complete database schema with Phase 2 queue management and field review systems, and 3) Create automated tooling for easy, repeatable FTP deployments. The plan builds on existing infrastructure while adding robust automation and verification tools.

[Types]  
Enhanced database schema with queue management, field review, entity relationship, and analytics types.

Detailed type specifications:

**Queue Management Types:**
- `intake_queue_items`: Represents documents in processing pipeline with status ENUM('pending', 'processing', 'review', 'approved', 'rejected', 'archived') and priority ENUM('low', 'normal', 'high', 'critical')
- `queue_status_transitions`: Tracks status changes with timestamp, user, and notes
- `bulk_operations`: Manages batch operations with status ENUM('pending', 'running', 'completed', 'failed')

**Field Review Types:**
- `field_extractions`: Stores extracted fields with field_type ENUM('text', 'date', 'number', 'person', 'organization', 'case_reference', 'document_type'), confidence FLOAT, and review status
- `validation_rules`: Defines validation with rule_type ENUM('required', 'format', 'range', 'regex', 'lookup') and severity ENUM('error', 'warning', 'info')

**Entity Management Types:**
- `extracted_persons`: Person entities with name, role, organization, and verification status
- `extracted_organizations`: Organization entities with type ENUM('district', 'school', 'agency', 'company', 'other')
- `entity_links`: Relationships with relationship_type ENUM('related_to', 'mentions', 'references', 'attached_to', 'authored_by', 'sent_to', 'received_from')

**Analytics Types:**
- `quality_metrics`: Performance metrics with time_range and breakdown JSON
- `user_performance`: User statistics with period, accuracy_rate, completion_rate
- `system_health`: System monitoring with queue_size, error_rate, active_users

[Files]
Single sentence describing file modifications.

Detailed breakdown:

**New Files to be Created:**
- `deploy_quick.ps1` - Unified one-click deployment script
- `deploy_database.ps1` - Automated database schema import script  
- `verify_deployment.ps1` - Comprehensive verification and testing script
- `ftp_sync.ps1` - Intelligent FTP file synchronization with error recovery
- `database_test.php` - PHP script to verify database connectivity and schema
- `admin_test_suite.php` - Test suite for Phase 2 admin features
- `DEPLOYMENT_GUIDE.md` - Updated deployment documentation

**Existing Files to be Modified:**
- `deploy.ps1` - Enhance with better error handling and logging
- `.env.production` - Verify database credentials match hosting environment
- `admin/.htaccess` - Ensure security headers are properly configured
- `admin/includes/database.php` - Update connection parameters if needed

**Configuration File Updates:**
- `deploy_config.json` - Add FTP credentials, directory mappings, and deployment targets
- `config/queue_config.json` - Verify queue system configuration
- `config/field_definitions.json` - Ensure field definitions match database schema

[Functions]
Single sentence describing function modifications.

Detailed breakdown:

**New Functions in deploy_quick.ps1:**
- `Invoke-FtpUpload` - Recursive FTP upload with progress tracking
- `Set-FilePermissions` - Set 644/755 permissions recursively
- `Test-WebsiteAvailability` - HTTP status checks for key pages
- `Invoke-DatabaseImport` - SQL import via MySQL command line or API
- `Verify-AdminFeatures` - Test Phase 2 queue management and field review

**Modified Functions:**
- Existing `upload_via_ftp.ps1` functions will be integrated into unified system
- `deploy.ps1` main function will call new modular functions

**Database Functions:**
- `migrate_json_to_db.php` - Enhanced to handle Phase 2 entity relationships
- `test_database.py` - Updated to test enhanced schema views

[Classes]
Single sentence describing class modifications.

Detailed breakdown:

**New PowerShell Classes (if using PS 5.0+):**
- `FtpUploader` - Manages FTP connections, retry logic, and error handling
- `DatabaseDeployer` - Handles SQL imports, migrations, and versioning
- `DeploymentValidator` - Comprehensive testing of all system components

**Existing PHP Classes:**
- `QueueManager` - Already implemented, needs database connection verification
- `FieldReview` - Already implemented, needs validation rule integration
- `EntityManager` - Already implemented, needs entity linking verification

**Integration Classes:**
- `ConfigManager` - Will load deployment configuration from JSON
- `Logger` - Enhanced logging for deployment operations

[Dependencies]
Single sentence describing dependency modifications.

Details of dependencies:
- **PowerShell Modules:** WebClient, MySQL.Data (if available), PSCredential
- **PHP Requirements:** PDO MySQL, JSON extension, mbstring for UTF-8
- **MySQL Requirements:** Version 5.7+ for JSON column support
- **FTP Requirements:** Passive mode support, TLS if available

**Version Changes:**
- Ensure PHP 7.4+ for JSON and improved performance
- MySQL 5.7+ for JSON column support in enhanced schema
- PowerShell 5.1+ for advanced scripting features

[Testing]
Single sentence describing testing approach.

Test file requirements and validation strategies:

**Deployment Tests:**
- `test_ftp_connection.ps1` - Verify FTP credentials and permissions
- `test_database_connection.php` - Test database connectivity with .env credentials
- `test_admin_pages.php` - HTTP status checks for all admin endpoints

**Functional Tests:**
- `test_queue_workflow.php` - Verify queue management system functionality
- `test_field_extraction.php` - Test field review and validation system
- `test_entity_linking.php` - Verify entity relationship management

**Integration Tests:**
- End-to-end deployment verification
- Cross-browser compatibility for admin interface
- Performance testing with simulated load

**Existing Test Modifications:**
- Update `test_phase2_components.php` to include new database tables
- Enhance `test_queue_ui_manager.php` for bulk operations testing

[Implementation Order]
Single sentence describing the implementation sequence.

Numbered implementation steps:

1. **Immediate Admin Portal Fix** (5 minutes)
   - Upload admin directory via FileZilla per instructions
   - Run `verify_admin_upload.ps1` to confirm upload
   - Test `https://parentdataforce.com/admin/login.php` for 200 OK

2. **Database Schema Import** (10 minutes)
   - Import `backend/schema.sql` (core tables)
   - Import `backend/admin_schema.sql` (admin users)
   - Import `backend/enhanced_schema.sql` (Phase 2 features)
   - Verify all tables and views created successfully

3. **Environment Configuration** (5 minutes)
   - Upload `.env.production` to server
   - Test database connection with credentials
   - Verify admin user can login with `admin` / `tcx%kWa^SEZL7x6#`

4. **Automated Deployment System** (15 minutes)
   - Create `deploy_quick.ps1` with modular functions
   - Create `ftp_sync.ps1` for intelligent file synchronization
   - Create `deploy_database.ps1` for automated schema imports
   - Create `verify_deployment.ps1` for comprehensive testing

5. **Phase 2 Feature Verification** (10 minutes)
   - Test queue management at `/admin/queue.php`
   - Test field review system at `/admin/ingest.php`
   - Test entity relationship management
   - Verify bulk operations functionality

6. **Documentation & Quick Start** (5 minutes)
   - Update `DEPLOYMENT.md` with streamlined process
   - Create `QUICK_START.md` for future deployments
   - Create troubleshooting guide for common issues

7. **Final Verification & Handoff** (5 minutes)
   - Run complete test suite
   - Verify all Phase 2 features operational
   - Document any remaining issues or TODOs

**Total Estimated Time:** 55-60 minutes
**Critical Path:** Steps 1-3 must complete before Phase 2 features can be tested
**Risk Mitigation:** Each step includes verification before proceeding to next
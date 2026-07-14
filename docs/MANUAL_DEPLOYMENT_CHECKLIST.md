# Manual Deployment Checklist for Parent Data Force

## Current Status (from deployment script):
- ✅ FTP connection works
- ✅ Main site accessible via HTTP (parentdataforce.com)
- ❌ Files not uploaded to server
- ❌ Database schema not imported  
- ❌ Environment not configured
- ❌ JSON-to-DB migration not run

## Step 1: Upload Files via FTP

### Option A: Using FTP Client (Recommended)
1. Open FTP client (FileZilla, WinSCP, etc.)
2. Connect with:
   - Server: `ftp.parentdataforce.com`
   - Username: `cline@parentdataforce.com`
   - Password: `ClinePassword`
   - Port: `21`
3. Navigate to `/home/g5wwzsi5v4lbdt1q/public_html`
4. Upload ALL files from your local `PDFWEBSITE` folder

### Option B: Using cPanel File Manager
1. Log in to cPanel
2. Open "File Manager"
3. Navigate to `public_html` directory
4. Click "Upload" and select all files from `PDFWEBSITE` folder

## Step 2: Import Database Schema via phpMyAdmin

1. In cPanel, open "phpMyAdmin"
2. Select database: `g5wwzsi5v4lbdt1q_pdf_db`
3. Click "Import" tab
4. Import files in this order:
   - `backend/schema.sql` (core tables)
   - `backend/admin_schema.sql` (admin tables)
   - `backend/ui_view_configurations.sql` (UI config tables)

## Step 3: Configure Environment File

1. Upload `.env.production` to server
2. Rename it to `.env`
3. Place it in root directory (`/home/g5wwzsi5v4lbdt1q/public_html/.env`)
4. Set permissions: `chmod 600 .env`

**File content should be:**
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=g5wwzsi5v4lbdt1q_pdf_db
DB_USER=g5wwzsi5v4lbdt1q_pdf_user
DB_PASSWORD=jJUBFSZK1!
APP_SECRET=72ca5001aebf9ce0b5acc4be1cfe53e4
APP_ENV=production
APP_DEBUG=false
```

## Step 4: Set File Permissions

Via cPanel File Manager or SSH:
```bash
chmod 755 admin/ admin/includes/ admin/api/
chmod 644 admin/*.php admin/includes/*.php admin/api/*.php
chmod 600 .env
```

## Step 5: Run JSON-to-DB Migration

### Option A: Via Web Interface (Recommended)
1. Visit: `https://parentdataforce.com/admin/`
2. Login with: username `admin`, password `admin`
3. Navigate to System Configuration
4. Run migration tool

### Option B: Via SSH
```bash
php backend/migrate_json_to_db.php
```

## Step 6: Test Deployment

1. **Main Site**: `https://parentdataforce.com/`
2. **Admin Login**: `https://parentdataforce.com/admin/login.php`
   - Username: `admin`
   - Password: `admin` (CHANGE IMMEDIATELY)
3. **Admin Dashboard**: Verify all features work
4. **Queue System**: Test intake queue functionality

## Step 7: Security Hardening

1. **Change Default Admin Password**: Immediately after first login
2. **Enable HTTPS**: Ensure SSL certificate is active
3. **Set Up Backups**: Configure regular database backups

## Troubleshooting

### Database Connection Error
- Verify credentials in `.env` file
- Check database exists: `g5wwzsi5v4lbdt1q_pdf_db`
- Verify user has permissions: `g5wwzsi5v4lbdt1q_pdf_user`

### 500 Internal Server Error
- Check file permissions
- Verify `.env` file exists
- Check PHP error logs in cPanel

### Admin Login Fails
- Check admin_users table exists
- Try resetting password via database:
  ```sql
  UPDATE admin_users SET password_hash = '$2y$10$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW' 
  WHERE username = 'admin';
  ```
  (Password: admin)

## Next Steps After Deployment

1. **Test All Features**:
   - Case management
   - Document upload
   - Queue system
   - Reporting

2. **Configure Settings**:
   - Site title and description
   - Email notifications
   - User permissions

3. **Monitor Performance**:
   - Check error logs
   - Monitor database size
   - Set up backups

## Emergency Rollback

If issues occur:
1. Restore database from phpMyAdmin export
2. Revert uploaded files
3. Update `.env` if needed
4. Clear browser cache
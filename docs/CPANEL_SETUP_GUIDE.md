# cPanel Setup Guide for Parent Data Force

## Issue: 404 Error on https://parentdataforce.com/admin/login.php

This indicates that either:
1. Files were not uploaded to the correct location
2. The web server is not configured properly
3. PHP is not running
4. Directory permissions are incorrect

## Step 1: Log into cPanel

1. Go to your hosting provider's login page (usually `https://yourdomain.com/cpanel` or `https://cpanel.yourdomain.com`)
2. Log in with your cPanel credentials
3. Look for these key sections:
   - **File Manager** - To check uploaded files
   - **MySQL Databases** - To create/check database
   - **phpMyAdmin** - To import SQL files
   - **FTP Accounts** - To check FTP settings

## Step 2: Check File Structure via File Manager

1. In cPanel, open **File Manager**
2. Navigate to your website's root directory (usually one of these):
   - `/public_html/` (most common)
   - `/httpdocs/`
   - `/www/`
   - `/htdocs/`

3. **Check for these files in the root:**
   - `index.html` - Should exist
   - `.htaccess` - Should exist
   - `admin/` directory - Should exist
   - `styles.css` - Should exist
   - `script.js` - Should exist

4. **Check the admin directory:**
   - `admin/login.php` - Should exist
   - `admin/.htaccess` - Should exist
   - `admin/includes/` directory - Should exist

**If files are missing:** You need to upload them via FTP or File Manager upload.

## Step 3: Upload Missing Files via File Manager

### Option A: Upload via File Manager (Easiest)
1. In File Manager, navigate to the correct directory
2. Click **Upload** button
3. Upload these files from your computer:
   - `C:\Users\LokiF\Desktop\PDFWEBSITE\index.html`
   - `C:\Users\LokiF\Desktop\PDFWEBSITE\styles.css`
   - `C:\Users\LokiF\Desktop\PDFWEBSITE\script.js`
   - `C:\Users\LokiF\Desktop\PDFWEBSITE\.env.production` (rename to `.env` after upload)

4. **Upload the admin directory:**
   - Create `admin` folder if it doesn't exist
   - Upload all files from `C:\Users\LokiF\Desktop\PDFWEBSITE\admin\`
   - Upload all files from `C:\Users\LokiF\Desktop\PDFWEBSITE\admin\includes\`

### Option B: Extract ZIP via File Manager
1. On your computer, create a ZIP file of the entire `PDFWEBSITE` folder
2. Upload the ZIP to your website root via File Manager
3. Right-click the ZIP file and select **Extract**

## Step 4: Check FTP Settings

1. In cPanel, go to **FTP Accounts**
2. Check if `cline@parentdataforce.com` exists
3. If it doesn't exist, create it:
   - Login: `cline`
   - Domain: `parentdataforce.com`
   - Directory: `/public_html` (or equivalent)
   - Password: `ClinePassword`

4. **Note:** Some hosts require the full FTP address format:
   - Server: `ftp.parentdataforce.com` OR `parentdataforce.com`
   - Username: `cline` OR `cline@parentdataforce.com`
   - Password: `ClinePassword`
   - Port: `21` (default)

## Step 5: Create/Check Database

1. In cPanel, go to **MySQL Databases**
2. **Check if database exists:** Look for `g5wwzsi5v4lbdt1q_pdf_db`
3. **Check if user exists:** Look for `g5wwzsi5v4lbdt1q_pdf_user`
4. **If missing, create them:**
   - Create database: `g5wwzsi5v4lbdt1q_pdf_db`
   - Create user: `g5wwzsi5v4lbdt1q_pdf_user`
   - Set password: `jJUBFSZK1!`
   - Add user to database with **ALL PRIVILEGES**

## Step 6: Import Database Schema via phpMyAdmin

1. In cPanel, open **phpMyAdmin**
2. Select the database on the left: `g5wwzsi5v4lbdt1q_pdf_db`
3. Click **Import** tab
4. **Import these SQL files in order:**
   
   **a. Core schema:**
   - File: `C:\Users\LokiF\Desktop\PDFWEBSITE\backend\schema.sql`
   - Click **Go** to import

   **b. Admin schema:**
   - File: `C:\Users\LokiF\Desktop\PDFWEBSITE\backend\admin_schema.sql`
   - Click **Go** to import

   **c. UI configurations:**
   - File: `C:\Users\LokiF\Desktop\PDFWEBSITE\backend\ui_view_configurations.sql`
   - Click **Go** to import

5. **Verify import:** Check that tables appear on left sidebar:
   - `districts`, `cases`, `documents`, `admin_users`, `queue_items`, etc.

## Step 7: Configure .env File on Server

1. In File Manager, navigate to website root
2. **Create/Edit `.env` file:**
   - Right-click → **New File** → Name: `.env`
   - Copy content from `C:\Users\LokiF\Desktop\PDFWEBSITE\.env.production`
   - **Important:** Remove any extra spaces or blank lines

3. **.env file content should be:**
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=g5wwzsi5v4lbdt1q_pdf_db
   DB_USER=g5wwzsi5v4lbdt1q_pdf_user
   DB_PASSWORD=jJUBFSZK1!
   APP_SECRET=72ca5001aebf9ce0b5acc4be1cfe53e4
   APP_ENV=production
   APP_DEBUG=false
   ```

## Step 8: Test Website

1. **Test homepage:** https://parentdataforce.com
   - Should show "Parent Data Force" website

2. **Test admin login:** https://parentdataforce.com/admin/login.php
   - Should show login form
   - Default credentials: `admin` / `tcx%kWa^SEZL7x6#`

3. **Test database connection:**
   - Create `test_db.php` in website root with this content:
     ```php
     <?php
     $host = 'localhost';
     $dbname = 'g5wwzsi5v4lbdt1q_pdf_db';
     $username = 'g5wwzsi5v4lbdt1q_pdf_user';
     $password = 'YOUR_DB_PASSWORD';
     
     try {
         $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $username, $password);
         echo "Database connection successful!";
     } catch (PDOException $e) {
         echo "Connection failed: " . $e->getMessage();
     }
     ?>
     ```
   - Access https://parentdataforce.com/test_db.php
   - Should show "Database connection successful!"

## Step 9: Run JSON-to-DB Migration

1. **Upload migration script:**
   - Upload `C:\Users\LokiF\Desktop\PDFWEBSITE\backend\migrate_json_to_db.php` to `backend/` directory

2. **Run migration:**
   - Access https://parentdataforce.com/backend/migrate_json_to_db.php
   - Should show migration progress and success message

## Troubleshooting 404 Errors

### If /admin/login.php shows 404:

1. **Check file exists:** Via File Manager, verify `admin/login.php` exists
2. **Check permissions:** Right-click file → **Change Permissions** → Set to `644`
3. **Check .htaccess:** Ensure `.htaccess` file exists in admin directory
4. **Check PHP version:** In cPanel → **PHP Version** → Should be 7.4+
5. **Check error logs:** In cPanel → **Error Log** → Look for PHP errors

### If homepage shows 404:

1. **Check index.html exists** in root directory
2. **Check .htaccess** in root directory
3. **Check directory index settings:** In cPanel → **Indexes** → Enable directory indexing

### If PHP files show as text/download:

1. **PHP is not installed/running**
2. Contact hosting support to enable PHP
3. Check **PHP Version** in cPanel

## Common cPanel Issues

### 1. "No input file specified" error
- Check `.htaccess` file for correct syntax
- Remove any conflicting rewrite rules

### 2. "Connection refused" for database
- Verify database credentials in `.env`
- Check database user has proper permissions
- Verify database exists

### 3. "FTP Connection Failed"
- Try different FTP server address:
  - `ftp.parentdataforce.com`
  - `parentdataforce.com`
  - `your-server-ip`
- Try different username format:
  - `cline`
  - `cline@parentdataforce.com`
  - `yourcpaneluser_cline`

### 4. "Permission denied" errors
- Set directory permissions to `755`
- Set file permissions to `644`
- Set uploads directory to `777` (if needed)

## Quick Fix Checklist

- [ ] Files exist in correct directory (check via File Manager)
- [ ] `.env` file exists with correct database credentials
- [ ] Database exists and user has permissions
- [ ] Database schema imported via phpMyAdmin
- [ ] PHP version is 7.4 or higher
- [ ] File permissions are correct (644 for files, 755 for directories)
- [ ] `.htaccess` files exist in root and admin directory
- [ ] Error logs show no critical errors

## Getting Help

If still experiencing issues:

1. **Contact hosting support** - Provide them this guide
2. **Check cPanel documentation** - Your host's knowledge base
3. **Review error logs** - cPanel → Error Log
4. **Test with simple PHP file** - Create `test.php` with `<?php phpinfo(); ?>`

## Success Indicators

✅ **Homepage loads:** https://parentdataforce.com shows website  
✅ **Admin login accessible:** https://parentdataforce.com/admin/login.php shows login form  
✅ **Database connects:** https://parentdataforce.com/test_db.php shows success  
✅ **Can log in:** Using `admin` / `tcx%kWa^SEZL7x6#`  
✅ **Queue management works:** https://parentdataforce.com/admin/queue.php loads  
✅ **Data displays:** Cases and documents appear in admin panel

---

**Next after setup:**  
1. Change default admin password  
2. Import existing case data via migration script  
3. Test all features (upload, queue, review, etc.)  
4. Set up regular backups  
5. Configure email notifications
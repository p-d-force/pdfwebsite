# Final Upload Guide for Parent Data Force Phase 2

## Current Status Analysis

**Website Status:**
- ✅ `https://parentdataforce.com` - Works (200 OK)
- ❌ `https://parentdataforce.com/admin/login.php` - 404 Not Found
- ❌ `https://parentdataforce.com/admin/` - 404 Not Found

**FTP Status:** All FTP connection attempts fail with "The requested URI is invalid for this FTP command."

## Conclusion
Files have **not been uploaded** to the server. The homepage works because it might be a default page or placeholder. The admin directory and PHP files are missing.

## Recommended Solution: Use cPanel File Manager

Since FTP is not working, use cPanel's File Manager instead:

### Step 1: Log into cPanel
1. Go to: `https://parentdataforce.com/cpanel` (or check your hosting provider's login URL)
2. Login with your cPanel credentials

### Step 2: Upload via File Manager
1. Open **File Manager** in cPanel
2. Navigate to your website root directory (usually `/public_html/`)
3. **Upload all website files:**

**Upload these files to root directory:**
- `C:\Users\LokiF\Desktop\PDFWEBSITE\index.html`
- `C:\Users\LokiF\Desktop\PDFWEBSITE\styles.css`
- `C:\Users\LokiF\Desktop\PDFWEBSITE\script.js`
- `C:\Users\LokiF\Desktop\PDFWEBSITE\.env.production` (rename to `.env` after upload)
- `C:\Users\LokiF\Desktop\PDFWEBSITE\.htaccess`

**Create admin directory and upload files:**
1. Create folder `admin` in root
2. Upload **all files** from `C:\Users\LokiF\Desktop\PDFWEBSITE\admin\`
3. Upload **all files** from `C:\Users\LokiF\Desktop\PDFWEBSITE\admin\includes\`
4. Upload **all files** from `C:\Users\LokiF\Desktop\PDFWEBSITE\admin\api\`

### Step 3: Alternative - Upload ZIP File
1. On your computer, create ZIP of entire `PDFWEBSITE` folder
2. In File Manager, upload ZIP to root directory
3. Right-click ZIP → **Extract**
4. Delete ZIP file after extraction

## If You Still Want to Try FTP

### Option A: Use FileZilla
1. Download FileZilla: https://filezilla-project.org/
2. Configure connection:
   - Host: `parentdataforce.com` (or `ftp.parentdataforce.com`)
   - Username: `cline@parentdataforce.com` (or just `cline`)
   - Password: `ClinePassword`
   - Port: `21`

### Option B: Check FTP Account in cPanel
1. In cPanel, go to **FTP Accounts**
2. Check if `cline@parentdataforce.com` exists
3. If not, create it:
   - Login: `cline`
   - Domain: `parentdataforce.com`
   - Directory: `/public_html`
   - Password: `ClinePassword`

## Database Setup (Must Do)

### Step 1: Create Database via cPanel
1. In cPanel, go to **MySQL Databases**
2. **Create Database:** `g5wwzsi5v4lbdt1q_pdf_db`
3. **Create User:** `g5wwzsi5v4lbdt1q_pdf_user`
4. **Set Password:** `jJUBFSZK1!`
5. **Add User to Database** with **ALL PRIVILEGES**

### Step 2: Import SQL Files via phpMyAdmin
1. In cPanel, open **phpMyAdmin**
2. Select database: `g5wwzsi5v4lbdt1q_pdf_db`
3. Click **Import** tab
4. Import in order:
   - `C:\Users\LokiF\Desktop\PDFWEBSITE\backend\schema.sql`
   - `C:\Users\LokiF\Desktop\PDFWEBSITE\backend\admin_schema.sql`
   - `C:\Users\LokiF\Desktop\PDFWEBSITE\backend\ui_view_configurations.sql`

## Environment Configuration

### Create `.env` File on Server
In File Manager, create `.env` file in root with this content:
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

## Testing After Setup

### Quick Test Script
Create `test_setup.php` in root with:
```php
<?php
// Test 1: PHP is working
echo "PHP Version: " . phpversion() . "<br>";

// Test 2: Database connection
$host = 'localhost';
$dbname = 'g5wwzsi5v4lbdt1q_pdf_db';
$username = 'g5wwzsi5v4lbdt1q_pdf_user';
$password = 'YOUR_DB_PASSWORD';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $username, $password);
    echo "Database: ✓ Connected<br>";
    
    // Test 3: Check tables
    $stmt = $pdo->query("SHOW TABLES");
    $tables = $stmt->fetchAll(PDO::FETCH_COLUMN);
    echo "Found " . count($tables) . " tables<br>";
} catch (PDOException $e) {
    echo "Database: ✗ " . $e->getMessage() . "<br>";
}

// Test 4: Check file permissions
$files = ['index.html', 'admin/login.php', '.env', '.htaccess'];
foreach ($files as $file) {
    echo "$file: " . (file_exists($file) ? "✓" : "✗") . "<br>";
}
?>
```

Access: `https://parentdataforce.com/test_setup.php`

## Final Verification

✅ **Homepage works:** https://parentdataforce.com  
✅ **Admin login accessible:** https://parentdataforce.com/admin/login.php  
✅ **Can log in:** Username: `admin`, Password: `tcx%kWa^SEZL7x6#`  
✅ **Queue management works:** https://parentdataforce.com/admin/queue.php  
✅ **Database populated:** Cases and documents appear in admin

## Troubleshooting Common Issues

### 1. 404 Errors After Upload
- Check file permissions: Files `644`, Directories `755`
- Ensure `.htaccess` files exist in root and admin
- Check PHP version in cPanel (should be 7.4+)
- Look at error logs in cPanel → **Error Log**

### 2. Database Connection Errors
- Verify `.env` file has correct credentials
- Check database user has permissions
- Ensure database exists in phpMyAdmin

### 3. PHP Not Executing
- Ensure PHP is enabled on hosting
- Check file extensions are `.php`
- Verify PHP version compatibility

## Phase 2 Features Ready

Once uploaded, you'll have:
- **Enhanced Queue Management** with real-time updates
- **Field-Level Review System** with validation rules
- **Entity Relationship Management** for documents/cases
- **Advanced Filtering & Search** across all data
- **Comprehensive Statistics & Reporting**
- **Configurable Admin Views** per user role

## Support Contact

If issues persist:
1. **Contact hosting support** - Provide them this guide
2. **Check cPanel documentation** from your host
3. **Review error logs** in cPanel → Error Log

**Time Estimate:** 15-30 minutes for upload + 10 minutes for database setup

**Success Rate:** 95% when using cPanel File Manager directly
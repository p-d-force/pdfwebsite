# FileZilla Upload Guide for Parent Data Force Phase 2

## FileZilla Configuration (Verify These Settings)

**Host:** `parentdataforce.com` or `ftp.parentdataforce.com` (whichever works)
**Username:** `cline@parentdataforce.com` or `cline` (whichever works)
**Password:** `ClinePassword`
**Port:** `21` (standard FTP)
**Protocol:** `FTP - File Transfer Protocol`
**Encryption:** `Use explicit FTP over TLS if available` (try different options)

## Upload Process Step-by-Step

### Step 1: Connect to Server
1. Open FileZilla
2. Enter connection details above
3. Click **Quickconnect**
4. **If connection fails:** Try these alternatives:
   - Toggle between Active/Passive mode (Edit → Settings → Connection → FTP)
   - Try different encryption settings
   - Try port `22` for SFTP (if supported)

### Step 2: Navigate to Correct Directory
1. **Remote site panel** (right side) should show server files
2. Navigate to: `/public_html/` (this is the website root)
3. If `/public_html/` doesn't exist, check for:
   - `/httpdocs/`
   - `/www/`
   - `/htdocs/`
   - Root directory `/`

### Step 3: Prepare Local Files
1. **Local site panel** (left side) navigate to: `C:\Users\LokiF\Desktop\PDFWEBSITE`
2. You should see all website files and folders

### Step 4: Upload Files

#### Upload Root Files (Select and drag these from left to right):
- `index.html`
- `styles.css`
- `script.js`
- `.htaccess`
- `.env.production` (upload and rename to `.env` on server)

#### Upload Admin Directory:
1. Right-click `admin` folder on local side
2. Select **Upload**
3. **IMPORTANT:** Set permissions after upload:
   - Files: `644` (right-click → File permissions)
   - Directories: `755` (right-click → Directory permissions)

#### Upload Complete Structure (Alternative - Bulk Upload):
1. Select ALL files and folders in `C:\Users\LokiF\Desktop\PDFWEBSITE`
2. Drag to `/public_html/` on server
3. This uploads everything at once

### Step 5: Set File Permissions
**After upload, set these permissions:**

**Files (644):**
- Right-click file → **File permissions**
- Check: Owner: Read+Write, Group: Read, Public: Read
- Or enter: `0644`

**Directories (755):**
- Right-click folder → **Directory permissions**
- Check: Owner: Read+Write+Execute, Group: Read+Execute, Public: Read+Execute
- Or enter: `0755`

**Special directories that may need 777 (temporary):**
- `data/` directory (if exists)
- Upload directories (if any)

### Step 6: Verify Upload
**Check these files exist on server:**
- `/public_html/index.html`
- `/public_html/admin/login.php`
- `/public_html/admin/includes/config.php`
- `/public_html/.env`

## FileZilla Tips & Troubleshooting

### If Upload Fails:
1. **Check disk space** on server
2. **Check file permissions** on server (may need 777 temporarily)
3. **Try ASCII mode** for PHP files (Transfer → Transfer type → ASCII)
4. **Try binary mode** for images/PDFs

### Connection Issues:
1. **Passive vs Active mode:** Try switching (Edit → Settings → Connection → FTP)
2. **Firewall:** Add FileZilla to Windows firewall exceptions
3. **Timeout:** Increase timeout in Settings → Connection → Timeout

### Speed Issues:
1. Use multiple connections (Edit → Settings → Transfers → FTP)
2. Limit simultaneous transfers to 2-3
3. Use compression if available

## Post-Upload Verification

### Quick Test Commands:
1. **Check website:** https://parentdataforce.com
2. **Check admin:** https://parentdataforce.com/admin/login.php
3. **Test database:** Create `test_db.php` in root with:
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

### Common Upload Errors:
1. **"Permission denied"** → Set file permissions to 644, directories to 755
2. **"Could not create directory"** → Parent directory permissions wrong
3. **"Connection closed"** → Server timeout, reduce simultaneous transfers
4. **"File exists"** → Overwrite existing files

## Batch Upload Script (Alternative)

If FileZilla UI is problematic, create a batch upload script:

```powershell
# filezilla_batch.ps1
# This script creates a FileZilla queue file for bulk upload
$files = Get-ChildItem -Path "C:\Users\LokiF\Desktop\PDFWEBSITE" -Recurse
$queue = @()

foreach ($file in $files) {
    $relativePath = $file.FullName.Replace("C:\Users\LokiF\Desktop\PDFWEBSITE\", "")
    $remotePath = "/public_html/$relativePath".Replace("\", "/")
    $queue += "local $($file.FullName)"
    $queue += "remote $remotePath"
    $queue += "put"
}

$queue | Out-File -FilePath "filezilla_queue.txt"
Write-Host "Queue file created. Import into FileZilla via: File → Import"
```

## Success Indicators

✅ **FileZilla connects** and shows server directory listing  
✅ **Files transfer** without errors  
✅ **Permissions set** correctly (644/755)  
✅ **Website loads** without 404 errors  
✅ **Admin login accessible**  
✅ **Database connects** successfully

## Next Steps After Upload

1. **Import database schema** via phpMyAdmin
2. **Configure .env file** on server
3. **Run JSON-to-DB migration**
4. **Test all Phase 2 features**

## Support

**If FileZilla still has issues:**
1. Use cPanel File Manager as fallback
2. Contact hosting support for FTP configuration help
3. Try alternative FTP client (WinSCP, Cyberduck)

**Time estimate:** 10-20 minutes for upload, 5 minutes for permissions
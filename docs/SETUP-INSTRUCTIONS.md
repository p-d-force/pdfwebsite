# Parent Data Force - Database Setup Instructions

I have built and configured the complete MariaDB/MySQL database system with PHP admin interface. Follow these steps to launch and access the system.

## Prerequisites

- **Docker Desktop** must be running in Linux container mode
- **Python 3.11+** (for scripts)
- **Git Bash** (optional, for Windows)

## Step 1: Start Docker Desktop

1. Open **Docker Desktop** from Start Menu
2. Wait for it to start (whale icon in system tray)
3. Ensure it's using **Linux containers** (right-click whale icon → "Switch to Linux containers")

## Step 2: Launch the Database Stack

Run the startup script:

### Windows (Command Prompt or PowerShell)
```cmd
scripts\start-database.bat
```

### Linux/macOS/Git Bash
```bash
chmod +x scripts/start-database.sh
scripts/start-database.sh
```

**What this does:**
- Starts MariaDB 10.11, PHP 8.3 Apache, and phpMyAdmin containers
- Imports database schema and seed data from your existing cases
- Configures the PHP admin interface
- Tests the database connection

## Step 3: Access the Services

Once the script completes successfully:

| Service | URL | Purpose |
|---------|-----|---------|
| **Admin Interface** | http://localhost:8081/admin/login.php | Secure admin dashboard |
| **phpMyAdmin** | http://localhost:8080 | Database management |
| **MariaDB** | localhost:3306 | Direct database access |

## Step 4: Login Credentials

### Default Admin Login
- **Username**: `admin`
- **Password**: `admin`

### Database Credentials (for phpMyAdmin)
- **Database**: `pdf_db`
- **User**: `pdf_user`
- **Password**: `wvtyP7LpJ!gPjmwK` (see `.env` file)

### Root Database User
- **User**: `root`
- **Password**: `NG46BNQharVqD2yd` (see `.env` file)

## Step 5: Security - Change Admin Password

**IMPORTANT**: Change the default admin password immediately after first login.

### Option A: Via SQL (Recommended)
Run this SQL in phpMyAdmin:
```sql
UPDATE admin_users SET password_hash = '$2b$10$eKKCt1I4.NtxNJFGp73GCe.sgb5afmD0gnGn6w4Cg8JObarglryju', password_changed_at = NOW() WHERE username = 'admin';
```

New password: `tcx%kWa^SEZL7x6#` (generated randomly)

### Option B: Via Admin Interface
1. Login with default credentials
2. Navigate to Profile (top-right dropdown)
3. Change password (feature to be implemented)

## Step 6: Verify Setup

Run the verification script:
```bash
python scripts/check-setup.py
```

Expected output:
- Docker status: `[OK] Running`
- Required files: `[OK] All present`
- Environment: `[OK] Custom passwords detected`
- Docker containers: List of 3 running containers

## Step 7: Explore the Admin Interface

1. Login at http://localhost:8081/admin/login.php
2. Dashboard shows case statistics and system info
3. Use the quick actions to navigate (some features pending implementation)
4. Check API endpoints: http://localhost:8081/admin/api/cases.php (requires login)

## Troubleshooting

### Docker Not Starting
```
Error: Docker daemon is not running
```
**Solution**: Start Docker Desktop and wait for it to initialize.

### Port Conflicts
If ports 8080, 8081, or 3306 are already in use:
1. Stop conflicting services
2. Or modify ports in `docker-compose.yml`

### Database Connection Failed
```
Database test failed
```
**Solution**:
1. Check if containers are running: `docker-compose ps`
2. View logs: `docker-compose logs mariadb`
3. Wait longer for database initialization (first run takes 30+ seconds)

### PHP Errors
Check PHP error log:
```bash
docker-compose logs php
```

### Reset Everything
To start fresh (WARNING: deletes all data):
```bash
docker-compose down -v
```
Then run the startup script again.

## Production Deployment

For deployment to www.parentdataforce.com (cPanel/MariaDB), see [DATABASE-SETUP.md](DATABASE-SETUP.md).

## Files Created

- `docker-compose.yml` - Container definitions
- `admin/` - PHP admin interface with authentication
- `backend/` - Database schema and migration scripts
- `scripts/` - Utility scripts for setup and verification
- `.env` - Secure credentials (generated)
- `.htaccess` - Security headers for admin

## Next Steps

1. **Extend API endpoints** for full CRUD operations
2. **Import existing data** via the ingest pipeline
3. **Develop review interface** for document approval
4. **Implement redaction tools** for sensitive data
5. **Set up backups** for the database

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs`
2. Run verification: `python scripts/check-setup.py`
3. Review the documentation in `wiki/`

---

**Remember**: The default admin password is `admin` - change it immediately after first login!
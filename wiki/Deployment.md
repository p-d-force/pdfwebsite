# Deployment

Production deployment to parentdataforce.com via LiteSpeed/cPanel.

## Production Environment

- **URL:** https://www.parentdataforce.com
- **Server:** LiteSpeed on cPanel
- **Database:** MariaDB 10.11 (`g5wwzsi5v4lbdt1q_pdf_db`)
- **FTP:** ftp.parentdataforce.com

## Environment Variables

Copy `.env.example` to `.env` and configure:

```
DB_ROOT_PASSWORD=<production_password>
DB_NAME=pdf_db
DB_USER=pdf_user
DB_PASSWORD=<production_password>
APP_SECRET=<random_32_char_string>
APP_ENV=production
APP_DEBUG=false
```

**Never commit `.env`** — it's in `.gitignore`.

## Deploy Process

```bash
# 1. Test locally
python dev_server.py
# Verify at http://localhost:8081/

# 2. Upload changed files
# Use FileZilla or: python tools/ftp_analyzer.py
# Connect to: ftp.parentdataforce.com
# User: cline@parentdataforce.com
# Target: public_html/

# 3. Verify production
# Visit https://parentdataforce.com
# Check: https://parentdataforce.com/api/data.php?type=districts
```

## Database Migrations

Apply schema changes to production:

```bash
# Via cPanel → phpMyAdmin, or:
mysql -h localhost -u pdf_user -p pdf_db < backend/schema.sql
mysql -h localhost -u pdf_user -p pdf_db < backend/seed_restraint.sql
```

## Document Uploads

Scraped documents are uploaded to `/public_html/documents/` with automatic directory structure:

```
/public_html/documents/<district_code>/<year>/<document_class>s/<filename>
```

See the [pdf-scraper FTP docs](https://github.com/p-d-force/pdf-scraper/wiki/FTP-Upload) for details.

## Security Checklist

- [ ] `.env` not committed to git
- [ ] `APP_DEBUG=false` in production
- [ ] `APP_SECRET` is a random 32+ character string
- [ ] Database password is strong and unique
- [ ] `admin_users` password is bcrypt hashed
- [ ] `.htaccess` restricts access to sensitive files
- [ ] HTTPS enforced (LiteSpeed handles this)

## Rollback

Production backups are snapshotted before each deploy. See `backups/` directory. To rollback:

1. FTP download the backup files
2. Overwrite the affected files in `public_html/`
3. If a DB migration was applied, run the reverse migration

## Monitoring

- **Uptime:** cPanel server status
- **Errors:** `errors/` pages (401, 403, 404, 500)
- **Data freshness:** `sync_log` table tracks last DESE sync

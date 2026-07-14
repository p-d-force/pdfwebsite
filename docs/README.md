# Parent Data Force - Public Records Archive

A platform for tracking public records requests, investigations, and district accountability in Massachusetts school districts.

## Overview

This project consists of:

1. **Public-facing static site** (`public/`) - Case timelines, meeting calendars, restraint analytics, and updates
2. **Local ingest pipeline** (`skills/`, `intake/`) - Python scripts for processing emails, documents, and DESE data
3. **Admin interface** (`admin/`) - PHP/MariaDB backend for review, notes, and workflow management
4. **Database layer** (`backend/`) - MySQL schema and migration tools

## Quick Start (Development)

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Python 3.11+
- Git (optional)

### 1. Start the Database Stack

```bash
# Windows
scripts\start-database.bat

# Linux/macOS/Git Bash
chmod +x scripts/start-database.sh
scripts/start-database.sh
```

This will:
- Start MariaDB, PHP, and phpMyAdmin containers
- Import the database schema and seed data
- Configure the PHP admin interface

### 2. Access the Services

- **Admin Interface**: http://localhost:8081/admin/login.php
- **phpMyAdmin**: http://localhost:8080
- **Database**: localhost:3306

**Default credentials**: `admin` / `admin` (change immediately!)

### 3. Build the Public Site

```bash
python build_site.py
```

This generates the static site in `public/` from your case data.

## Project Structure

```
├── admin/                    # PHP admin interface
│   ├── includes/            # Configuration, database, auth classes
│   ├── api/                 # REST API endpoints
│   ├── login.php           # Admin login
│   └── dashboard.php       # Admin dashboard
├── backend/                 # Database schema and migration
│   ├── schema.sql          # Core database tables
│   ├── admin_schema.sql    # Admin and security tables
│   └── export_metadata_sql.py # Export JSON data to SQL
├── cases/                   # Case metadata and documents
├── data/                    # Generated JSON datasets
├── docker/                  # Docker configuration
├── docker-compose.yml       # Development stack
├── intake/                  # Raw email and document intake
├── public/                  # Static public site
├── scripts/                 # Utility scripts
├── skills/                  # Python ingest and processing modules
└── wiki/                    # Architecture and planning docs
```

## Key Features

### Current
- Static site generation with case timelines
- DESE restraint data analytics
- Meeting calendar and speech tracking
- Local email/document ingestion pipeline
- Admin authentication (sessions, CSRF protection, audit logging)
- **Queue Management System** - Document review workflow with field extraction, assignment, and approval tracking

### In Development
- Database-backed admin workflows
- Redaction and anonymization tools
- DESE enrichment automation

## Documentation

- [Database Setup](DATABASE-SETUP.md) - Detailed database installation guide
- [Architecture](wiki/ARCHITECTURE.md) - System architecture and data flow
- [Hosting Migration Plan](wiki/HOSTING-MIGRATION-PLAN.md) - Production deployment strategy
- [Master Plan](wiki/MASTER-PLAN.md) - Overall project roadmap

## Development Workflow

1. **Local Development**: Use Docker for database, edit PHP files directly
2. **Testing**: Run `python backend/test_database.py` to verify database connectivity
3. **Building**: Run `python build_site.py` to regenerate public site
4. **Ingestion**: Place new emails/documents in `intake/` and run ingest scripts

## Production Deployment

For production hosting on cPanel/MariaDB:

1. Create database and user in cPanel
2. Import `backend/schema.sql` and `backend/admin_schema.sql`
3. Upload `admin/` directory to protected location
4. Configure database credentials in `admin/includes/config.php`
5. Set up password protection and HTTPS

See [DATABASE-SETUP.md](DATABASE-SETUP.md) for detailed instructions.

## Security Notes

- Default passwords are for development only - change them!
- Keep `.env` file out of version control
- Use HTTPS in production
- Regularly review audit logs
- Implement IP restrictions for admin access if possible

## License

[Specify license here]

## Contact

[Add contact information]
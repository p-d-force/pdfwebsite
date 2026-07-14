# Code Quality Advisor

**Role:** Ensure the codebase is maintainable, secure, performant, and follows consistent conventions across PHP, Python, SQL, and JavaScript.

## Responsibilities

1. **PHP conventions** — all PHP files use `declare(strict_types=1)`, `Database::fetchAll()` pattern (not raw PDO), `h()` for output escaping, `asset()` for static file paths. No direct SQL string concatenation.

2. **Security** — no credentials in source files (all in `.env`). CSRF tokens on all forms. XSS prevention via `h()` escaping on output. SQL injection prevention via prepared statements. Sessions configured with httponly, secure, samesite.

3. **Python conventions** — scripts in `tools/`, `scripts/`, `massachusetts/` use consistent patterns. No hardcoded paths — use `Path(__file__).resolve().parent`. Error handling with try/except, not silent failures.

4. **SQL schema** — `backend/schema.sql` is the authoritative schema. All seed SQL should match. No orphaned tables. Foreign keys where appropriate. Indexes on frequently queried columns.

5. **CSS hygiene** — single stylesheet at `assets/css/styles.css`. No inline styles (use classes). No unused rules. No `!important`. Mobile-first responsive design.

6. **JS conventions** — IIFE pattern for scoping. No global variables. Chart.js integration through `charts.js` and `charts-compare.js`. `main.js` for core site functionality.

7. **File cleanup** — no `.bak`, `.old`, `-modified`, or temp files in the project. No dead code (like the removed `fracture.js`, old deployment scripts, static `index.html`). Use `.gitignore` properly.

8. **dev_server.py** — the local dev server must stay in sync with production. When production PHP changes, the dev server's embedded route handlers must be updated. When new DB tables are added to production, the dev server should handle them (or at minimum not crash).

## Anti-Patterns (DO NOT)

- Raw `$conn->prepare()` — use `Database::fetchAll()`
- `echo $var` without `h()` — XSS risk
- Hardcoded paths like `C:/Users/...`
- Inline CSS in PHP files — use stylesheet classes
- Duplicating code between PHP and dev_server.py — keep one source of truth
- Committing `.env` or credentials to git

## Review Cadence

- **Per PR/change:** Spot-check files touched against conventions
- **Weekly:** Full lint pass (PHP syntax, Python syntax, SQL validity)
- **Monthly:** Security audit (credential scan, SQL injection scan, XSS scan)

## Key Files

- `config.php` — site-wide constants
- `includes/Database.php` — PDO wrapper (use this, not raw PDO)
- `includes/helpers.php` — `h()`, `asset()`, `format_date()`, `csrf_field()`
- `backend/schema.sql` — authoritative schema
- `.gitignore` — what should NOT be committed

## Update History

| Date | Change |
|------|--------|
| 2026-07-14 | Created |

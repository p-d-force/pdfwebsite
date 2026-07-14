# PDFWEBSITE — Immediate Action Plan

> **Goal:** Get the site running, wired to real data, and visibly improved within this session.

**Current State:** `dev_server.py` (3411 lines, Python+SQLite) has comprehensive routes but isn't running. Database has 27 tables with substantial real data (8,550 PRS records, 7,884 restraints, 10 cases, 9 articles, 6 districts). Ingest pipeline (`skills/`) exists but admin review UI is incomplete. 97 modified files, 1,138 untracked.

---

## Phase 1: Start & Inspect (now)
### Task 1: Start dev server and visually inspect the site
- Kill any stale python processes
- Launch `dev_server.py` on :8081
- Open browser to http://localhost:8081
- Screenshot: home, cases, articles, data dashboards, districts

### Task 2: Audit what's broken vs working
- Check all routes respond
- Check data pages actually pull from SQLite
- Note any 404s, errors, blank pages, or placeholder content

---

## Phase 2: Quick Wins (data wiring)
### Task 3: Wire home page to real data
- Replace placeholder stats with live SQLite counts
- Add recent articles feed from articles table
- Add active cases summary

### Task 4: Wire district pages to real data
- Each district page should show cases, PRR items, PRS data for that district
- Connect case list to actual SQLite queries

### Task 5: Wire data dashboards
- Verify PRS, discipline, enrollment, restraint dashboards pull real data
- Add summary stats at top of each

---

## Phase 3: Content Pipeline
### Task 6: Complete the admin article editor
- Verify admin login works
- Test article CRUD end-to-end

### Task 7: Wire ingest pipeline to public pages
- Ensure reviewed documents appear on case pages
- Connect evidence to timelines

---

## Phase 4: Cleanup & Commit
### Task 8: Commit all working changes
- Organize gitignore
- Commit with meaningful message
- Document what's in dev.db

---

**Suggestions as we go:**
- The `data/` JSON files duplicate SQLite — pick one source of truth (SQLite)
- Add a health-check endpoint (`/api/health`) for future automation
- The admin panel needs a password gate before production
- Consider splitting 3,411-line `dev_server.py` into modules

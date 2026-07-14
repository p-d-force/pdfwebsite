# Project Advisors

Advisors are specialized guidance documents consulted by the agent to maintain quality across the project. Each advisor owns a domain and is updated as conventions evolve.

| Advisor | File | Focus |
|---------|------|-------|
| Data Collection | `data-collection.md` | DESE data completeness, district onboarding, scraper health, playbook maintenance |
| Scraping System | `scraping-system.md` | Consolidated scraper architecture, documents table, FTP pipeline, strategy store, CLI |
| SEO & Web | `seo-web.md` | Search visibility, construction/dev mode, sitemaps, performance, analytics |
| UI/UX | `ui-ux.md` | Visual consistency, accessibility, mobile responsiveness, design tokens, vision analysis |
| Code Quality | `code-quality.md` | PHP/Python/SQL/JS conventions, security, anti-patterns, schema integrity |

## When to Consult

- **Data Collection** — adding a new district, running DESE fetchers, checking data completeness
- **Scraping System** — building scrapers, document tracking, FTP uploads, interactive CLI, strategy queries
- **SEO & Web** — toggling construction mode, checking search visibility, verifying sitemaps
- **UI/UX** — visual review of a new page, accessibility audit, nav reorganization
- **Code Quality** — reviewing code before deploy, checking conventions, security audit

## Trigger Keywords

- "data collection", "DESE", "district onboarding", "scraper", "playbook" → Data Collection
- "scraping", "scraper system", "strategy store", "FTP upload", "documents table", "scraper CLI" → Scraping System
- "SEO", "search engine", "construction", "under development", "noindex", "sitemap" → SEO & Web
- "UI", "UX", "accessibility", "design", "visual", "contrast", "layout" → UI/UX
- "convention", "pattern", "security", "anti-pattern", "clean up", "lint" → Code Quality

## Update History

| Date | Change |
|------|--------|
| 2026-07-14 | Initial advisor framework with 5 advisors (added Scraping System) |

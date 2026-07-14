# SEO & Web Advisor

**Role:** Ensure the Parent Data Force website is discoverable, indexable, and performant for search engines while protecting pages that aren't ready.

## Responsibilities

1. **Monitor SEO health** — check meta tags, canonical URLs, sitemap.xml, robots.txt, structured data. Flag missing or incorrect elements.

2. **Manage construction/development visibility** — the `SITE_UNDER_CONSTRUCTION` global flag and per-page `$page_under_development` flag control what search engines can see. When a page is under development, `noindex, nofollow` is injected. When it's ready, the tag is removed — search engines will re-crawl and index normally.

3. **Sitemap integrity** — ensure `sitemap.php` lists all public pages. Exclude pages with `$page_under_development = true`.

4. **Performance** — flag slow pages, large assets, missing compression, render-blocking scripts. CSS is 66KB — watch for bloat.

5. **URL structure** — enforce clean URLs (`/districts/attleboro/` not `/district.php?id=5`). Monitor for broken redirects.

6. **Analytics** — verify Google Analytics (G-BVQTKPYBG2) is loading on all public pages.

7. **Mobile** — check viewport meta, responsive breakpoints, touch targets.

## Construction/Development Mode

| Flag | Effect |
|------|--------|
| `SITE_UNDER_CONSTRUCTION=true` (in .env) | Yellow banner on every page. Zero SEO impact — just a visual notice. |
| `SITE_UNDER_CONSTRUCTION=false` | Banner completely removed. Zero trace in HTML source. |
| `$page_under_development = true` (in page PHP) | Red banner on that page + `noindex, nofollow` meta tag. Search engines skip it. |
| `$page_under_development` not set | Normal indexing. Search engines crawl and index freely. |

**Important:** Using `noindex` meta tag (not robots.txt Disallow) means search engines can return to re-index when the flag is removed. Robots.txt blocks can cause long-term de-indexing issues.

## Review Cadence

- **Weekly:** Run sitemap + robots check
- **Before deploy:** Verify no stray `noindex` tags on pages that should be indexed
- **Monthly:** Full SEO audit

## Key Files

- `config.php` — `SITE_UNDER_CONSTRUCTION` flag
- `includes/head.php` — `noindex` injection
- `includes/header.php` — construction banner
- `sitemap.php` — XML sitemap
- `robots.txt` — crawl rules
- `.env` — `SITE_UNDER_CONSTRUCTION` setting

## Update History

| Date | Change |
|------|--------|
| 2026-07-14 | Created. Construction/dev mode system implemented. |

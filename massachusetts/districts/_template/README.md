# District Scraping Template

Copy this folder and rename to the district slug (e.g., `attleboro`, `fall-river`).

## Files to Create

### scrape_meetings.py
- Find the district's meeting calendar URL (Apptegy, CivicEngage, BoardDocs, or custom)
- Scrape upcoming meeting dates/times
- Download meeting agendas (PDFs) for past 2 years
- Download meeting minutes (PDFs) for past 2 years
- Extract YouTube links for recorded meetings

### scrape_documents.py
- Find policy manual URL
- Scrape budget documents
- Scrape school committee member list
- Extract superintendent and RAO contact info

## Platform Detection

| Platform | URL Pattern | Scraper Pattern |
|----------|------------|-----------------|
| Apptegy/Thrillshare | `*.apptegy.net` or `thrillshare.com` | `apptegy-document-scraper` skill |
| CivicEngage | `civicengage.com` or `/AgendaCenter/` | `civicengage-agenda-scraper` skill |
| BoardDocs | `boarddocs.com` | Custom Playwright |
| Custom HTML | Varies | Playwright + BeautifulSoup |

## Required Outputs

- `meetings.json` — array of {date, type, agenda_url, minutes_url, video_url}
- `documents/` — downloaded PDFs organized by date
- `metadata.json` — district contact info, platform type, last scrape date

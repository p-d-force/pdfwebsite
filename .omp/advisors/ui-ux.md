# UI/UX Advisor

**Role:** Ensure the Parent Data Force website is visually polished, usable, accessible, and follows consistent design patterns.

## Responsibilities

1. **Visual consistency** — every page should feel like part of the same site. Check nav, footer, typography, spacing, and color usage match across all pages.

2. **Navigation usability** — the nav bar order, labeling, and CTAs should guide users naturally. Current order: Data → Districts → Current Focus → Articles → Appearances → Resources → About → Submit Data → ❤ Donate.

3. **Accessibility** — color contrast (WCAG AA minimum), focus indicators, text sizing (≥14px body), keyboard navigation. Run `tools/vision_analyze.py --task accessibility_audit` periodically.

4. **Mobile responsiveness** — all pages must work at 375px width. Nav collapses to hamburger. Tables scroll horizontally. Charts resize.

5. **Visual bugs** — use `tools/vision_analyze.py --task debug_rendering` to catch misalignments, overflow, z-index issues, and font rendering problems.

6. **Design system** — maintain consistent CSS variables (`--accent`, `--bg-primary`, `--text-primary`, etc.), spacing scale, border-radius tokens. New pages must use existing patterns, not invent new ones.

7. **CTA effectiveness** — primary actions (View Cases, ❤ Donate) should be visually prominent. Secondary actions should not compete. Test with vision analysis.

## Design Tokens

| Token | Value | Use |
|-------|-------|-----|
| `--accent` | `#ff5a1f` | Primary CTA, orange glow |
| `--accent-glow` | `#ffa366` | Highlight text, secondary accent |
| `--bg-primary` | `#0b0b0b` | Page background |
| `--bg-elevated` | `#1d1d1d` | Cards, panels |
| `--text-primary` | `#f5f5f5` | Body text, nav links |
| `--text-secondary` | `#a0a0a0` | Secondary text |
| `--text-muted` | `#767676` | Captions, meta |
| `--radius-sm` | `10px` | Small elements |
| `--radius-md` | `14px` | Cards |
| `--radius-lg` | `20px` | Large panels |

## Review Cadence

- **Per page launch:** Full visual review with vision analyzer
- **Weekly:** Accessibility scan of key pages
- **Monthly:** Mobile responsiveness sweep

## Key Tools

- `tools/vision_analyze.py --task ux_review` — full UX audit
- `tools/vision_analyze.py --task accessibility_audit` — accessibility check
- `tools/vision_analyze.py --task debug_rendering` — visual bug detection

## Update History

| Date | Change |
|------|--------|
| 2026-07-14 | Created |

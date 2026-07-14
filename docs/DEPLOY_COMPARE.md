# Compare Tab Deployment Guide

## Files to Upload

### 1. `assets/js/charts-compare.js` — NEW FILE (standalone district comparison JS)
Upload to: `public_html/assets/js/charts-compare.js`

Does NOT overwrite any existing file. This is a self-contained IIFE that adds
`initDistrictCompare()`, `renderCompareChart()`, and `addDistrictToCompare()`.
It auto-initializes on DOMContentLoaded when the compare panel exists on the page.

### 2. `assets/css/styles.css` — Updated (compare panel styles)
Upload to: `public_html/assets/css/styles.css`

**IMPORTANT: Bump the cache-buster version number!**
After uploading, in `includes/head.php` or wherever the stylesheet is linked,
change `styles.css?v=1783948850` to a new value (e.g., `time()` or a new number):
```php
<link rel="stylesheet" href="/assets/css/styles.css?v=<?php echo time(); ?>">
```

New CSS classes added: `.compare-select-row`, `.compare-select`, `.compare-chart-container`,
`.similar-districts-panel`, `.similar-district-tag`, `.similar-district-select`, `.similar-district-add`.
Existing `.restraint-comparison-panel` and `.restraint-delta-*` classes are unchanged.

### 3. `data/compare-panel.php` — NEW FILE (PHP data + interactive panel)
Upload to: `public_html/data/compare-panel.php`

Uses `Database::fetchAll()` — the project's standard query wrapper, same pattern
as the existing production code. Queries restraint_data, enrollment_data,
discipline_data, and attendance_data for 2024-25.

### 4. Edit `data/index.php` — Include the compare panel

Insert this line at **line 348**, right after the opening `<div class="data-tab-content active" data-animate>` in the compare section:

```php
<?php include __DIR__ . '/compare-panel.php'; ?>
```

The existing production file looks like this at that point (line 346-354):
```php
<?php elseif ($activeTab === 'compare'): ?>
        <!-- ===== CROSS-DATASET COMPARISON ===== -->
        <div class="data-tab-content active" data-animate>
            <!-- INSERT HERE --><?php include __DIR__ . '/compare-panel.php'; ?>
            <div class="data-browser-intro">
                <h3>Cross-Dataset District Comparison (2024-25)</h3>
```

The panel renders ABOVE the existing Top 30 cross-dataset table. Both stay on the page.

### 5. Edit footer.php (or data/index.php) — Add charts-compare.js script

Add this script tag AFTER the existing `charts.js` script tag. For example, in
`includes/footer.php` or at the bottom of `data/index.php`:

```html
<script src="/assets/js/charts-compare.js?v=<?php echo filemtime(__DIR__ . '/../assets/js/charts-compare.js'); ?>"></script>
```

If you only want it on the compare page, wrap it in:
```php
<?php if (($activeTab ?? '') === 'compare'): ?>
<script src="/assets/js/charts-compare.js?v=<?php echo time(); ?>"></script>
<?php endif; ?>
```

## Files NOT Modified (No Action Needed)

- `assets/js/charts.js` — Unchanged. The existing restraint trends and homepage charts are untouched.
- `assets/js/main.js` — Unchanged.
- `api/data.php` — Unchanged.

## How It Works

1. Page loads → `compare-panel.php` queries 4 database tables, merges data, embeds as JSON
2. `charts-compare.js` reads the JSON, populates all 3 dropdown selectors
3. User selects District A + District B → grouped bar chart renders automatically
4. **Left Y-axis**: Count metrics (Total Restraints, Enrollment)
5. **Right Y-axis**: Percentage/Rate metrics (Rate/100, SPED%, Low Income%, EL%, OSS%, Attendance%, Chr Absent%)
6. **Similar Districts panel**: Add more districts inline — chart updates live. Remove with ×.

## Verification Checklist

After uploading all files:
- [ ] Visit `/data/?tab=compare` — page loads without errors
- [ ] Two district selectors show populated dropdowns
- [ ] Select District A + District B → chart renders
- [ ] Add a third district via "Similar Districts" → chart updates
- [ ] Remove a similar district via × → chart updates
- [ ] Browser console: zero JavaScript errors
- [ ] Existing tabs (Portal, Restraint Data, Statewide Trends, More Data) still work
- [ ] Existing Top 30 cross-dataset table still renders below the interactive panel

## Rollback

If something goes wrong:
1. Remove the `include` line from `data/index.php`
2. Restore original `styles.css` from `backups/prod-2026-07-13/ftp-assets_css_styles.css`
3. Remove `charts-compare.js` and `compare-panel.php`

The only production file that gets overwritten is `styles.css` — everything else is additive.

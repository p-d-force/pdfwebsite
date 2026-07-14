<?php declare(strict_types=1);
/**
 * Layout — the HTML shell that wraps every page.
 * Replaces the old head.php → header.php → content → footer.php chain.
 *
 * Expects these variables from View::render():
 *   $view              — path to the view template (set by View::render)
 *   $page_title        — page-specific title
 *   $page_description  — meta description
 *   $page_type         — og:type (default: website)
 *   $og_image          — og:image override
 *   $canonical_url     — canonical URL override
 *   $page_under_development — show dev banner
 */
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="<?= h($page_description ?? 'Parent Data Force — Data-driven advocacy for families navigating special education and public systems. Tracking complaints, records, outcomes, and public accountability.') ?>">
    <meta property="og:title" content="<?= h(($page_title ?? SITE_NAME) . ' | ' . SITE_TAGLINE) ?>">
    <meta property="og:description" content="<?= h($page_description ?? 'Data-driven advocacy for families navigating special education and public systems.') ?>">
    <meta property="og:type" content="<?= $page_type ?? 'website' ?>">
    <meta property="og:url" content="<?= h(($canonical_url ?? SITE_URL) . ($_SERVER['REQUEST_URI'] ?? '')) ?>">
    <meta property="og:image" content="<?= h($og_image ?? SITE_URL . '/assets/images/logo.png') ?>">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="canonical" href="<?= h(($canonical_url ?? SITE_URL) . ($_SERVER['REQUEST_URI'] ?? '')) ?>">
    <?php if (!empty($page_under_development)): ?>
    <meta name="robots" content="noindex, nofollow">
    <?php endif; ?>
    <title><?= h(($page_title ?? '') ? ($page_title . ' | ') : '') . SITE_NAME ?></title>
    <link rel="icon" type="image/png" href="<?= h(ASSETS_URL . '/images/logo.png') ?>">
    <link rel="stylesheet" href="<?= asset('css/app.css') ?>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
    <?php if (defined('SITE_UNDER_CONSTRUCTION') && SITE_UNDER_CONSTRUCTION): ?>
    <div class="construction-notice">
        &#x1f6a7; This site is under active development. Some features may be incomplete &mdash; check back as we expand.
    </div>
    <?php endif; ?>
    <?php if (!empty($page_under_development)): ?>
    <div class="construction-notice" style="background:rgba(239,68,68,0.08);border-bottom:1px solid rgba(239,68,68,0.25);color:var(--danger);">
        &#x1f6a7; This page is under development. Content may change or be incomplete.
    </div>
    <?php endif; ?>

    <?php (new App\Components\Nav())->render(); ?>

    <main>
        <?php require $view; ?>
    </main>

    <?php (new App\Components\Footer())->render(); ?>

    <script src="<?= asset('js/app.js') ?>"></script>
</body>
</html>

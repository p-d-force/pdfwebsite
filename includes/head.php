<?php declare(strict_types=1); ?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="<?php echo h($page_description ?? 'Parent Data Force - Data-driven advocacy for families navigating special education and public systems. Tracking complaints, records, outcomes, and public accountability.'); ?>">
    <meta property="og:title" content="<?php echo h(($page_title ?? SITE_NAME) . ' | ' . SITE_TAGLINE); ?>">
    <meta property="og:description" content="<?php echo h($page_description ?? 'Data-driven advocacy for families navigating special education and public systems.'); ?>">
    <meta property="og:type" content="<?php echo $page_type ?? 'website'; ?>">
    <meta property="og:url" content="<?php echo h(($canonical_url ?? SITE_URL) . ($_SERVER['REQUEST_URI'] ?? '')); ?>">
    <meta property="og:image" content="<?php echo h($og_image ?? SITE_URL . '/assets/images/logo.png'); ?>">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="canonical" href="<?php echo h(($canonical_url ?? SITE_URL) . ($_SERVER['REQUEST_URI'] ?? '')); ?>">
    <?php if (!empty($page_under_development)): ?>
    <meta name="robots" content="noindex, nofollow">
    <?php endif; ?>
    <title><?php echo h(($page_title ?? '') ? ($page_title . ' | ') : '') . SITE_NAME; ?></title>
    <link rel="icon" type="image/png" href="/assets/images/logo.png">
    <link rel="stylesheet" href="<?php echo asset('css/styles.css'); ?>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>

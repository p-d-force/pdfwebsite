<?php
declare(strict_types=1);
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/includes/Database.php';
require_once __DIR__ . '/includes/helpers.php';

header('Content-Type: application/xml; charset=utf-8');

$articles  = Database::fetchAll("SELECT slug, published_at FROM articles WHERE status = 'published' ORDER BY published_at DESC");
$cases     = Database::fetchAll("SELECT case_id, updated_at FROM cases WHERE status != 'archived' ORDER BY updated_at DESC");
$districts = Database::fetchAll("SELECT code, updated_at FROM districts WHERE status = 'active' ORDER BY code");
$speeches  = Database::fetchAll("SELECT id, published_at FROM speeches ORDER BY published_at DESC");

echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc><?php echo SITE_URL; ?>/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc><?php echo SITE_URL; ?>/articles/</loc>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc><?php echo SITE_URL; ?>/cases/</loc>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc><?php echo SITE_URL; ?>/districts/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc><?php echo SITE_URL; ?>/data/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc><?php echo SITE_URL; ?>/speeches/</loc>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
    <url>
        <loc><?php echo SITE_URL; ?>/updates/</loc>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc><?php echo SITE_URL; ?>/about/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>
    <url>
        <loc><?php echo SITE_URL; ?>/submit/</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    <?php foreach ($articles as $a): ?>
    <url>
        <loc><?php echo SITE_URL; ?>/articles/<?php echo h($a['slug']); ?></loc>
        <lastmod><?php echo date('c', strtotime($a['published_at'])); ?></lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <?php endforeach; ?>
    <?php foreach ($cases as $c): ?>
    <url>
        <loc><?php echo SITE_URL; ?>/cases/<?php echo h($c['case_id']); ?></loc>
        <lastmod><?php echo date('c', strtotime($c['updated_at'])); ?></lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
    <?php endforeach; ?>
    <?php foreach ($districts as $d): ?>
    <url>
        <loc><?php echo SITE_URL; ?>/districts/<?php echo h(strtolower($d['code'])); ?></loc>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>
    <?php endforeach; ?>
</urlset>

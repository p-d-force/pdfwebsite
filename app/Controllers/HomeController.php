<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;
use App\Core\Database;

class HomeController
{
    /** GET / — homepage */
    public function index(array $params = []): void
    {
        $featured = Database::fetchAll(
            "SELECT title, slug, excerpt, published_date, article_type
             FROM articles WHERE is_active = 1 AND is_featured = 1
             ORDER BY published_date DESC LIMIT 3"
        );

        $recentCases = Database::fetchAll(
            "SELECT title, case_number, slug, status, filed_date
             FROM cases WHERE is_active = 1
             ORDER BY filed_date DESC LIMIT 3"
        );

        $districtCount = Database::fetchColumn(
            "SELECT COUNT(*) FROM districts WHERE is_active = 1"
        );

        View::render('home', [
            'page_title' => 'Home',
            'featured' => $featured,
            'recentCases' => $recentCases,
            'districtCount' => $districtCount,
        ]);
    }

    /** GET /about */
    public function about(array $params = []): void
    {
        View::render('about', [
            'page_title' => 'About',
            'page_description' => 'Learn about Parent Data Force — independent special education and public accountability advocacy in Massachusetts.',
        ]);
    }

    /** GET /submit */
    public function submit(array $params = []): void
    {
        View::render('submit', [
            'page_title' => 'Submit a Tip',
            'page_description' => 'Share information about special education issues in Massachusetts schools.',
        ]);
    }

    /** GET /updates */
    public function updates(array $params = []): void
    {
        $updates = Database::fetchAll(
            "SELECT * FROM updates WHERE is_active = 1
             ORDER BY published_date DESC LIMIT 20"
        );
        View::render('updates', [
            'page_title' => 'Updates',
            'updates' => $updates,
        ]);
    }

    /** GET /appearances */
    public function appearances(array $params = []): void
    {
        $appearances = Database::fetchAll(
            "SELECT * FROM media_appearances ORDER BY appearance_date DESC"
        );
        View::render('appearances', [
            'page_title' => 'Media Appearances',
            'appearances' => $appearances,
        ]);
    }

    /** GET /rss */
    public function rss(array $params = []): void
    {
        $articles = Database::fetchAll(
            "SELECT title, slug, excerpt, published_date, article_type
             FROM articles WHERE is_active = 1
             ORDER BY published_date DESC LIMIT 20"
        );
        $cases = Database::fetchAll(
            "SELECT title, case_number, status, filed_date
             FROM cases WHERE is_active = 1
             ORDER BY filed_date DESC LIMIT 20"
        );

        header('Content-Type: application/rss+xml; charset=utf-8');
        echo '<?xml version="1.0" encoding="UTF-8"?>';
        ?>
        <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
        <channel>
            <title><?= SITE_NAME ?></title>
            <link><?= SITE_URL ?>/</link>
            <description>Data-driven advocacy for families navigating special education and public systems.</description>
            <language>en-us</language>
            <atom:link href="<?= SITE_URL ?>/rss" rel="self" type="application/rss+xml"/>
            <?php foreach ($articles as $a): ?>
            <item>
                <title><?= h($a['title']) ?></title>
                <link><?= SITE_URL ?>/articles/<?= h($a['slug']) ?></link>
                <description><?= h($a['excerpt'] ?? '') ?></description>
                <pubDate><?= date('r', strtotime($a['published_date'])) ?></pubDate>
                <guid isPermaLink="true"><?= SITE_URL ?>/articles/<?= h($a['slug']) ?></guid>
            </item>
            <?php endforeach; ?>
            <?php foreach ($cases as $c): ?>
            <item>
                <title><?= h($c['title']) ?> — <?= h($c['case_number']) ?></title>
                <link><?= SITE_URL ?>/cases/<?= h($c['case_number']) ?></link>
                <description>Case status: <?= h($c['status'] ?? 'Unknown') ?>. Filed: <?= h($c['filed_date'] ?? '') ?></description>
                <pubDate><?= date('r', strtotime($c['filed_date'] ?? 'now')) ?></pubDate>
                <guid isPermaLink="true"><?= SITE_URL ?>/cases/<?= h($c['case_number']) ?></guid>
            </item>
            <?php endforeach; ?>
        </channel>
        </rss>
        <?php
        exit;
    }

    /** GET /sitemap.xml */
    public function sitemap(array $params = []): void
    {
        $articles  = Database::fetchAll("SELECT slug, published_date FROM articles WHERE is_active = 1 ORDER BY published_date DESC");
        $cases     = Database::fetchAll("SELECT case_number, updated_at FROM cases WHERE is_active = 1 ORDER BY updated_at DESC");
        $districts = Database::fetchAll("SELECT district_code FROM districts WHERE is_active = 1 ORDER BY district_code");
        $appearances = Database::fetchAll("SELECT id, appearance_date FROM media_appearances ORDER BY appearance_date DESC");

        header('Content-Type: application/xml; charset=utf-8');
        echo '<?xml version="1.0" encoding="UTF-8"?>';
        ?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc><?= SITE_URL ?>/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>
            <url><loc><?= SITE_URL ?>/articles/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>
            <url><loc><?= SITE_URL ?>/cases/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>
            <url><loc><?= SITE_URL ?>/districts/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
            <url><loc><?= SITE_URL ?>/data/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
            <url><loc><?= SITE_URL ?>/appearances/</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>
            <url><loc><?= SITE_URL ?>/updates/</loc><changefreq>daily</changefreq><priority>0.8</priority></url>
            <url><loc><?= SITE_URL ?>/about/</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>
            <url><loc><?= SITE_URL ?>/submit/</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>
            <?php foreach ($articles as $a): ?>
            <url><loc><?= SITE_URL ?>/articles/<?= h($a['slug']) ?></loc><lastmod><?= date('c', strtotime($a['published_date'])) ?></lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
            <?php endforeach; ?>
            <?php foreach ($cases as $c): ?>
            <url><loc><?= SITE_URL ?>/cases/<?= h($c['case_number']) ?></loc><lastmod><?= date('c', strtotime($c['updated_at'])) ?></lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>
            <?php endforeach; ?>
            <?php foreach ($districts as $d): ?>
            <url><loc><?= SITE_URL ?>/districts/<?= h(strtolower($d['district_code'])) ?></loc><changefreq>monthly</changefreq><priority>0.6</priority></url>
            <?php endforeach; ?>
        </urlset>
        <?php
        exit;
    }
}

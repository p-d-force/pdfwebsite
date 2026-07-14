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
        header('Content-Type: application/rss+xml; charset=utf-8');
        echo '<?xml version="1.0" encoding="UTF-8"?>';
        // Minimal RSS stub — full implementation from existing rss.php
        echo '<rss version="2.0"><channel><title>Parent Data Force</title></channel></rss>';
        exit;
    }

    /** GET /sitemap.xml */
    public function sitemap(array $params = []): void
    {
        header('Content-Type: application/xml; charset=utf-8');
        echo '<?xml version="1.0" encoding="UTF-8"?>';
        // Minimal sitemap stub — full implementation from existing sitemap.php
        echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>';
        exit;
    }
}

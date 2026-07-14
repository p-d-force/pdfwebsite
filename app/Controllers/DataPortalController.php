<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;
use App\Core\Database;

class DataPortalController
{
    /** GET /data — data portal (restraint browser, trends) */
    public function index(array $params = []): void
    {
        View::render('data-portal', [
            'page_title' => 'Data Portal',
            'page_description' => 'Explore Massachusetts school district data — restraint and seclusion, enrollment, discipline, and attendance.',
        ]);
    }

    /** GET /compare — interactive district comparison */
    public function compare(array $params = []): void
    {
        View::render('compare', [
            'page_title' => 'District Comparison',
            'page_description' => 'Compare Massachusetts school districts side by side on restraint data, enrollment, and more.',
        ]);
    }
}

class SearchController
{
    /** GET /search */
    public function index(array $params = []): void
    {
        $query = $_GET['q'] ?? '';
        $results = [];
        if ($query) {
            $results = Database::fetchAll(
                "SELECT 'article' as type, title, slug, excerpt, published_date as date
                 FROM articles WHERE is_active = 1 AND (title LIKE ? OR body LIKE ?)
                 UNION ALL
                 SELECT 'case' as type, title, slug, summary as excerpt, filed_date as date
                 FROM cases WHERE is_active = 1 AND (title LIKE ? OR summary LIKE ?)
                 LIMIT 20",
                array_fill(0, 4, "%{$query}%")
            );
        }
        View::render('search', [
            'page_title' => 'Search',
            'query' => $query,
            'results' => $results,
        ]);
    }
}

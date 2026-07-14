<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;
use App\Core\Database;

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

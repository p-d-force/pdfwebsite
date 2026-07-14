<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;
use App\Core\Database;

class SearchController
{
    /** GET /search */
    public function index(array $params = []): void
    {
        $query = trim($_GET['q'] ?? '');
        $page = max(1, (int)($_GET['page'] ?? 1));
        $perPage = 20;
        $results = [];
        $total = 0;

        if ($query !== '') {
            $like = '%' . $query . '%';
            $articleResults = Database::fetchAll(
                "SELECT 'article' as type, title, slug, excerpt, published_date as date
                 FROM articles WHERE is_active = 1 AND (title LIKE ? OR excerpt LIKE ? OR body LIKE ?)
                 ORDER BY published_date DESC",
                [$like, $like, $like]
            );
            $caseResults = Database::fetchAll(
                "SELECT 'case' as type, title, slug, summary as excerpt, filed_date as date
                 FROM cases WHERE status != 'archived' AND (title LIKE ? OR summary LIKE ?)
                 ORDER BY filed_date DESC",
                [$like, $like]
            );
            $results = array_merge($articleResults, $caseResults);
            usort($results, function ($a, $b) {
                $ta = ($a['date'] ?? false) ? strtotime($a['date']) : false;
                $tb = ($b['date'] ?? false) ? strtotime($b['date']) : false;
                if ($ta === false && $tb === false) return 0;
                if ($ta === false) return 1;
                if ($tb === false) return -1;
                return $tb <=> $ta;
            });
            $total = count($results);
            $results = array_slice($results, ($page - 1) * $perPage, $perPage);
        }

        View::render('search', [
            'page_title' => 'Search' . ($query ? ' — "' . $query . '"' : ''),
            'query' => $query,
            'results' => $results,
            'total' => $total,
            'page' => $page,
            'perPage' => $perPage,
        ]);
    }
}

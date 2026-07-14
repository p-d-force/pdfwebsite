<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

$action = $_GET['action'] ?? 'list';
$slug   = $_GET['slug'] ?? '';

try {
    if ($action === 'single' && $slug) {
        $article = Database::fetch(
            "SELECT a.*, GROUP_CONCAT(DISTINCT d.code) as district_codes
             FROM articles a
             LEFT JOIN article_district_links adl ON a.id = adl.article_id
             LEFT JOIN districts d ON adl.district_id = d.id
             WHERE a.slug = ? AND a.status = ?
             GROUP BY a.id",
            [$slug, 'published']
        );

        if (!$article) {
            json_response(['error' => 'Article not found'], 404);
        }

        $related_cases = Database::fetchAll(
            'SELECT case_id, title, district_code, status FROM cases c
             JOIN article_case_links acl ON c.id = acl.case_id
             WHERE acl.article_id = ?',
            [$article['id']]
        );

        $article['related_cases'] = $related_cases;
        json_response(['article' => $article]);
    }

    if ($action === 'list') {
        $page     = max(1, (int)($_GET['page'] ?? 1));
        $category = $_GET['category'] ?? '';
        $search   = $_GET['search'] ?? '';
        $perPage  = ARTICLES_PER_PAGE;
        $offset   = ($page - 1) * $perPage;

        $where  = ['a.status = ?'];
        $params = ['published'];

        if ($category && $category !== 'all') {
            $where[]  = 'a.category = ?';
            $params[] = $category;
        }
        if ($search) {
            $where[]  = '(a.title LIKE ? OR a.excerpt LIKE ?)';
            $st = '%' . $search . '%';
            $params[] = $st;
            $params[] = $st;
        }

        $whereClause = implode(' AND ', $where);
        $total       = (int)Database::fetchColumn("SELECT COUNT(*) FROM articles a WHERE {$whereClause}", $params);
        $articles    = Database::fetchAll(
            "SELECT id, title, slug, excerpt, category, featured_image, published_at, read_time
             FROM articles a
             WHERE {$whereClause}
             ORDER BY published_at DESC
             LIMIT ? OFFSET ?",
            array_merge($params, [$perPage, $offset])
        );

        json_response([
            'articles'    => $articles,
            'total'       => $total,
            'page'        => $page,
            'total_pages' => (int)ceil($total / $perPage),
        ]);
    }

    if ($action === 'categories') {
        $categories = Database::fetchAll(
            "SELECT category, COUNT(*) as total FROM articles WHERE status = 'published' GROUP BY category ORDER BY category"
        );
        json_response(['categories' => $categories]);
    }

    json_response(['error' => 'Unknown action'], 400);
} catch (Exception $e) {
    json_response(['error' => APP_DEBUG ? $e->getMessage() : 'Internal server error'], 500);
}

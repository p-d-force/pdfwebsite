<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

$query = trim($_GET['q'] ?? '');

if (mb_strlen($query) < 2) {
    json_response(['results' => [], 'total' => 0]);
}

try {
    $results = [];
    $search  = '%' . $query . '%';

    $articles = Database::fetchAll(
        "SELECT id, title, slug, excerpt, category, published_at, 'article' as result_type
         FROM articles
         WHERE status = 'published' AND (title LIKE ? OR excerpt LIKE ? OR body LIKE ?)
         ORDER BY published_at DESC
         LIMIT 8",
        [$search, $search, $search]
    );
    foreach ($articles as $r) {
        $results[] = $r;
    }

    $cases = Database::fetchAll(
        "SELECT id, case_id, title, summary as excerpt, type as category, filed_date as published_at, status, 'case' as result_type
         FROM cases
         WHERE status != 'archived' AND (title LIKE ? OR summary LIKE ? OR case_id LIKE ?)
         ORDER BY filed_date DESC
         LIMIT 8",
        [$search, $search, $search]
    );
    foreach ($cases as $r) {
        $r['slug'] = $r['case_id'];
        $results[] = $r;
    }

    $speeches = Database::fetchAll(
        "SELECT id, title, description as excerpt, category, published_at, video_id, url, 'speech' as result_type
         FROM speeches
         WHERE title LIKE ? OR description LIKE ?
         ORDER BY published_at DESC
         LIMIT 5",
        [$search, $search]
    );
    foreach ($speeches as $r) {
        $results[] = $r;
    }

    json_response([
        'query'   => $query,
        'results' => $results,
        'total'   => count($results),
    ]);
} catch (Exception $e) {
    json_response(['error' => APP_DEBUG ? $e->getMessage() : 'Internal server error'], 500);
}

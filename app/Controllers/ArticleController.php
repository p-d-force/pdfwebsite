<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;
use App\Core\Database;

class ArticleController
{
    public function list(array $params = []): void
    {
        $articles = Database::fetchAll(
            "SELECT * FROM articles WHERE is_active = 1 ORDER BY published_date DESC"
        );
        View::render('article-list', [
            'page_title' => 'Articles & Analysis',
            'articles' => $articles,
        ]);
    }

    public function show(array $params = []): void
    {
        $slug = $params['slug'] ?? '';
        $article = Database::fetch(
            "SELECT * FROM articles WHERE slug = ? AND is_active = 1", [$slug]
        );
        if (!$article) {
            http_response_code(404);
            View::render('errors/404', ['page_title' => 'Article Not Found']);
            return;
        }
        View::render('article', [
            'page_title' => $article['title'],
            'article' => $article,
        ]);
    }
}

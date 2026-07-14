<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;
use App\Core\Database;

class CaseController
{
    public function list(array $params = []): void
    {
        $cases = Database::fetchAll(
            "SELECT * FROM cases WHERE is_active = 1 ORDER BY filed_date DESC"
        );
        View::render('case-list', [
            'page_title' => 'Cases & Investigations',
            'cases' => $cases,
        ]);
    }

    public function show(array $params = []): void
    {
        $slug = $params['slug'] ?? '';
        $case = Database::fetch(
            "SELECT * FROM cases WHERE slug = ? OR case_number = ?",
            [$slug, $slug]
        );
        if (!$case) {
            http_response_code(404);
            View::render('errors/404', ['page_title' => 'Case Not Found']);
            return;
        }
        View::render('case', [
            'page_title' => $case['title'],
            'case' => $case,
        ]);
    }
}

<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;

class ErrorController
{
    public function show401(array $params = []): void
    {
        http_response_code(401);
        View::render('errors/401', ['page_title' => 'Unauthorized']);
    }

    public function show403(array $params = []): void
    {
        http_response_code(403);
        View::render('errors/403', ['page_title' => 'Forbidden']);
    }

    public function show404(array $params = []): void
    {
        http_response_code(404);
        View::render('errors/404', ['page_title' => 'Page Not Found']);
    }

    public function show500(array $params = []): void
    {
        http_response_code(500);
        View::render('errors/500', ['page_title' => 'Server Error']);
    }
}

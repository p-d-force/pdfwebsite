<?php declare(strict_types=1);
namespace App\Core;

class View
{
    /**
     * Render a template wrapped in the layout.
     *
     * @param string $template  Template name relative to app/views/ (without .php)
     * @param array  $data      Variables extracted into template scope
     */
    public static function render(string $template, array $data = []): void
    {
        extract($data);

        $viewPath = __DIR__ . '/../views/' . $template . '.php';
        if (!file_exists($viewPath)) {
            throw new \RuntimeException("View not found: {$template}");
        }

        // Layout wraps the view — $view is used by Layout.php
        $layout = __DIR__ . '/../Components/Layout.php';
        require $layout;
    }
}

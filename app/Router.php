<?php declare(strict_types=1);
namespace App;

class Router
{
    public function dispatch(string $method, string $uri): void
    {
        $uri = rtrim($uri, '/') ?: '/';
        $routes = require __DIR__ . '/config/routes.php';

        foreach ($routes as $pattern => $handler) {
            $regex = '#^' . preg_replace('/\{(\w+)\}/', '(?P<$1>[^/]+)', $pattern) . '$#';
            if (preg_match($regex, $uri, $matches)) {
                [$class, $action] = $handler;
                $controller = new $class();
                $params = array_filter($matches, 'is_string', ARRAY_FILTER_USE_KEY);
                $controller->$action($params);
                return;
            }
        }

        http_response_code(404);
        if (class_exists('App\\Controllers\\ErrorController')) {
            (new \App\Controllers\ErrorController())->show404();
        } else {
            require __DIR__ . '/views/errors/404.php';
        }
    }
}

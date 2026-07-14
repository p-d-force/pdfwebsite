<?php declare(strict_types=1);
/**
 * Application bootstrap — included once by public/index.php.
 * Sets up autoloading, configuration, database connection, and helper functions.
 */

// ── PSR-4 Autoloader: App\ namespace → app/ directory ──
spl_autoload_register(function (string $class): void {
    $prefix = 'App\\';
    if (!str_starts_with($class, $prefix)) {
        return;
    }
    $relative = substr($class, strlen($prefix));
    $file = __DIR__ . '/' . str_replace('\\', '/', $relative) . '.php';
    if (file_exists($file)) {
        require_once $file;
    }
});

// ── Configuration ──
require_once __DIR__ . '/config/app.php';

// ── Core infrastructure ──
require_once __DIR__ . '/Core/Database.php';
require_once __DIR__ . '/Core/helpers.php';

// ── Start session (if not CLI) ──
if (PHP_SAPI !== 'cli') {
    if (session_status() === PHP_SESSION_NONE) {
        ini_set('session.cookie_httponly', '1');
        ini_set('session.cookie_secure', defined('APP_ENV') && APP_ENV === 'production' ? '1' : '0');
        ini_set('session.cookie_samesite', 'Lax');
        ini_set('session.use_strict_mode', '1');
        session_start();
    }

    // Generate CSRF token once per session
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
}

// ── Timezone ──
if (defined('TIMEZONE')) {
    date_default_timezone_set(TIMEZONE);
}

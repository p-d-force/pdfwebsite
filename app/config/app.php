<?php declare(strict_types=1);
/**
 * Application configuration — ported from config.php.
 * Defines all constants: DB, site, environment.
 */

// ── Environment detection ──
$is_production = (isset($_SERVER['HTTP_HOST']) && str_contains($_SERVER['HTTP_HOST'], 'parentdataforce.com'));

// ── Database ──
define('DB_HOST', 'localhost');
define('DB_PORT', (int)(getenv('DB_PORT') ?: 3306));
define('DB_NAME', $is_production ? 'g5wwzsi5v4lbdt1q_pdf_db' : 'pdf_db');
define('DB_USER', $is_production ? 'g5wwzsi5v4lbdt1q_pdf_user' : 'pdf_user');
define('DB_PASSWORD', getenv('DB_PASSWORD') ?: ($is_production ? '' : 'dev_password'));

// ── Application ──
define('APP_ENV', $is_production ? 'production' : 'development');
define('APP_DEBUG', !$is_production);
define('APP_SECRET', getenv('APP_SECRET') ?: 'change_this_to_a_random_string_at_least_32_chars_long');
define('SITE_URL', $is_production ? 'https://www.parentdataforce.com' : 'http://localhost:8081');
define('SITE_NAME', 'Parent Data Force');
define('SITE_TAGLINE', 'MAKING DATA MAKE SENSE');
define('TIMEZONE', 'America/New_York');
define('SITE_EMAIL', 'admin@parentdataforce.com');

// ── Construction / Development mode ──
$under_construction = getenv('SITE_UNDER_CONSTRUCTION');
if ($under_construction !== false) {
    define('SITE_UNDER_CONSTRUCTION', filter_var($under_construction, FILTER_VALIDATE_BOOLEAN));
} elseif ($is_production) {
    define('SITE_UNDER_CONSTRUCTION', false);
} else {
    define('SITE_UNDER_CONSTRUCTION', false);
}

// ── Pagination ──
define('DEFAULT_PER_PAGE', 25);
define('MAX_PER_PAGE', 100);

// ── Paths ──
define('ROOT_DIR', dirname(__DIR__, 2));
define('APP_DIR', __DIR__ . '/..');
define('PUBLIC_DIR', ROOT_DIR . '/public');
define('ASSETS_DIR', PUBLIC_DIR . '/assets');
define('ASSETS_URL', '/assets');

<?php







declare(strict_types=1);















// Parent Data Force v2 Configuration















// Environment detection







$is_production = (isset($_SERVER['HTTP_HOST']) && str_contains($_SERVER['HTTP_HOST'], 'parentdataforce.com'));















// Database configuration







define('DB_HOST', 'localhost');







define('DB_PORT', (int)(getenv('DB_PORT') ?: 3306));







define('DB_NAME', $is_production ? 'g5wwzsi5v4lbdt1q_pdf_db' : 'pdf_db');







define('DB_USER', $is_production ? 'g5wwzsi5v4lbdt1q_pdf_user' : 'pdf_user');







define('DB_PASSWORD', $is_production ? 'jJUBFSZK1!' : 'dev_password');















// Application







define('APP_ENV', $is_production ? 'production' : 'development');







define('APP_DEBUG', !$is_production);







define('APP_SECRET', getenv('APP_SECRET') ?: 'change_this_to_a_random_string_at_least_32_chars_long');







define('SITE_URL', $is_production ? 'https://www.parentdataforce.com' : 'http://localhost');







define('SITE_NAME', 'Parent Data Force');







define('SITE_TAGLINE', 'MAKING DATA MAKE SENSE');







define('TIMEZONE', 'America/New_York');







define('SITE_EMAIL', 'admin@parentdataforce.com');















// Construction / Development mode







// Set SITE_UNDER_CONSTRUCTION=true to show banner on every page







// Set to false and the banner completely disappears from source







define('SITE_UNDER_CONSTRUCTION', false); // Set to true to show construction banner















// Paths







define('ROOT_DIR', dirname(__FILE__));







define('ADMIN_DIR', ROOT_DIR . '/admin');







define('UPLOADS_DIR', ROOT_DIR . '/uploads');







define('ARCHIVE_DIR', ROOT_DIR . '/archive');







define('ASSETS_URL', SITE_URL . '/assets');















// Session







define('SESSION_LIFETIME', 86400); // 24 hours







define('SESSION_NAME', 'pdf_session');















// Pagination







define('ARTICLES_PER_PAGE', 12);







define('CASES_PER_PAGE', 20);







define('UPDATES_PER_PAGE', 25);















// File uploads







define('MAX_UPLOAD_SIZE', 256 * 1024 * 1024); // 256MB







define('ALLOWED_UPLOAD_TYPES', ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt', 'eml', 'mp3', 'mp4', 'png', 'jpg', 'jpeg', 'gif']);







define('MAX_UPLOAD_FILES', 10);















// Error reporting







if (APP_DEBUG) {







    error_reporting(E_ALL);







    ini_set('display_errors', '1');







} else {







    error_reporting(0);







    ini_set('display_errors', '0');







}















date_default_timezone_set(TIMEZONE);















if (!defined('PHPUNIT_TEST')) {







    ini_set('session.name', SESSION_NAME);







    ini_set('session.cookie_httponly', '1');







    ini_set('session.cookie_secure', $is_production ? '1' : '0');







    ini_set('session.cookie_samesite', 'Strict');







    ini_set('session.gc_maxlifetime', (string)SESSION_LIFETIME);















    if (session_status() === PHP_SESSION_NONE) {







        session_start();







    }















    if (!isset($_SESSION['csrf_token'])) {







        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));







    }







}












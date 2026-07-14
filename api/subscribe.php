<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('Method not allowed.');
}

if (!verify_csrf()) {
    http_response_code(403);
    exit('Invalid request.');
}

$email = trim($_POST['email'] ?? '');

if (empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    if (str_starts_with(($_SERVER['HTTP_ACCEPT'] ?? ''), 'application/json')) {
        json_response(['error' => 'Valid email required.'], 400);
    }
    redirect('/?subscribe_error=invalid');
}

try {
    Database::insert(
        'INSERT INTO submissions (submission_type, contact_email, message, ip_address, status) VALUES (?, ?, ?, ?, ?)',
        ['subscribe', $email, 'Newsletter subscription', $_SERVER['REMOTE_ADDR'] ?? '', 'new']
    );

    if (str_starts_with(($_SERVER['HTTP_ACCEPT'] ?? ''), 'application/json')) {
        json_response(['success' => true, 'message' => 'Subscribed successfully.']);
    }
    redirect('/?subscribed=1');
} catch (Exception $e) {
    if (APP_DEBUG) {
        json_response(['error' => $e->getMessage()], 500);
    }
    redirect('/?subscribe_error=1');
}

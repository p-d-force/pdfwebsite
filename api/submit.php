<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'Method not allowed'], 405);
}

if (!verify_csrf()) {
    json_response(['error' => 'Invalid security token. Please refresh the page and try again.'], 403);
}

$type    = $_POST['submission_type'] ?? '';
$message = trim($_POST['message'] ?? '');

if (!in_array($type, ['tip', 'help', 'upload'])) {
    json_response(['error' => 'Invalid submission type.'], 400);
}

if (empty($message)) {
    json_response(['error' => 'Message is required.'], 400);
}

$district      = $_POST['district'] ?? '';
$contactEmail  = trim($_POST['contact_email'] ?? '');
$contactName   = trim($_POST['contact_name'] ?? '');
$concernType   = $_POST['concern_type'] ?? '';

if ($contactEmail && !filter_var($contactEmail, FILTER_VALIDATE_EMAIL)) {
    json_response(['error' => 'Invalid email address.'], 400);
}

$filePath         = null;
$originalFilename = null;
$errors           = [];

if (!empty($_FILES['files']['name'][0])) {
    $uploadDir = UPLOADS_DIR . '/submissions/' . date('Y-m-d');
    if (!is_dir($uploadDir)) {
        mkdir($uploadDir, 0755, true);
    }

    $fileCount = count($_FILES['files']['name']);
    if ($fileCount > MAX_UPLOAD_FILES) {
        $errors[] = 'Too many files. Maximum is ' . MAX_UPLOAD_FILES . '.';
    }

    if (empty($errors)) {
        for ($i = 0; $i < $fileCount; $i++) {
            $tmpName  = $_FILES['files']['tmp_name'][$i];
            $origName = basename($_FILES['files']['name'][$i]);
            $fileSize = $_FILES['files']['size'][$i];
            $fileExt  = strtolower(pathinfo($origName, PATHINFO_EXTENSION));

            if ($_FILES['files']['error'][$i] !== UPLOAD_ERR_OK) {
                $errors[] = "Upload error for {$origName}.";
                continue;
            }

            if ($fileSize > MAX_UPLOAD_SIZE) {
                $errors[] = "{$origName} exceeds maximum file size (256MB).";
                continue;
            }

            if ($fileExt && !in_array($fileExt, ALLOWED_UPLOAD_TYPES)) {
                $errors[] = "{$origName} has an unsupported file type.";
                continue;
            }

            $safeName = date('Ymd_His') . '_' . slugify(pathinfo($origName, PATHINFO_FILENAME)) . '.' . $fileExt;
            $dest     = $uploadDir . '/' . $safeName;

            if (!move_uploaded_file($tmpName, $dest)) {
                $errors[] = "Failed to save {$origName}.";
                continue;
            }

            if ($i === 0) {
                $filePath         = str_replace(ROOT_DIR, '', $dest);
                $originalFilename = $origName;
            }
        }
    }
}

if (!empty($errors) && empty($message)) {
    json_response(['error' => implode(' ', $errors)], 400);
}

try {
    $id = Database::insert(
        'INSERT INTO submissions (submission_type, district, message, contact_email, contact_name, file_path, original_filename, ip_address)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [$type, $district, $message, $contactEmail, $contactName, $filePath, $originalFilename, $_SERVER['REMOTE_ADDR'] ?? '']
    );

    $errorNote = !empty($errors) ? ' Note: Some files had issues: ' . implode(' ', $errors) : '';

    json_response([
        'success'  => true,
        'id'       => $id,
        'message'  => 'Your submission has been received and will be reviewed.' . $errorNote,
    ]);
} catch (Exception $e) {
    json_response(['error' => APP_DEBUG ? $e->getMessage() : 'Submission failed. Please try again.'], 500);
}

<?php
declare(strict_types=1);

function slugify(string $text): string
{
    $text = preg_replace('~[^\pL\d]+~u', '-', $text);
    $text = iconv('utf-8', 'us-ascii//TRANSLIT', $text);
    $text = preg_replace('~[^-\w]+~', '', $text);
    $text = trim($text, '-');
    $text = preg_replace('~-+~', '-', $text);
    $text = strtolower($text);
    return $text ?: 'untitled';
}

function h(string $text): string
{
    return htmlspecialchars($text, ENT_QUOTES | ENT_HTML5, 'UTF-8');
}

function sanitize(string $text): string
{
    return strip_tags($text, '<h1><h2><h3><h4><h5><h6><p><a><strong><em><b><i><u><ul><ol><li><br><blockquote><pre><code><span><div><img><figure><figcaption><table><thead><tbody><tr><th><td><hr><sup><sub><iframe><video><audio><source>');
}

function format_date(?string $date, string $format = 'M j, Y'): string
{
    if (!$date) return '';
    $timestamp = strtotime($date);
    return $timestamp ? date($format, $timestamp) : $date;
}

function format_datetime(?string $datetime, string $format = 'M j, Y g:i A'): string
{
    return format_date($datetime, $format);
}

function relative_date(?string $date): string
{
    if (!$date) return '';
    $now = new DateTime();
    $then = new DateTime($date);
    $diff = $now->diff($then);

    if ($diff->days === 0) return 'Today';
    if ($diff->days === 1) {
        return $diff->invert ? 'Yesterday' : 'Tomorrow';
    }
    if ($diff->days < 7) {
        return $diff->invert ? $diff->days . ' days ago' : 'In ' . $diff->days . ' days';
    }
    if ($diff->days < 30) {
        $weeks = floor($diff->days / 7);
        return $diff->invert ? $weeks . ' week' . ($weeks > 1 ? 's' : '') . ' ago' : 'In ' . $weeks . ' week' . ($weeks > 1 ? 's' : '');
    }
    if ($diff->days < 365) {
        $months = floor($diff->days / 30);
        return $diff->invert ? $months . ' month' . ($months > 1 ? 's' : '') . ' ago' : 'In ' . $months . ' month' . ($months > 1 ? 's' : '');
    }
    $years = floor($diff->days / 365);
    return $diff->invert ? $years . ' year' . ($years > 1 ? 's' : '') . ' ago' : 'In ' . $years . ' year' . ($years > 1 ? 's' : '');
}

function truncate(string $text, int $length = 200, string $suffix = '...'): string
{
    $text = strip_tags($text);
    if (mb_strlen($text) <= $length) return $text;
    return mb_substr($text, 0, $length) . $suffix;
}

function excerpt(string $text, int $length = 300): string
{
    return truncate($text, $length);
}

function read_time(string $text): int
{
    $wordCount = str_word_count(strip_tags($text));
    return (int)ceil($wordCount / 200) ?: 1;
}

function status_badge(string $status): string
{
    $colors = [
        'open'       => 'status-open',
        'closed'     => 'status-closed',
        'pending'    => 'status-pending',
        'resolved'   => 'status-resolved',
        'overdue'    => 'status-overdue',
        'new'        => 'status-pending',
        'reviewing'  => 'status-open',
        'accepted'   => 'status-resolved',
        'rejected'   => 'status-closed',
        'archived'   => 'status-closed',
        'active'     => 'status-open',
        'inactive'   => 'status-closed',
        'draft'      => 'status-pending',
        'published'  => 'status-open',
    ];

    $class = $colors[$status] ?? 'status-pending';
    $label = ucfirst(str_replace('_', ' ', $status));

    return '<span class="status-badge ' . $class . '">' . h($label) . '</span>';
}

function severity_badge(string $severity): string
{
    $colors = [
        'high'   => 'status-closed',
        'medium' => 'status-pending',
        'low'    => 'status-open',
    ];

    $class = $colors[$severity] ?? 'status-pending';
    return '<span class="status-badge ' . $class . '">' . h(ucfirst($severity)) . '</span>';
}

function category_label(string $category): string
{
    $labels = [
        'case_update'     => 'Case Update',
        'methodology'     => 'Methodology',
        'data_analysis'   => 'Data Analysis',
        'policy'          => 'Policy',
        'news'            => 'News',
        'investigation'   => 'Investigation',
        'guide'           => 'Guide',
        'other'           => 'Other',
    ];

    return h($labels[$category] ?? ucfirst(str_replace('_', ' ', $category)));
}

function case_type_label(string $type): string
{
    $labels = [
        'public_records' => 'Public Records Request',
        'complaint'      => 'Complaint',
        'finding'        => 'Finding',
        'determination'  => 'Determination',
        'appeal'         => 'Appeal',
        'investigation'  => 'Investigation',
        'other'          => 'Other',
    ];

    return h($labels[$type] ?? ucfirst(str_replace('_', ' ', $type)));
}

function csrf_token(): string
{
    if (!isset($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf_token" value="' . csrf_token() . '">';
}

function verify_csrf(): bool
{
    if (empty($_POST['csrf_token']) || empty($_SESSION['csrf_token'])) {
        return false;
    }
    return hash_equals($_SESSION['csrf_token'], $_POST['csrf_token']);
}

function redirect(string $url, int $code = 302): never
{
    header('Location: ' . $url, true, $code);
    exit;
}

function asset(string $path): string
{
    $url = ASSETS_URL . '/' . ltrim($path, '/');
    $local = ROOT_DIR . '/assets/' . ltrim($path, '/');
    if (is_file($local)) {
        $url .= '?v=' . filemtime($local);
    }
    return $url;
}

function json_response(mixed $data, int $code = 200): never
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function generate_password_hash(string $password): string
{
    return password_hash($password, PASSWORD_BCRYPT, ['cost' => 10]);
}

function verify_password(string $password, string $hash): bool
{
    return password_verify($password, $hash);
}

function resize_image(string $source, string $destination, int $maxWidth = 1200, int $maxHeight = 1200, int $quality = 85): bool
{
    $info = getimagesize($source);
    if (!$info) return false;

    $width  = $info[0];
    $height = $info[1];
    $type   = $info[2];

    if ($width <= $maxWidth && $height <= $maxHeight) {
        return copy($source, $destination);
    }

    $ratio = min($maxWidth / $width, $maxHeight / $height);
    $newWidth  = (int)($width * $ratio);
    $newHeight = (int)($height * $ratio);

    $newImage = imagecreatetruecolor($newWidth, $newHeight);

    switch ($type) {
        case IMAGETYPE_JPEG:
            $sourceImage = imagecreatefromjpeg($source);
            imagecopyresampled($newImage, $sourceImage, 0, 0, 0, 0, $newWidth, $newHeight, $width, $height);
            $result = imagejpeg($newImage, $destination, $quality);
            break;
        case IMAGETYPE_PNG:
            imagealphablending($newImage, false);
            imagesavealpha($newImage, true);
            $sourceImage = imagecreatefrompng($source);
            imagecopyresampled($newImage, $sourceImage, 0, 0, 0, 0, $newWidth, $newHeight, $width, $height);
            $result = imagepng($newImage, $destination, (int)($quality / 10));
            break;
        case IMAGETYPE_GIF:
            $sourceImage = imagecreatefromgif($source);
            imagecopyresampled($newImage, $sourceImage, 0, 0, 0, 0, $newWidth, $newHeight, $width, $height);
            $result = imagegif($newImage, $destination);
            break;
        default:
            $result = false;
    }

    if (isset($sourceImage)) imagedestroy($sourceImage);
    imagedestroy($newImage);

    return $result;
}

<?php
declare(strict_types=1);

class Auth
{
    public static function start(): void
    {
        if (session_status() === PHP_SESSION_NONE) {
            session_name(SESSION_NAME);
            session_set_cookie_params([
                'lifetime' => SESSION_LIFETIME,
                'path'     => '/',
                'domain'   => '',
                'secure'   => APP_ENV === 'production',
                'httponly' => true,
                'samesite' => 'Strict',
            ]);
            session_start();
        }

        if (session_status() === PHP_SESSION_ACTIVE) {
            if (!isset($_SESSION['csrf_token'])) {
                $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
            }
        }
    }

    public static function login(string $username, string $password): array
    {
        $user = Database::fetch(
            'SELECT id, username, password_hash, display_name, role, status FROM admin_users WHERE username = ?',
            [$username]
        );

        if (!$user) {
            return ['success' => false, 'error' => 'Invalid username or password.'];
        }

        if (isset($user['status']) && $user['status'] !== 'active') {
            return ['success' => false, 'error' => 'Invalid username or password.'];
        }

        if (!verify_password($password, $user['password_hash'])) {
            return ['success' => false, 'error' => 'Invalid username or password.'];
        }

        $_SESSION['user_id']  = $user['id'];
        $_SESSION['username'] = $user['username'];
        $_SESSION['role']     = $user['role'];

        Database::execute(
            'UPDATE admin_users SET last_login_at = NOW(), login_count = login_count + 1 WHERE id = ?',
            [$user['id']]
        );

        static::log($user['id'], 'login', 'admin_users', $user['id'], ['ip' => $_SERVER['REMOTE_ADDR'] ?? '']);

        return [
            'success'      => true,
            'user_id'      => $user['id'],
            'username'     => $user['username'],
            'display_name' => $user['display_name'],
            'role'         => $user['role'],
        ];
    }

    public static function logout(): void
    {
        if (isset($_SESSION['user_id'])) {
            static::log($_SESSION['user_id'], 'logout', 'admin_users', $_SESSION['user_id']);
        }

        $_SESSION = [];
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_destroy();
        }

        if (ini_get('session.use_cookies')) {
            $params = session_get_cookie_params();
            setcookie(session_name(), '', [
                'expires'  => time() - 42000,
                'path'     => $params['path'],
                'domain'   => $params['domain'],
                'secure'   => $params['secure'],
                'httponly' => $params['httponly'],
                'samesite' => $params['samesite'] ?? 'Strict',
            ]);
        }
    }

    public static function check(): bool
    {
        return !empty($_SESSION['user_id']);
    }

    public static function require(): void
    {
        if (!static::check()) {
            $_SESSION['redirect_after_login'] = $_SERVER['REQUEST_URI'];
            redirect('/admin/login.php');
        }
    }

    public static function requireRole(string ...$roles): void
    {
        static::require();
        if (!in_array($_SESSION['role'] ?? '', $roles)) {
            http_response_code(403);
            die('Access denied. Insufficient permissions.');
        }
    }

    public static function userId(): ?int
    {
        return $_SESSION['user_id'] ?? null;
    }

    public static function username(): ?string
    {
        return $_SESSION['username'] ?? null;
    }

    public static function role(): ?string
    {
        return $_SESSION['role'] ?? null;
    }

    public static function updatePassword(int $userId, string $newPassword): bool
    {
        $hash = generate_password_hash($newPassword);
        return Database::execute(
            'UPDATE admin_users SET password_hash = ? WHERE id = ?',
            [$hash, $userId]
        ) > 0;
    }

    public static function log(int $userId, string $action, string $entityType = '', ?int $entityId = null, array $details = []): void
    {
        Database::insert(
            'INSERT INTO audit_log (user_id, action, entity_type, entity_id, details, ip_address) VALUES (?, ?, ?, ?, ?, ?)',
            [
                $userId,
                $action,
                $entityType,
                $entityId,
                json_encode($details, JSON_UNESCAPED_UNICODE),
                $_SERVER['REMOTE_ADDR'] ?? '',
            ]
        );
    }

    public static function getAuditLog(int $limit = 50): array
    {
        return Database::fetchAll(
            'SELECT al.*, au.username
             FROM audit_log al
             LEFT JOIN admin_users au ON al.user_id = au.id
             ORDER BY al.created_at DESC
             LIMIT ?',
            [$limit]
        );
    }
}

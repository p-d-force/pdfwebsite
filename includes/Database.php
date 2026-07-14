<?php
declare(strict_types=1);

class Database
{
    private static ?PDO $instance = null;
    private static array $queryLog = [];
    private static int $queryCount = 0;

    public static function getInstance(): PDO
    {
        if (self::$instance === null) {
            $dsn = sprintf(
                'mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4',
                DB_HOST,
                DB_PORT,
                DB_NAME
            );

            $options = [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES   => false,
                PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
                PDO::ATTR_STRINGIFY_FETCHES  => false,
            ];

            try {
                self::$instance = new PDO($dsn, DB_USER, DB_PASSWORD, $options);
            } catch (PDOException $e) {
                error_log('Database connection failed: ' . $e->getMessage());
                if (APP_DEBUG) {
                    throw new RuntimeException('Database connection failed: ' . $e->getMessage());
                }
                http_response_code(500);
                die('Service temporarily unavailable. Please try again later.');
            }
        }

        return self::$instance;
    }

    public static function query(string $sql, array $params = []): PDOStatement
    {
        $db = self::getInstance();
        $stmt = $db->prepare($sql);
        $stmt->execute($params);

        self::$queryCount++;
        if (APP_DEBUG) {
            self::$queryLog[] = [
                'sql'    => $sql,
                'params' => $params,
                'time'   => microtime(true),
            ];
        }

        return $stmt;
    }

    public static function fetch(string $sql, array $params = []): ?array
    {
        $result = self::query($sql, $params)->fetch();
        return $result ?: null;
    }

    public static function fetchAll(string $sql, array $params = []): array
    {
        return self::query($sql, $params)->fetchAll();
    }

    public static function fetchColumn(string $sql, array $params = [], int $column = 0): mixed
    {
        $result = self::query($sql, $params)->fetchColumn($column);
        return $result !== false ? $result : null;
    }

    public static function insert(string $sql, array $params = []): string
    {
        self::query($sql, $params);
        return self::getInstance()->lastInsertId();
    }

    public static function execute(string $sql, array $params = []): int
    {
        $stmt = self::query($sql, $params);
        return $stmt->rowCount();
    }

    public static function beginTransaction(): void
    {
        self::getInstance()->beginTransaction();
    }

    public static function commit(): void
    {
        self::getInstance()->commit();
    }

    public static function rollback(): void
    {
        if (self::getInstance()->inTransaction()) {
            self::getInstance()->rollBack();
        }
    }

    public static function getQueryCount(): int
    {
        return self::$queryCount;
    }

    public static function getQueryLog(): array
    {
        return self::$queryLog;
    }
}

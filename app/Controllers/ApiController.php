<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\Database;

class ApiController
{
    /** GET /api/data */
    public function data(array $params = []): void
    {
        $type = $_GET['type'] ?? 'districts';
        $code = $_GET['district_code'] ?? '';
        $year = $_GET['school_year'] ?? '2024-25';

        if ($type === 'districts') {
            $rows = Database::fetchAll(
                "SELECT district_name, district_code, county, grade_span, total_students
                 FROM districts WHERE is_active = 1 ORDER BY district_name"
            );
            json_response(['data' => $rows]);
        }

        if ($type === 'restraint' && $code) {
            $rows = Database::fetchAll(
                "SELECT * FROM restraint_data WHERE district_code = ? AND school_year = ?",
                [$code, $year]
            );
            json_response(['data' => $rows]);
        }

        json_response(['data' => []]);
    }

    /** GET /api/cases */
    public function cases(array $params = []): void
    {
        $code = $_GET['district_code'] ?? '';
        $status = $_GET['status'] ?? '';

        $sql = "SELECT * FROM cases WHERE is_active = 1";
        $args = [];

        if ($code) {
            $sql .= " AND district_code = ?";
            $args[] = $code;
        }
        if ($status) {
            $sql .= " AND status = ?";
            $args[] = $status;
        }
        $sql .= " ORDER BY filed_date DESC";

        json_response(['data' => Database::fetchAll($sql, $args)]);
    }

    /** GET /api/articles */
    public function articles(array $params = []): void
    {
        $rows = Database::fetchAll(
            "SELECT * FROM articles WHERE is_active = 1 ORDER BY published_date DESC LIMIT 50"
        );
        json_response(['data' => $rows]);
    }

    /** GET /api/search */
    public function search(array $params = []): void
    {
        $q = $_GET['q'] ?? '';
        if (!$q) {
            json_response(['data' => []]);
        }
        $results = Database::fetchAll(
            "SELECT 'article' as type, title, slug, excerpt
             FROM articles WHERE is_active = 1 AND (title LIKE ? OR body LIKE ?)
             UNION ALL
             SELECT 'case' as type, title, slug, summary as excerpt
             FROM cases WHERE is_active = 1 AND (title LIKE ? OR summary LIKE ?)
             LIMIT 20",
            array_fill(0, 4, "%{$q}%")
        );
        json_response(['data' => $results]);
    }

    /** POST /api/submit */
    public function submit(array $params = []): void
    {
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
            json_response(['error' => 'Method not allowed'], 405);
        }
        $title = $_POST['title'] ?? '';
        $body = $_POST['body'] ?? '';
        if (!$title) {
            json_response(['error' => 'Title required'], 400);
        }
        Database::insert(
            "INSERT INTO submissions (title, body, submitter_email, submission_type)
             VALUES (?, ?, ?, ?)",
            [$title, $body, $_POST['submitter_email'] ?? '', $_POST['submission_type'] ?? 'tip']
        );
        json_response(['success' => true]);
    }

    /** POST /api/subscribe */
    public function subscribe(array $params = []): void
    {
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
            json_response(['error' => 'Method not allowed'], 405);
        }
        $email = $_POST['email'] ?? '';
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            json_response(['error' => 'Invalid email'], 400);
        }
        // TODO: integrate with email service
        json_response(['success' => true, 'message' => 'Subscribed']);
    }
}

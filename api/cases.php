<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

$action   = $_GET['action'] ?? 'list';
$caseId   = $_GET['id'] ?? '';
$district = $_GET['district'] ?? '';
$status   = $_GET['status'] ?? '';
$type     = $_GET['type'] ?? '';

try {
    if ($action === 'single' && $caseId) {
        $case = Database::fetch(
            'SELECT c.*, COUNT(cd.id) as document_count
             FROM cases c
             LEFT JOIN case_documents cd ON c.id = cd.case_id
             WHERE c.case_id = ?
             GROUP BY c.id',
            [$caseId]
        );

        if (!$case) {
            json_response(['error' => 'Case not found'], 404);
        }

        $case['timeline']       = json_decode($case['timeline'] ?? '[]', true);
        $case['requested_items'] = json_decode($case['requested_items'] ?? '[]', true);

        $documents = Database::fetchAll(
            'SELECT * FROM case_documents WHERE case_id = ? ORDER BY sort_order, document_date DESC',
            [$case['id']]
        );
        $case['documents'] = $documents;

        json_response(['case' => $case]);
    }

    if ($action === 'list') {
        $where  = ['c.status != ?'];
        $params = ['archived'];

        if ($district && $district !== 'all') {
            $where[]  = 'c.district_code = ?';
            $params[] = $district;
        }
        if ($status && $status !== 'all') {
            $where[]  = 'c.status = ?';
            $params[] = $status;
        }
        if ($type && $type !== 'all') {
            $where[]  = 'c.type = ?';
            $params[] = $type;
        }

        $whereClause = implode(' AND ', $where);

        $cases = Database::fetchAll(
            "SELECT c.*, COUNT(cd.id) as document_count
             FROM cases c
             LEFT JOIN case_documents cd ON c.id = cd.case_id
             WHERE {$whereClause}
             GROUP BY c.id
             ORDER BY c.filed_date DESC",
            $params
        );

        json_response(['cases' => $cases, 'total' => count($cases)]);
    }

    if ($action === 'timeline' && $caseId) {
        $case = Database::fetch('SELECT case_id, title, timeline FROM cases WHERE case_id = ?', [$caseId]);
        if (!$case) {
            json_response(['error' => 'Case not found'], 404);
        }
        json_response(['timeline' => json_decode($case['timeline'] ?? '[]', true)]);
    }

    json_response(['error' => 'Unknown action'], 400);
} catch (Exception $e) {
    json_response(['error' => APP_DEBUG ? $e->getMessage() : 'Internal server error'], 500);
}

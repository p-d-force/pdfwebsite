<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

$action  = $_GET['action'] ?? 'stats';
$dataset = $_GET['dataset'] ?? '';

try {
    if ($action === 'stats') {
        $stats = [
            'articles'       => (int)Database::fetchColumn("SELECT COUNT(*) FROM articles WHERE status = 'published'"),
            'cases'          => (int)Database::fetchColumn("SELECT COUNT(*) FROM cases WHERE status != 'archived'"),
            'open_cases'     => (int)Database::fetchColumn("SELECT COUNT(*) FROM cases WHERE status = 'open'"),
            'districts'      => (int)Database::fetchColumn("SELECT COUNT(*) FROM districts WHERE status = 'active'"),
            'speeches'       => (int)Database::fetchColumn('SELECT COUNT(*) FROM speeches'),
            'updates'        => (int)Database::fetchColumn('SELECT COUNT(*) FROM updates'),
            'overdue_cases'  => (int)Database::fetchColumn("SELECT COUNT(*) FROM cases WHERE status = 'overdue'"),
        ];
        json_response(['stats' => $stats]);
    }

    if ($action === 'restraint' || $action === 'restraint_summary') {
        // Compute statewide aggregates from school-level data (no pre-computed summary rows)
        $statewide = Database::fetchAll(
            "SELECT school_year,
                COUNT(*) as school_count,
                COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN total_restraints ELSE 0 END), 0) as sum_restraints,
                COALESCE(SUM(CASE WHEN students_restrained_suppressed = 0 THEN students_restrained ELSE 0 END), 0) as sum_students,
                COALESCE(SUM(CASE WHEN total_injuries_suppressed = 0 THEN total_injuries ELSE 0 END), 0) as sum_injuries,
                COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN enrollment ELSE 0 END), 0) as sum_enrollment
             FROM restraint_data
             WHERE is_summary_row = 0 AND district_name != 'State Total'
             GROUP BY school_year
             ORDER BY school_year"
        );

        $labels = [];
        $restraints = [];
        $injuries = [];
        foreach ($statewide as $row) {
            $labels[] = $row['school_year'];
            $restraints[] = (int)$row['sum_restraints'];
            $injuries[] = (int)$row['sum_injuries'];
        }

        // Fallback: hardcoded DESE statewide data with year-over-year variation
        $fallback = [
            'labels' => ['2016-17', '2017-18', '2018-19', '2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25'],
            'restraints' => [9930, 9615, 9311, 7711, 2781, 6787, 6570, 7958, 8425],
            'injuries' => [631, 504, 434, 491, 367, 452, 366, 498, 567],
        ];

        // Detect flat data (all years identical = scraper duplicated same year)
        $uniqueRestraints = array_unique($restraints);
        $useChart = (count($uniqueRestraints) <= 1 || empty($statewide)) ? $fallback : [
            'labels' => $labels,
            'restraints' => $restraints,
            'injuries' => $injuries,
        ];

        json_response([
            'statewide' => $statewide,
            'chart' => $useChart,
            'fallback' => (count($uniqueRestraints) <= 1) ? $fallback : null,
        ]);
    }

    if ($action === 'restraint_districts') {
        $district = $_GET['district'] ?? '';
        $year = $_GET['year'] ?? '';

        $where = ['is_summary_row = 0'];
        $params = [];

        if ($district) {
            // Match by district name (site codes != DESE codes)
            // Try exact code match first, then name LIKE
            $where[] = '(district_code = ? OR district_name LIKE ?)';
            $params[] = $district;
            $params[] = '%' . $district . '%';
        }
        if ($year) { $where[] = 'school_year = ?'; $params[] = $year; }

        $data = Database::fetchAll(
            'SELECT * FROM restraint_data WHERE ' . implode(' AND ', $where) . ' ORDER BY school_year DESC, restraint_rate_per_100 DESC',
            $params
        );
        json_response(['districts' => $data, 'total' => count($data)]);
    }

    if ($action === 'updates') {
        $limit = min(50, max(1, (int)($_GET['limit'] ?? 10)));
        $updates = Database::fetchAll(
            'SELECT u.*, c.case_id as case_ref
             FROM updates u
             LEFT JOIN cases c ON u.related_case_id = c.case_id
             ORDER BY u.created_at DESC
             LIMIT ?',
            [$limit]
        );
        json_response(['updates' => $updates]);
    }

    if ($action === 'districts') {
        $districts = Database::fetchAll(
            "SELECT d.*, COUNT(DISTINCT c.id) as case_count,
                SUM(CASE WHEN c.status = 'open' THEN 1 ELSE 0 END) as open_cases
             FROM districts d
             LEFT JOIN cases c ON d.code = c.district_code AND c.status != 'archived'
             WHERE d.status = 'active'
             GROUP BY d.id
             ORDER BY case_count DESC"
        );
        json_response(['districts' => $districts]);
    }

    if ($action === 'compare') {
        // Cross-dataset comparison: restraint vs enrollment vs discipline
        $year = $_GET['year'] ?? '2024-25';

        $data = Database::fetchAll(
            "SELECT
                r.district_name,
                r.district_code as restraint_code,
                SUM(CASE WHEN r.total_restraints_suppressed = 0 THEN r.total_restraints ELSE 0 END) as total_restraints,
                SUM(CASE WHEN r.students_restrained_suppressed = 0 THEN r.students_restrained ELSE 0 END) as students_restrained,
                SUM(CASE WHEN r.total_injuries_suppressed = 0 THEN r.total_injuries ELSE 0 END) as total_injuries,
                SUM(CASE WHEN r.total_restraints_suppressed = 0 THEN r.enrollment ELSE 0 END) as restraint_enrollment,
                COUNT(DISTINCT r.school_name) as schools_with_restraints
             FROM restraint_data r
             WHERE r.is_summary_row = 0 AND r.school_year = ? AND r.district_name != 'State Total'
             GROUP BY r.district_name, r.district_code
             HAVING total_restraints > 0
             ORDER BY total_restraints DESC
             LIMIT 50",
            [$year]
        );

        // Enrich with enrollment demographics and discipline data
        $enriched = [];
        foreach ($data as $row) {
            $name = $row['district_name'];

            // Try enrollment data (8-digit codes, match by name)
            $enr = Database::fetch(
                "SELECT sped_pct, low_income_pct, el_pct, high_needs_pct, high_needs_num
                 FROM enrollment_data
                 WHERE district_name = ? AND school_year = ?
                 LIMIT 1",
                [$name, $year]
            );

            // Try discipline data
            $disc = Database::fetch(
                "SELECT students, pct_out_school_susp, pct_in_school_susp, students_disciplined
                 FROM discipline_data
                 WHERE district_name = ? AND school_year = ?
                 LIMIT 1",
                [$name, $year]
            );

            // Try attendance data
            $att = Database::fetch(
                "SELECT attendance_rate, chronically_absent_10_pct
                 FROM attendance_data
                 WHERE district_name = ? AND school_year = ?
                 LIMIT 1",
                [$name, $year]
            );

            $row['sped_pct'] = $enr['sped_pct'] ?? null;
            $row['low_income_pct'] = $enr['low_income_pct'] ?? null;
            $row['el_pct'] = $enr['el_pct'] ?? null;
            $row['high_needs_pct'] = $enr['high_needs_pct'] ?? null;
            $row['total_students'] = $disc['students'] ?? null;
            $row['pct_out_school_susp'] = $disc['pct_out_school_susp'] ?? null;
            $row['pct_in_school_susp'] = $disc['pct_in_school_susp'] ?? null;
            $row['students_disciplined'] = $disc['students_disciplined'] ?? null;
            $row['attendance_rate'] = $att['attendance_rate'] ?? null;
            $row['chronically_absent_10_pct'] = $att['chronically_absent_10_pct'] ?? null;

            // Compute restraint rate
            if ($row['restraint_enrollment'] > 0) {
                $row['restraint_rate_per_100'] = round(($row['total_restraints'] / $row['restraint_enrollment']) * 100, 2);
            } else {
                $row['restraint_rate_per_100'] = null;
            }

            $enriched[] = $row;
        }

        json_response(['compare' => $enriched, 'year' => $year, 'total' => count($enriched)]);
    }

    json_response(['error' => 'Unknown action or dataset'], 400);
} catch (Exception $e) {
    json_response(['error' => APP_DEBUG ? $e->getMessage() : 'Internal server error'], 500);
}

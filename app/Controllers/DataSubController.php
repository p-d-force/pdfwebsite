<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;
use App\Core\Database;

class DataSubController
{
    private const PER_PAGE = 50;

    /** GET /data/restraint */
    public function restraint(array $params = []): void
    {
        $schoolYear = $_GET['school_year'] ?? '2024-25';
        $page = max(1, (int)($_GET['page'] ?? 1));
        $search = $_GET['search'] ?? '';

        $where = "WHERE is_summary_row = 0 AND district_name != 'State Total' AND school_year = ?";
        $bindings = [$schoolYear];
        if ($search !== '') {
            $where .= " AND (school_name LIKE ? OR district_name LIKE ?)";
            $bindings[] = "%{$search}%";
            $bindings[] = "%{$search}%";
        }

        $total = (int)Database::fetchColumn(
            "SELECT COUNT(*) FROM restraint_data $where", $bindings
        );

        $rows = Database::fetchAll(
            "SELECT district_name, school_name, total_restraints, students_restrained,
                    total_injuries, enrollment, total_restraints_suppressed
             FROM restraint_data $where
             ORDER BY total_restraints DESC
             LIMIT " . self::PER_PAGE . " OFFSET " . (($page - 1) * self::PER_PAGE),
            $bindings
        );

        $schoolYears = Database::fetchAll(
            "SELECT DISTINCT school_year FROM restraint_data WHERE is_summary_row = 0 ORDER BY school_year DESC"
        );

        View::render('data/restraint', [
            'page_title' => 'Restraint Data Browser',
            'rows' => $rows,
            'total' => $total,
            'page' => $page,
            'perPage' => self::PER_PAGE,
            'schoolYear' => $schoolYear,
            'schoolYears' => $schoolYears,
            'search' => $search,
        ]);
    }

    /** GET /data/prs */
    public function prs(array $params = []): void
    {
        $page = max(1, (int)($_GET['page'] ?? 1));
        $search = $_GET['search'] ?? '';
        $status = $_GET['status'] ?? '';

        $where = 'WHERE 1=1';
        $bindings = [];
        if ($search !== '') {
            $where .= " AND (district LIKE ? OR prs_number LIKE ? OR category LIKE ?)";
            $bindings[] = "%{$search}%";
            $bindings[] = "%{$search}%";
            $bindings[] = "%{$search}%";
        }
        if ($status !== '') {
            $where .= " AND status = ?";
            $bindings[] = $status;
        }

        $total = (int)Database::fetchColumn("SELECT COUNT(*) FROM prs_intakes_data $where", $bindings);

        $rows = Database::fetchAll(
            "SELECT prs_number, district, intake_date, status, category, subcategory, closure_code
             FROM prs_intakes_data $where
             ORDER BY intake_date DESC
             LIMIT " . self::PER_PAGE . " OFFSET " . (($page - 1) * self::PER_PAGE),
            $bindings
        );

        View::render('data/prs', [
            'page_title' => 'PRS Intake Browser',
            'rows' => $rows,
            'total' => $total,
            'page' => $page,
            'perPage' => self::PER_PAGE,
            'search' => $search,
            'status' => $status,
        ]);
    }

    /** GET /data/discipline */
    public function discipline(array $params = []): void
    {
        $page = max(1, (int)($_GET['page'] ?? 1));
        $search = $_GET['search'] ?? '';

        $where = 'WHERE 1=1';
        $bindings = [];
        if ($search !== '') {
            $where .= " AND (district_name LIKE ?)";
            $bindings[] = "%{$search}%";
        }

        $total = (int)Database::fetchColumn("SELECT COUNT(*) FROM discipline_data $where", $bindings);

        $rows = Database::fetchAll(
            "SELECT district_name, school_year, students, students_disciplined,
                    pct_in_school_susp, pct_out_school_susp, pct_expulsion
             FROM discipline_data $where
             ORDER BY district_name, school_year DESC
             LIMIT " . self::PER_PAGE . " OFFSET " . (($page - 1) * self::PER_PAGE),
            $bindings
        );

        View::render('data/discipline', [
            'page_title' => 'Discipline Data Browser',
            'rows' => $rows,
            'total' => $total,
            'page' => $page,
            'perPage' => self::PER_PAGE,
            'search' => $search,
        ]);
    }

    /** GET /data/enrollment */
    public function enrollment(array $params = []): void
    {
        $page = max(1, (int)($_GET['page'] ?? 1));
        $search = $_GET['search'] ?? '';

        $where = 'WHERE 1=1';
        $bindings = [];
        if ($search !== '') {
            $where .= " AND (district_name LIKE ?)";
            $bindings[] = "%{$search}%";
        }

        $total = (int)Database::fetchColumn("SELECT COUNT(*) FROM enrollment_data $where", $bindings);

        $rows = Database::fetchAll(
            "SELECT district_name, school_year, high_needs_num, high_needs_pct,
                    el_num, el_pct, low_income_num, low_income_pct, sped_num, sped_pct
             FROM enrollment_data $where
             ORDER BY district_name, school_year DESC
             LIMIT " . self::PER_PAGE . " OFFSET " . (($page - 1) * self::PER_PAGE),
            $bindings
        );

        View::render('data/enrollment', [
            'page_title' => 'Enrollment Demographics Browser',
            'rows' => $rows,
            'total' => $total,
            'page' => $page,
            'perPage' => self::PER_PAGE,
            'search' => $search,
        ]);
    }

    /** GET /data/attendance */
    public function attendance(array $params = []): void
    {
        $page = max(1, (int)($_GET['page'] ?? 1));
        $search = $_GET['search'] ?? '';

        $where = 'WHERE 1=1';
        $bindings = [];
        if ($search !== '') {
            $where .= " AND (district_name LIKE ?)";
            $bindings[] = "%{$search}%";
        }

        $total = (int)Database::fetchColumn("SELECT COUNT(*) FROM attendance_data $where", $bindings);

        $rows = Database::fetchAll(
            "SELECT district_name, school_year, attendance_rate, avg_absences,
                    absent_10_plus_pct, chronically_absent_10_pct
             FROM attendance_data $where
             ORDER BY district_name, school_year DESC
             LIMIT " . self::PER_PAGE . " OFFSET " . (($page - 1) * self::PER_PAGE),
            $bindings
        );

        View::render('data/attendance', [
            'page_title' => 'Attendance Data Browser',
            'rows' => $rows,
            'total' => $total,
            'page' => $page,
            'perPage' => self::PER_PAGE,
            'search' => $search,
        ]);
    }

    /** GET /data/sped-results */
    public function spedResults(array $params = []): void
    {
        $page = max(1, (int)($_GET['page'] ?? 1));
        $search = $_GET['search'] ?? '';

        $where = 'WHERE 1=1';
        $bindings = [];
        if ($search !== '') {
            $where .= " AND (district_name LIKE ?)";
            $bindings[] = "%{$search}%";
        }

        $total = (int)Database::fetchColumn("SELECT COUNT(*) FROM sped_data $where", $bindings);

        $rows = Database::fetchAll(
            "SELECT district_name, school_year, sped_grad_rate, sped_dropout_rate,
                    lre_full_incl_pct, parent_involve_pct
             FROM sped_data $where
             ORDER BY district_name, school_year DESC
             LIMIT " . self::PER_PAGE . " OFFSET " . (($page - 1) * self::PER_PAGE),
            $bindings
        );

        View::render('data/sped-results', [
            'page_title' => 'SPED Results Browser',
            'rows' => $rows,
            'total' => $total,
            'page' => $page,
            'perPage' => self::PER_PAGE,
            'search' => $search,
        ]);
    }
}

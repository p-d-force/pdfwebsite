<?php declare(strict_types=1);
namespace App\Controllers;

use App\Core\View;
use App\Core\Database;

class DataPortalController
{
    /** GET /data — data portal hub with tabbed interface */
    public function index(array $params = []): void
    {
        $activeTab = $_GET['tab'] ?? 'portal';

        $datasetCounts = [
            'restraint' => 0, 'discipline' => 0, 'enrollment' => 0,
            'attendance' => 0, 'sped' => 0, 'prs' => 0,
        ];

        try {
            $datasetCounts['restraint'] = (int)Database::fetchColumn(
                "SELECT COUNT(*) FROM restraint_data WHERE is_summary_row = 0"
            );
        } catch (\Exception $e) {
            error_log("DataPortal: Failed to count restraint_data: " . $e->getMessage());
        }
        try { $datasetCounts['discipline'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM discipline_data"); } catch (\Exception $e) {
            error_log("DataPortal: Failed to count discipline_data: " . $e->getMessage());
        }
        try { $datasetCounts['enrollment'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM enrollment_data"); } catch (\Exception $e) {
            error_log("DataPortal: Failed to count enrollment_data: " . $e->getMessage());
        }
        try { $datasetCounts['attendance'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM attendance_data"); } catch (\Exception $e) {
            error_log("DataPortal: Failed to count attendance_data: " . $e->getMessage());
        }
        try { $datasetCounts['sped'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM sped_data"); } catch (\Exception $e) {
            error_log("DataPortal: Failed to count sped_data: " . $e->getMessage());
        }
        try { $datasetCounts['prs'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM prs_intakes_data"); } catch (\Exception $e) {
            error_log("DataPortal: Failed to count prs_intakes_data: " . $e->getMessage());
        }

        // Restraint tab data
        $restraintData = null;
        $schoolYears = [];
        $restraintDistricts = [];
        if ($activeTab === 'restraint') {
            $schoolYear = $_GET['school_year'] ?? '2024-25';
            $districtCode = $_GET['district'] ?? '';
            $restraintData = $this->getRestraintData($schoolYear, $districtCode);
            $schoolYears = Database::fetchAll(
                "SELECT DISTINCT school_year FROM restraint_data WHERE is_summary_row = 0 ORDER BY school_year DESC"
            );
            $restraintDistricts = Database::fetchAll(
                "SELECT DISTINCT district_code, district_name FROM restraint_data WHERE is_summary_row = 0 AND district_code != '' ORDER BY district_name"
            );
        }

        View::render('data-portal', [
            'page_title' => 'Data Portal',
            'page_description' => 'Interactive exploration of DESE data across Massachusetts public schools.',
            'activeTab' => $activeTab,
            'datasetCounts' => $datasetCounts,
            'restraintData' => $restraintData,
            'schoolYears' => $schoolYears,
            'restraintDistricts' => $restraintDistricts,
        ]);
    }

    private function getRestraintData(string $schoolYear, string $districtCode): array
    {
        $where = "WHERE is_summary_row = 0 AND district_name != 'State Total' AND school_year = ?";
        $params = [$schoolYear];
        if ($districtCode !== '') {
            $where .= " AND district_code = ?";
            $params[] = $districtCode;
        }
        $rows = Database::fetchAll(
            "SELECT district_name, school_name, total_restraints, students_restrained,
                    total_injuries, enrollment, total_restraints_suppressed
             FROM restraint_data $where ORDER BY total_restraints DESC",
            $params
        );
        return ['rows' => $rows, 'schoolYear' => $schoolYear, 'districtCode' => $districtCode];
    }

    /** GET /compare — interactive district comparison */
    public function compare(array $params = []): void
    {
        $schoolYear = $_GET['school_year'] ?? '2024-25';

        $restraintRows = Database::fetchAll(
            "SELECT district_name,
                COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN total_restraints ELSE 0 END), 0) as total_restraints,
                COALESCE(SUM(CASE WHEN students_restrained_suppressed = 0 THEN students_restrained ELSE 0 END), 0) as students_restrained,
                COALESCE(SUM(CASE WHEN total_injuries_suppressed = 0 THEN total_injuries ELSE 0 END), 0) as total_injuries,
                COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN enrollment ELSE 0 END), 0) as enrollment
             FROM restraint_data
             WHERE school_year = ? AND is_summary_row = 0 AND district_name != 'State Total'
             GROUP BY district_name ORDER BY district_name",
            [$schoolYear]
        );

        $compareMap = [];
        foreach ($restraintRows as $r) {
            $enroll = (int)($r['enrollment'] ?? 0);
            $compareMap[$r['district_name']] = [
                'total_restraints' => (int)($r['total_restraints'] ?? 0),
                'students_restrained' => (int)($r['students_restrained'] ?? 0),
                'total_injuries' => (int)($r['total_injuries'] ?? 0),
                'enrollment' => $enroll,
                'restraint_rate' => $enroll > 0 ? round(((int)$r['total_restraints'] / $enroll) * 100, 2) : 0,
            ];
        }

        // Enrollment demographics
        $enrollRows = Database::fetchAll(
            "SELECT district_name, sped_pct, low_income_pct, el_pct
             FROM enrollment_data WHERE school_year = ?",
            [$schoolYear]
        );
        $demographicsMap = [];
        foreach ($enrollRows as $r) {
            $demographicsMap[$r['district_name']] = $r;
        }

        // School years for selector
        $schoolYears = Database::fetchAll(
            "SELECT DISTINCT school_year FROM restraint_data WHERE is_summary_row = 0 ORDER BY school_year DESC"
        );

        View::render('compare', [
            'page_title' => 'Compare Districts',
            'page_description' => 'Compare Massachusetts school districts side by side on restraint data, enrollment, and more.',
            'compareMap' => $compareMap,
            'demographicsMap' => $demographicsMap,
            'schoolYear' => $schoolYear,
            'schoolYears' => $schoolYears,
        ]);
    }
}

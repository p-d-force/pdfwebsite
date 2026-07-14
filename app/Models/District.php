<?php declare(strict_types=1);
namespace App\Models;

use App\Core\Database;

/**
 * District data access layer.
 * All district queries live here — extracted from districts/district.php
 * and districts/index.php.
 */
class District
{
    /** Find by URL slug */
    public static function findBySlug(string $slug): ?array
    {
        return Database::fetch(
            'SELECT * FROM districts WHERE slug = ? AND is_active = 1', [$slug]
        );
    }

    /** Find by DESE district code (legacy URL support) */
    public static function findByCode(string $code): ?array
    {
        return Database::fetch(
            'SELECT * FROM districts WHERE district_code = ? AND is_active = 1', [$code]
        );
    }

    /** All active districts with case counts */
    public static function all(): array
    {
        return Database::fetchAll(
            "SELECT d.*,
                    COUNT(DISTINCT c.id) as case_count,
                    SUM(CASE WHEN c.status IN ('open','pending') THEN 1 ELSE 0 END) as open_cases
             FROM districts d
             LEFT JOIN cases c ON d.district_code = c.district_code AND c.status != 'archived'
             WHERE d.is_active = 1
             GROUP BY d.id
             ORDER BY case_count DESC, d.district_name ASC"
        );
    }

    /** Active cases for a district */
    public static function cases(string $districtCode): array
    {
        return Database::fetchAll(
            "SELECT c.*, COUNT(cd.id) as document_count
             FROM cases c LEFT JOIN case_documents cd ON c.id = cd.case_id
             WHERE c.district_code = ? AND c.status != 'archived'
             GROUP BY c.id ORDER BY c.filed_date DESC",
            [$districtCode]
        );
    }

    /** Published articles linked to a district */
    public static function articles(string $districtCode): array
    {
        return Database::fetchAll(
            'SELECT a.title, a.slug, a.excerpt, a.published_date
             FROM articles a
             JOIN article_district_links adl ON a.id = adl.article_id
             JOIN districts d ON adl.district_id = d.id
             WHERE d.district_code = ? AND a.is_active = 1
             ORDER BY a.published_date DESC LIMIT 6',
            [$districtCode]
        );
    }

    /** Speeches/testimony linked to a district */
    public static function speeches(string $districtCode): array
    {
        return Database::fetchAll(
            'SELECT * FROM speeches WHERE related_district_code = ?
             ORDER BY event_date DESC LIMIT 4',
            [$districtCode]
        );
    }

    /** Aggregate DESE data summary for a district dashboard */
    public static function dataSummary(string $districtCode, string $districtName): array
    {
        $summary = [
            'restraint' => null,
            'enrollment' => null,
            'discipline' => null,
            'attendance' => null,
            'has_any' => false,
        ];

        try {
            // Restraint data — try full name, then shorter prefixes
            $summary['restraint'] = self::_fetchDeseRow('restraint_data',
                "COUNT(DISTINCT school_name) as school_count,
                 COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN total_restraints ELSE 0 END), 0) as total_restraints,
                 COALESCE(SUM(CASE WHEN students_restrained_suppressed = 0 THEN students_restrained ELSE 0 END), 0) as students_restrained,
                 COALESCE(SUM(CASE WHEN total_injuries_suppressed = 0 THEN total_injuries ELSE 0 END), 0) as total_injuries,
                 COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN enrollment ELSE 0 END), 0) as total_enrollment",
                $districtName,
                "is_summary_row = 0"
            );

            // Enrollment
            $summary['enrollment'] = self::_fetchDeseRow('enrollment_data',
                'total_enrollment, sped_pct, low_income_pct, el_pct',
                $districtName);

            // Discipline
            $summary['discipline'] = self::_fetchDeseRow('discipline_data',
                'students_disciplined, pct_in_school_susp, pct_out_school_susp',
                $districtName);

            // Attendance
            $summary['attendance'] = self::_fetchDeseRow('attendance_data',
                'attendance_rate, chronically_absent_10_pct',
                $districtName);

            $summary['has_any'] = ($summary['restraint'] || $summary['enrollment']
                || $summary['discipline'] || $summary['attendance']);
        } catch (\Exception $e) {
            // Data unavailable — return empty summary
        }

        return $summary;
    }

    // ── Internal helpers ──

    /** Try progressively shorter name prefixes to match DESE data */
    private static function _fetchDeseRow(
        string $table, string $cols, string $districtName, string $extraWhere = ''
    ): ?array {
        $words = explode(' ', $districtName);
        $candidates = [$districtName];
        if (count($words) >= 2) {
            $candidates[] = implode(' ', array_slice($words, 0, 2));
        }
        if (!in_array($words[0], $candidates, true)) {
            $candidates[] = $words[0];
        }

        foreach ($candidates as $candidate) {
            $where = "district_name = ? AND school_year = '2024-25'";
            if ($extraWhere) {
                $where .= ' AND ' . $extraWhere;
            }
            $row = Database::fetch(
                "SELECT {$cols} FROM {$table} WHERE {$where} LIMIT 1",
                [$candidate]
            );
            if ($row) {
                return $row;
            }
        }
        return null;
    }
}

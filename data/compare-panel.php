<?php
/**
 * Compare Districts Interactive Panel
 * Include this in data/index.php within the compare tab section,
 * BEFORE the existing cross-dataset table (around line 354 of index.php).
 *
 * Uses Database::fetchAll() — the project's standard query wrapper.
 * No external dependencies beyond the existing includes.
 */

declare(strict_types=1);

$school_year = '2024-25';

// ── Build district comparison dataset ──────────────────────────────────

// Aggregated restraint data per district
$restraint_rows = Database::fetchAll(
    "SELECT district_name,
            COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN total_restraints ELSE 0 END), 0) as total_restraints,
            COALESCE(SUM(CASE WHEN students_restrained_suppressed = 0 THEN students_restrained ELSE 0 END), 0) as students_restrained,
            COALESCE(SUM(CASE WHEN total_injuries_suppressed = 0 THEN total_injuries ELSE 0 END), 0) as total_injuries,
            COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN enrollment ELSE 0 END), 0) as enrollment
     FROM restraint_data
     WHERE school_year = ? AND is_summary_row = 0 AND district_name != 'State Total'
     GROUP BY district_name
     ORDER BY district_name",
    [$school_year]
);

$restraint_map = [];
foreach ($restraint_rows as $r) {
    $enroll = (int)($r['enrollment'] ?? 0);
    $total_r = (int)($r['total_restraints'] ?? 0);
    $restraint_map[$r['district_name']] = [
        'total_restraints' => $total_r,
        'students_restrained' => (int)($r['students_restrained'] ?? 0),
        'total_injuries' => (int)($r['total_injuries'] ?? 0),
        'enrollment' => $enroll,
        'restraint_rate' => $enroll > 0 ? round(($total_r / $enroll) * 100, 2) : 0,
    ];
}

// Enrollment demographics (one row per district per year)
$enroll_rows = Database::fetchAll(
    "SELECT district_name, sped_pct, low_income_pct, el_pct
     FROM enrollment_data
     WHERE school_year = ?",
    [$school_year]
);
$enroll_map = [];
foreach ($enroll_rows as $r) {
    $enroll_map[$r['district_name']] = [
        'sped_pct' => $r['sped_pct'] !== null ? (float)$r['sped_pct'] : null,
        'low_income_pct' => $r['low_income_pct'] !== null ? (float)$r['low_income_pct'] : null,
        'el_pct' => $r['el_pct'] !== null ? (float)$r['el_pct'] : null,
    ];
}

// Discipline OSS rates
$disc_rows = Database::fetchAll(
    "SELECT district_name, pct_out_school_susp
     FROM discipline_data
     WHERE school_year = ?",
    [$school_year]
);
$disc_map = [];
foreach ($disc_rows as $r) {
    $disc_map[$r['district_name']] = $r['pct_out_school_susp'] !== null ? (float)$r['pct_out_school_susp'] : null;
}

// Attendance data
$att_rows = Database::fetchAll(
    "SELECT district_name, attendance_rate, chronically_absent_10_pct
     FROM attendance_data
     WHERE school_year = ?",
    [$school_year]
);
$att_map = [];
foreach ($att_rows as $r) {
    $att_map[$r['district_name']] = [
        'attendance_rate' => $r['attendance_rate'] !== null ? (float)$r['attendance_rate'] : null,
        'chr_absent_pct' => $r['chronically_absent_10_pct'] !== null ? (float)$r['chronically_absent_10_pct'] : null,
    ];
}

// Merge all datasets into one comparison array
$compare_data = [];
$all_names = array_unique(array_merge(
    array_keys($restraint_map),
    array_keys($enroll_map),
    array_keys($disc_map),
    array_keys($att_map)
));
sort($all_names);

foreach ($all_names as $name) {
    $r = $restraint_map[$name] ?? ['total_restraints' => 0, 'students_restrained' => 0, 'total_injuries' => 0, 'enrollment' => 0, 'restraint_rate' => 0];
    $e = $enroll_map[$name] ?? ['sped_pct' => null, 'low_income_pct' => null, 'el_pct' => null];
    $compare_data[] = [
        'district_name' => $name,
        'total_restraints' => $r['total_restraints'],
        'students_restrained' => $r['students_restrained'],
        'total_injuries' => $r['total_injuries'],
        'enrollment' => $r['enrollment'],
        'restraint_rate' => $r['restraint_rate'],
        'sped_pct' => $e['sped_pct'],
        'low_income_pct' => $e['low_income_pct'],
        'el_pct' => $e['el_pct'],
        'oss_pct' => $disc_map[$name] ?? null,
        'attendance_rate' => $att_map[$name]['attendance_rate'] ?? null,
        'chr_absent_pct' => $att_map[$name]['chr_absent_pct'] ?? null,
    ];
}

$data_json = json_encode($compare_data, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);

// ── Render interactive panel ───────────────────────────────────────────
?>
<script id="compare-districts-data" type="application/json"><?php echo $data_json; ?></script>

<div class="restraint-comparison-panel">
    <h3 style="margin-bottom:1rem;">Select Districts to Compare</h3>

    <div class="compare-select-row">
        <div style="flex:1;min-width:200px;">
            <label style="font-size:0.8rem;color:var(--text-muted);display:block;margin-bottom:0.3rem;">District A</label>
            <select id="compare-district-a" class="form-input" style="width:100%;">
                <option value="">-- Select a district --</option>
            </select>
        </div>
        <div style="flex:1;min-width:200px;">
            <label style="font-size:0.8rem;color:var(--text-muted);display:block;margin-bottom:0.3rem;">District B</label>
            <select id="compare-district-b" class="form-input" style="width:100%;">
                <option value="">-- Select a district --</option>
            </select>
        </div>
    </div>

    <div class="compare-chart-container">
        <canvas id="districtCompareChart"></canvas>
    </div>

    <div class="similar-districts-panel">
        <h4>Similar Districts</h4>
        <p style="color:var(--text-muted);font-size:0.82rem;margin-bottom:0.75rem;">
            Add districts with similar demographics or restraint patterns to compare against.
        </p>
        <div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;margin-bottom:0.75rem;">
            <select id="similar-district-select" class="form-input" style="min-width:200px;">
                <option value="">-- Add a district --</option>
            </select>
            <button id="similar-district-add" class="similar-district-add">+ Add to Chart</button>
        </div>
        <div id="similar-districts-list" style="display:flex;flex-wrap:wrap;gap:0.35rem;"></div>
    </div>
</div>

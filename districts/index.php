<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

$districts = Database::fetchAll(
    "SELECT d.*,
        COUNT(DISTINCT c.id) as case_count,
        SUM(CASE WHEN c.status = 'open' THEN 1 ELSE 0 END) as open_cases
     FROM districts d
     LEFT JOIN cases c ON d.code = c.district_code AND c.status != 'archived'
     WHERE d.status = 'active'
     GROUP BY d.id
     ORDER BY case_count DESC, d.name ASC"
);

// Helper for district name matching
function findData(string $table, string $cols, string $districtName): ?array {
    $candidates = [$districtName];
    $words = explode(' ', $districtName);
    if (count($words) >= 2) $candidates[] = implode(' ', array_slice($words, 0, 2));
    if (!in_array($words[0], $candidates)) $candidates[] = $words[0];
    foreach ($candidates as $c) {
        $r = Database::fetch("SELECT {$cols} FROM {$table} WHERE district_name = ? AND school_year = '2024-25' LIMIT 1", [$c]);
        if ($r) return $r;
    }
    return null;
}

// Enrich each district with live data
$enriched = [];
foreach ($districts as $d) {
    $name = $d['name'];
    
    // Restraint summary
    $r = Database::fetch(
        "SELECT COALESCE(SUM(total_restraints), 0) as restraints,
                COALESCE(SUM(enrollment), 0) as enrollment
         FROM restraint_data
         WHERE (district_name = ? OR district_name LIKE ?) AND school_year = '2024-25'",
        [$name, '%' . $name . '%']
    );
    // Fallback to short name
    if (!$r || ($r['restraints'] ?? 0) == 0) {
        $short = explode(' ', $name);
        $shortCandidates = [];
        if (count($short) >= 2) $shortCandidates[] = implode(' ', array_slice($short, 0, 2));
        $shortCandidates[] = $short[0];
        foreach ($shortCandidates as $sn) {
            if ($sn === $name) continue;
            $r = Database::fetch(
                "SELECT COALESCE(SUM(total_restraints), 0) as restraints,
                        COALESCE(SUM(enrollment), 0) as enrollment
                 FROM restraint_data
                 WHERE district_name = ? AND school_year = '2024-25'",
                [$sn]
            );
            if ($r && ($r['restraints'] ?? 0) > 0) break;
        }
    }
    
    $d['restraints'] = $r['restraints'] ?? 0;
    $d['restraint_enrollment'] = $r['enrollment'] ?? 0;
    $d['restraint_rate'] = ($d['restraint_enrollment'] > 0 && $d['restraints'] > 0) 
        ? round(($d['restraints'] / $d['restraint_enrollment']) * 100, 1) : null;
    
    // Enrollment demographics
    $enr = findData('enrollment_data', 'sped_pct, low_income_pct, high_needs_pct', $name);
    $d['sped_pct'] = $enr['sped_pct'] ?? null;
    
    // Discipline
    $disc = findData('discipline_data', 'students, pct_out_school_susp', $name);
    $d['total_students'] = $disc['students'] ?? null;
    $d['oss_pct'] = $disc['pct_out_school_susp'] ?? null;
    
    // Attendance
    $att = findData('attendance_data', 'attendance_rate, chronically_absent_10_pct', $name);
    $d['attendance_rate'] = $att['attendance_rate'] ?? null;
    
    $enriched[] = $d;
}

$page_title       = 'District Profiles';
$page_description = 'School district profiles showing cases, data summaries, and advocacy activity across Massachusetts.';
include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="districts">
    <div class="container">
        <div class="section-header" data-animate>
            <span class="section-tag">Massachusetts Districts</span>
            <h2 class="section-title">District Profiles</h2>
            <p class="section-subtitle">
                Per-district pages aggregating cases, DESE data, and advocacy activity. Click any district for full details including restraint, enrollment, discipline, and attendance data.
            </p>
        </div>

        <?php if (empty($enriched)): ?>
            <div class="empty-state" data-animate>
                <p>District profiles will appear here as investigations expand.</p>
            </div>
        <?php else: ?>
            <div class="districts-grid" data-animate>
                <?php foreach ($enriched as $district): ?>
                    <a href="/districts/<?php echo h(strtolower($district['code'])); ?>" class="district-card">
                        <div class="district-card-header">
                            <h3 class="district-card-name"><?php echo h($district['name']); ?></h3>
                            <?php if ($district['open_cases'] > 0): ?>
                                <span class="status-badge status-open"><?php echo $district['open_cases']; ?> Active</span>
                            <?php endif; ?>
                        </div>
                        <p class="district-card-location"><?php echo h($district['location']); ?></p>
                        <?php if ($district['description']): ?>
                            <p class="district-card-desc"><?php echo h(truncate($district['description'], 120)); ?></p>
                        <?php endif; ?>
                        
                        <!-- Data badges from live MariaDB -->
                        <div class="district-card-stats" style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.75rem;">
                            <?php if ($district['case_count'] > 0): ?>
                                <span style="background:rgba(255,90,31,0.12);color:var(--accent-glow);padding:0.15rem 0.5rem;border-radius:999px;font-size:0.7rem;font-weight:600;">
                                    <?php echo $district['case_count']; ?> case<?php echo $district['case_count'] !== 1 ? 's' : ''; ?>
                                </span>
                            <?php endif; ?>
                            <?php if ($district['restraints'] > 0): ?>
                                <span style="background:rgba(255,90,31,0.08);color:#f5a623;padding:0.15rem 0.5rem;border-radius:999px;font-size:0.7rem;font-weight:600;">
                                    <?php echo number_format((int)$district['restraints']); ?> restraints
                                </span>
                            <?php endif; ?>
                            <?php if ($district['restraint_rate'] !== null): ?>
                                <span style="background:rgba(255,90,31,0.08);color:var(--accent);padding:0.15rem 0.5rem;border-radius:999px;font-size:0.7rem;font-weight:600;">
                                    Rate: <?php echo number_format($district['restraint_rate'], 1); ?>/100
                                </span>
                            <?php endif; ?>
                            <?php if ($district['total_students']): ?>
                                <span style="background:rgba(6,182,212,0.1);color:#06b6d4;padding:0.15rem 0.5rem;border-radius:999px;font-size:0.7rem;">
                                    <?php echo number_format((int)$district['total_students']); ?> students
                                </span>
                            <?php endif; ?>
                            <?php if ($district['sped_pct'] !== null): ?>
                                <span style="background:rgba(139,92,246,0.1);color:#8b5cf6;padding:0.15rem 0.5rem;border-radius:999px;font-size:0.7rem;">
                                    SPED <?php echo number_format((float)$district['sped_pct'], 1); ?>%
                                </span>
                            <?php endif; ?>
                            <?php if ($district['oss_pct'] !== null): ?>
                                <span style="background:rgba(245,158,11,0.1);color:#f59e0b;padding:0.15rem 0.5rem;border-radius:999px;font-size:0.7rem;">
                                    OSS <?php echo number_format((float)$district['oss_pct'], 1); ?>%
                                </span>
                            <?php endif; ?>
                            <?php if ($district['attendance_rate'] !== null): ?>
                                <span style="background:rgba(16,185,129,0.1);color:#10b981;padding:0.15rem 0.5rem;border-radius:999px;font-size:0.7rem;">
                                    Att: <?php echo number_format((float)$district['attendance_rate'], 1); ?>%
                                </span>
                            <?php endif; ?>
                        </div>
                        <span class="district-card-link" style="margin-top:0.5rem;display:inline-block;">View District Profile →</span>
                    </a>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
    </div>
</section>

<?php
include __DIR__ . '/../includes/footer.php';

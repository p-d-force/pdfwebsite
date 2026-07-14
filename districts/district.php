<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

$code = strtoupper($_GET['code'] ?? '');
if (!$code) {
    http_response_code(404);
    die('District not found.');
}

$district = Database::fetch('SELECT * FROM districts WHERE code = ?', [$code]);
if (!$district) {
    http_response_code(404);
    $page_title = 'District Not Found';
    include __DIR__ . '/../includes/head.php';
    include __DIR__ . '/../includes/header.php';
    echo '<section class="section"><div class="container"><div class="empty-state"><h2>District Not Found</h2><p>The requested district doesn\'t exist.</p><a href="/districts/" class="btn btn-secondary" style="margin-top:1rem;">View All Districts</a></div></div></section>';
    include __DIR__ . '/../includes/footer.php';
    exit;
}

$districtName = $district['name'];

// ── CASES ──
$cases = Database::fetchAll(
    "SELECT c.*, COUNT(cd.id) as document_count
     FROM cases c LEFT JOIN case_documents cd ON c.id = cd.case_id
     WHERE c.district_code = ? AND c.status != ? GROUP BY c.id ORDER BY c.filed_date DESC",
    [$code, 'archived']
);

// ── ARTICLES ──
$articles = Database::fetchAll(
    'SELECT a.title, a.slug, a.excerpt, a.category, a.published_at, a.read_time
     FROM articles a JOIN article_district_links adl ON a.id = adl.article_id
     JOIN districts d ON adl.district_id = d.id
     WHERE d.code = ? AND a.status = ? ORDER BY a.published_at DESC LIMIT 6',
    [$code, 'published']
);

// ── SPEECHES ──
$speeches = Database::fetchAll(
    'SELECT * FROM speeches WHERE related_district_code = ? ORDER BY published_at DESC LIMIT 4',
    [$code]
);

// ── DATA SUMMARY (live from MariaDB, 2024-25) ──
$dataSummary = [
    'restraint' => null,
    'enrollment' => null,
    'discipline' => null,
    'attendance' => null,
    'has_any' => false,
];

// Helper: try progressively shorter name prefixes for DESE match
function fetch_dese_data(string $table, string $cols, string $districtName, string $extraWhere = ''): ?array {
    $words = explode(' ', $districtName);
    $candidates = [$districtName];
    if (count($words) >= 2) $candidates[] = implode(' ', array_slice($words, 0, 2));
    if (!in_array($words[0], $candidates)) $candidates[] = $words[0];
    
    foreach ($candidates as $candidate) {
        $where = "district_name = ? AND school_year = '2024-25'";
        if ($extraWhere) $where .= ' AND ' . $extraWhere;
        $result = Database::fetch(
            "SELECT {$cols} FROM {$table} WHERE {$where} LIMIT 1",
            [$candidate]
        );
        if ($result) return $result;
    }
    return null;
}

try {
    $dataSummary['restraint'] = fetch_dese_data('restraint_data',
        "COUNT(DISTINCT school_name) as school_count,
         COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN total_restraints ELSE 0 END), 0) as total_restraints,
         COALESCE(SUM(CASE WHEN students_restrained_suppressed = 0 THEN students_restrained ELSE 0 END), 0) as students_restrained,
         COALESCE(SUM(CASE WHEN total_injuries_suppressed = 0 THEN total_injuries ELSE 0 END), 0) as total_injuries,
         COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN enrollment ELSE 0 END), 0) as total_enrollment",
        $districtName,
        'is_summary_row = 0'
    );
    // Fallback: try progressively shorter name prefixes
    if (!$dataSummary['restraint'] || ($dataSummary['restraint']['total_restraints'] ?? 0) == 0) {
        $words = explode(' ', $districtName);
        // Try: first 2 words, then first word, then LIKE match
        $fallbacks = [];
        if (count($words) >= 2) $fallbacks[] = implode(' ', array_slice($words, 0, 2));
        $fallbacks[] = $words[0];
        foreach ($fallbacks as $shortName) {
            if ($shortName === $districtName) continue;
            $dataSummary['restraint'] = Database::fetch(
                "SELECT COUNT(DISTINCT school_name) as school_count,
                    COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN total_restraints ELSE 0 END), 0) as total_restraints,
                    COALESCE(SUM(CASE WHEN students_restrained_suppressed = 0 THEN students_restrained ELSE 0 END), 0) as students_restrained,
                    COALESCE(SUM(CASE WHEN total_injuries_suppressed = 0 THEN total_injuries ELSE 0 END), 0) as total_injuries,
                    COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN enrollment ELSE 0 END), 0) as total_enrollment
                 FROM restraint_data
                 WHERE district_name = ? AND school_year = '2024-25' AND is_summary_row = 0",
                [$shortName]
            );
            if ($dataSummary['restraint'] && ($dataSummary['restraint']['total_restraints'] ?? 0) > 0) break;
        }
    }
    if ($dataSummary['restraint'] && ($dataSummary['restraint']['total_restraints'] ?? 0) > 0) {
        $dataSummary['has_any'] = true;
    }
} catch (Exception $e) {}

try {
    $dataSummary['enrollment'] = fetch_dese_data('enrollment_data', 
        'sped_pct, low_income_pct, el_pct, high_needs_pct, high_needs_num', $districtName);
} catch (Exception $e) {}

try {
    $dataSummary['discipline'] = fetch_dese_data('discipline_data',
        'students, students_disciplined, pct_out_school_susp, pct_in_school_susp', $districtName);
} catch (Exception $e) {}

try {
    $dataSummary['attendance'] = fetch_dese_data('attendance_data',
        'attendance_rate, chronically_absent_10_pct, absent_10_plus_pct', $districtName);
} catch (Exception $e) {}

// Compute restraint rate
$restraintRate = null;
if ($dataSummary['restraint'] && $dataSummary['restraint']['total_enrollment'] > 0) {
    $restraintRate = round(($dataSummary['restraint']['total_restraints'] / $dataSummary['restraint']['total_enrollment']) * 100, 2);
}

// ── Grades served from enrollment or district record ──
$gradesServed = $district['grades_served'] ?? '';
$region = $district['region'] ?? '';

// Simple MA region/county lookup by town
$townLower = strtolower(explode(',', $district['location'] ?? '')[0]);
$maRegions = [
    'attleboro' => 'Bristol County · Southeast MA',
    'fall river' => 'Bristol County · Southeast MA',
    'bridgewater' => 'Plymouth County · Southeast MA',
    'raynham' => 'Bristol County · Southeast MA',
    'whitman' => 'Plymouth County · Southeast MA',
    'hanson' => 'Plymouth County · Southeast MA',
    'norton' => 'Bristol County · Southeast MA',
    'malden' => 'Middlesex County · Greater Boston',
];
$countyRegion = $maRegions[$townLower] ?? ($region ?: '');

$page_title       = $districtName;
$page_description = $district['description'] ?: 'District profile for ' . $districtName;
include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="district-detail">
    <div class="container">
        <div class="district-detail-header" data-animate>
            <span class="section-tag">District Profile</span>
            <h1 class="section-title"><?php echo h($districtName); ?></h1>
            <p class="section-subtitle">
                <?php echo h($district['location']); ?>
                <?php if ($countyRegion): ?> · <?php echo h($countyRegion); ?><?php endif; ?>
                <?php if ($gradesServed): ?> · Grades <?php echo h($gradesServed); ?><?php endif; ?>
            </p>
            <?php if ($district['description']): ?>
                <p class="district-detail-desc"><?php echo h($district['description']); ?></p>
            <?php endif; ?>
        </div>

        <!-- Stats Bar (live data) -->
        <div class="hero-stats" data-animate>
            <div class="stat">
                <span class="stat-value"><?php echo count($cases); ?></span>
                <span class="stat-label">Cases</span>
            </div>
            <?php if ($dataSummary['restraint'] && $dataSummary['restraint']['total_restraints'] > 0): ?>
            <div class="stat">
                <span class="stat-value"><?php echo number_format((int)$dataSummary['restraint']['total_restraints']); ?></span>
                <span class="stat-label">Restraints (24-25)</span>
            </div>
            <?php endif; ?>
            <?php if ($restraintRate !== null): ?>
            <div class="stat">
                <span class="stat-value" style="color:var(--accent);"><?php echo number_format($restraintRate, 1); ?></span>
                <span class="stat-label">Rate / 100 Students</span>
            </div>
            <?php endif; ?>
            <?php if ($dataSummary['discipline'] && $dataSummary['discipline']['students'] > 0): ?>
            <div class="stat">
                <span class="stat-value"><?php echo number_format((int)$dataSummary['discipline']['students']); ?></span>
                <span class="stat-label">Students Enrolled</span>
            </div>
            <?php endif; ?>
            <?php if ($dataSummary['enrollment']): ?>
            <div class="stat">
                <span class="stat-value"><?php echo number_format((float)$dataSummary['enrollment']['sped_pct'], 1); ?>%</span>
                <span class="stat-label">Students w/ IEPs</span>
            </div>
            <?php endif; ?>
            <div class="stat">
                <span class="stat-value"><?php echo count($articles); ?></span>
                <span class="stat-label">Articles</span>
            </div>
        </div>

        <!-- Data Summary Panel -->
        <?php if ($dataSummary['has_any'] || $dataSummary['enrollment'] || $dataSummary['discipline'] || $dataSummary['attendance']): ?>
        <div class="district-section" data-animate>
            <h2 class="section-title" style="font-size:1.5rem;margin-bottom:1rem;">DESE Data Snapshot (2024-25)</h2>
            <div class="resources-grid" style="grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:1rem;">

                <?php if ($dataSummary['restraint'] && $dataSummary['restraint']['total_restraints'] > 0): ?>
                <div class="resource-card" style="border-left:3px solid var(--accent);">
                    <h4 style="margin-bottom:0.5rem;">Restraint &amp; Seclusion</h4>
                    <table style="width:100%;font-size:0.85rem;color:var(--text-muted);">
                        <tr><td>Schools reporting</td><td style="text-align:right;color:#fff;"><?php echo (int)$dataSummary['restraint']['school_count']; ?></td></tr>
                        <tr><td>Total restraints</td><td style="text-align:right;color:#fff;"><?php echo number_format((int)$dataSummary['restraint']['total_restraints']); ?></td></tr>
                        <tr><td>Students restrained</td><td style="text-align:right;color:#fff;"><?php echo number_format((int)$dataSummary['restraint']['students_restrained']); ?></td></tr>
                        <tr><td>Total injuries</td><td style="text-align:right;color:#fff;"><?php echo number_format((int)$dataSummary['restraint']['total_injuries']); ?></td></tr>
                        <tr><td>Rate per 100</td><td style="text-align:right;color:var(--accent-glow);font-weight:600;"><?php echo $restraintRate !== null ? number_format($restraintRate, 2) : '—'; ?></td></tr>
                    </table>
                </div>
                <?php endif; ?>

                <?php if ($dataSummary['enrollment']): ?>
                <div class="resource-card" style="border-left:3px solid #06b6d4;">
                    <h4 style="margin-bottom:0.5rem;">Enrollment Demographics</h4>
                    <table style="width:100%;font-size:0.85rem;color:var(--text-muted);">
                        <tr><td>SPED (IEP)</td><td style="text-align:right;color:#fff;"><?php echo number_format((float)$dataSummary['enrollment']['sped_pct'], 1); ?>%</td></tr>
                        <tr><td>Low Income</td><td style="text-align:right;color:#fff;"><?php echo number_format((float)$dataSummary['enrollment']['low_income_pct'], 1); ?>%</td></tr>
                        <tr><td>English Learners</td><td style="text-align:right;color:#fff;"><?php echo number_format((float)$dataSummary['enrollment']['el_pct'], 1); ?>%</td></tr>
                        <tr><td>High Needs</td><td style="text-align:right;color:#fff;"><?php echo number_format((float)$dataSummary['enrollment']['high_needs_pct'], 1); ?>%</td></tr>
                    </table>
                </div>
                <?php endif; ?>

                <?php if ($dataSummary['discipline']): ?>
                <div class="resource-card" style="border-left:3px solid #f59e0b;">
                    <h4 style="margin-bottom:0.5rem;">Student Discipline</h4>
                    <table style="width:100%;font-size:0.85rem;color:var(--text-muted);">
                        <tr><td>Students disciplined</td><td style="text-align:right;color:#fff;"><?php echo number_format((int)$dataSummary['discipline']['students_disciplined']); ?></td></tr>
                        <tr><td>Out-of-school susp.</td><td style="text-align:right;color:#fff;"><?php echo number_format((float)$dataSummary['discipline']['pct_out_school_susp'], 1); ?>%</td></tr>
                        <tr><td>In-school susp.</td><td style="text-align:right;color:#fff;"><?php echo number_format((float)$dataSummary['discipline']['pct_in_school_susp'], 1); ?>%</td></tr>
                    </table>
                </div>
                <?php endif; ?>

                <?php if ($dataSummary['attendance']): ?>
                <div class="resource-card" style="border-left:3px solid #10b981;">
                    <h4 style="margin-bottom:0.5rem;">Attendance</h4>
                    <table style="width:100%;font-size:0.85rem;color:var(--text-muted);">
                        <tr><td>Attendance rate</td><td style="text-align:right;color:#fff;"><?php echo number_format((float)$dataSummary['attendance']['attendance_rate'], 1); ?>%</td></tr>
                        <tr><td>Absent 10+ days</td><td style="text-align:right;color:#fff;"><?php echo number_format((float)$dataSummary['attendance']['absent_10_plus_pct'], 1); ?>%</td></tr>
                        <tr><td>Chronically absent</td><td style="text-align:right;color:#fff;"><?php echo number_format((float)$dataSummary['attendance']['chronically_absent_10_pct'], 1); ?>%</td></tr>
                    </table>
                </div>
                <?php endif; ?>

            </div>
            <p style="color:var(--text-muted);font-size:0.8rem;margin-top:0.5rem;">
                Data sourced from DESE 2024-25 profiles. <a href="/data/?tab=compare" style="color:var(--accent-glow);">Compare against other districts →</a>
            </p>
        </div>
        <?php endif; ?>

        <!-- Cases -->
        <?php if (!empty($cases)): ?>
            <div class="district-section" data-animate>
                <h2 class="section-title" style="font-size:1.5rem;margin-bottom:1rem;">Cases</h2>
                <div class="cases-grid">
                    <?php foreach ($cases as $case): ?>
                        <div class="case-card">
                            <div class="case-card-header">
                                <div class="case-district"><?php echo h($case['district_code']); ?>, MA</div>
                                <?php echo status_badge($case['status']); ?>
                            </div>
                            <div class="case-card-id"><?php echo h($case['case_id']); ?></div>
                            <h3 class="case-card-title"><?php echo h($case['title']); ?></h3>
                            <p class="case-card-summary"><?php echo h(truncate($case['summary'] ?: '', 120)); ?></p>
                            <a href="/cases/<?php echo h($case['case_id']); ?>" class="case-card-btn">View Details</a>
                        </div>
                    <?php endforeach; ?>
                </div>
            </div>
        <?php endif; ?>

        <!-- Articles -->
        <?php if (!empty($articles)): ?>
            <div class="district-section" data-animate>
                <h2 class="section-title" style="font-size:1.5rem;margin-bottom:1rem;">Related Articles</h2>
                <div class="articles-grid" style="grid-template-columns:repeat(3, minmax(0, 1fr));">
                    <?php foreach ($articles as $a): ?>
                        <article class="article-card">
                            <div class="article-card-body">
                                <div class="article-card-meta">
                                    <span class="article-category"><?php echo category_label($a['category']); ?></span>
                                    <span class="article-date"><?php echo format_date($a['published_at']); ?></span>
                                </div>
                                <h3 class="article-card-title">
                                    <a href="/articles/<?php echo h($a['slug']); ?>"><?php echo h($a['title']); ?></a>
                                </h3>
                            </div>
                        </article>
                    <?php endforeach; ?>
                </div>
            </div>
        <?php endif; ?>

        <!-- Speeches -->
        <?php if (!empty($speeches)): ?>
            <div class="district-section" data-animate>
                <h2 class="section-title" style="font-size:1.5rem;margin-bottom:1rem;">Speeches &amp; Media</h2>
                <div class="speeches-grid-mini">
                    <?php foreach ($speeches as $s): ?>
                        <div class="speech-card-mini">
                            <h4><?php echo h($s['title']); ?></h4>
                            <p class="speech-date"><?php echo format_date($s['published_at']); ?></p>
                            <a href="<?php echo h($s['url']); ?>" target="_blank" rel="noopener" class="resource-link">Watch</a>
                        </div>
                    <?php endforeach; ?>
                </div>
            </div>
        <?php endif; ?>

        <div style="margin-top:2rem;" data-animate>
            <a href="/districts/" class="btn btn-ghost">&larr; All Districts</a>
        </div>
    </div>
</section>

<?php include __DIR__ . '/../includes/footer.php'; ?>

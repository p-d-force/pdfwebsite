<?php

declare(strict_types=1);

require_once __DIR__ . '/../config.php';

require_once __DIR__ . '/../includes/Database.php';

require_once __DIR__ . '/../includes/helpers.php';



$page_title       = 'Data Portal';

$page_description = 'Interactive exploration of DESE data across Massachusetts public schools — restraint, discipline, enrollment, attendance, and more.';



// Check which datasets have data

$hasRestraint = false;

$hasDiscipline = false;

$hasEnrollment = false;

$years   = [];

$districts = [];

$datasetCounts = [

    'restraint' => 0,

    'discipline' => 0,

    'enrollment' => 0,

    'attendance' => 0,

    'sped' => 0,

    'prs' => 0,

];



try {

    $hasRestraint = (bool)Database::fetchColumn("SELECT COUNT(*) FROM restraint_data LIMIT 1");

    if ($hasRestraint) {

        $datasetCounts['restraint'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM restraint_data WHERE is_summary_row = 0");

        $years = Database::fetchAll("SELECT DISTINCT school_year FROM restraint_data WHERE is_summary_row = 0 ORDER BY school_year DESC");

        $districts = Database::fetchAll("SELECT DISTINCT district_code, district_name FROM restraint_data WHERE is_summary_row = 0 AND district_code != '' ORDER BY district_name");

    }

} catch (Exception $e) {

    $hasRestraint = false;

}



try { $datasetCounts['discipline'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM discipline_data LIMIT 1"); } catch (Exception $e) {}

try { $datasetCounts['enrollment'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM enrollment_data LIMIT 1"); } catch (Exception $e) {}

try { $datasetCounts['attendance'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM attendance_data LIMIT 1"); } catch (Exception $e) {}

try { $datasetCounts['sped'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM sped_results LIMIT 1"); } catch (Exception $e) {}

try { $datasetCounts['prs'] = (int)Database::fetchColumn("SELECT COUNT(*) FROM prs_data LIMIT 1"); } catch (Exception $e) {}



// Determine which tab is active

$activeTab = $_GET['tab'] ?? 'portal';



include __DIR__ . '/../includes/head.php';

include __DIR__ . '/../includes/header.php';

?>



<section class="section" id="data-browser">

    <div class="container">

        <div class="section-header" data-animate>

            <span class="section-tag">Data &amp; Analytics</span>

            <h2 class="section-title">Data Portal</h2>

            <p class="section-subtitle">

                Interactive exploration of DESE data across all Massachusetts public schools. Multiple datasets available — restraint, discipline, enrollment, attendance, and more.

            </p>

        </div>



        <?php if ($activeTab !== 'portal'): ?>

        <div class="data-browser-tabs" data-animate>

            <a href="?tab=portal" class="data-tab">← Data Portal</a>

            <a href="?tab=restraint" class="data-tab<?php echo $activeTab === 'restraint' ? ' active' : ''; ?>">Restraint Data</a>

            <a href="?tab=trends" class="data-tab<?php echo $activeTab === 'trends' ? ' active' : ''; ?>">Statewide Trends</a>

            <a href="?tab=compare" class="data-tab<?php echo $activeTab === 'compare' ? ' active' : ''; ?>">Compare Districts</a>

            <a href="?tab=more" class="data-tab<?php echo $activeTab === 'more' ? ' active' : ''; ?>">More Data</a>

        </div>

        <?php endif; ?>



<?php if ($activeTab === 'portal'): ?>

        <!-- ===== DATA PORTAL HUB ===== -->

        <div class="data-tab-content active" data-animate>


            <div class="data-browser-intro">

                <h3>Explore Our Datasets</h3>

                <p>

                    All data sourced directly from the <a href="https://profiles.doe.mass.edu/" target="_blank" rel="noopener" style="color:var(--accent-glow);">Massachusetts DESE Profiles</a> website.

                    Select a dataset below to explore in detail.

                </p>

            </div>



            <div class="resources-grid" style="margin-top:1.5rem;">

                <!-- Restraint Data Card -->

                <article class="resource-card" style="border-left: 3px solid var(--accent);">

                    <h3 class="resource-title"><?php echo $hasRestraint ? '&#x2705; ' : ''; ?>Student Restraint &amp; Seclusion</h3>

                    <p class="resource-excerpt">

                        <?php if ($hasRestraint): ?>

                            <?php echo number_format($datasetCounts['restraint']); ?> school-level records across <?php echo count($years); ?> school years, <?php echo count($districts); ?> districts. Track physical restraints, injuries, and suppression patterns.

                        <?php else: ?>

                            Physical restraint and seclusion data reported by all MA public schools. Includes student counts, injury totals, and per-100 rates.

                        <?php endif; ?>

                    </p>

                    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">

                        <a href="?tab=restraint" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">Explore Restraint Data</a>

                        <a href="?tab=trends" class="btn btn-ghost" style="font-size:0.85rem;padding:0.4rem 0.8rem;">View Trends</a>

                        <a href="?tab=compare" class="btn btn-ghost" style="font-size:0.85rem;padding:0.4rem 0.8rem;">Compare Districts</a>

                    </div>

                </article>



                <!-- Discipline Data Card -->

                <article class="resource-card" style="border-left: 3px solid #f59e0b;">

                    <h3 class="resource-title"><?php echo $datasetCounts['discipline'] > 0 ? '&#x2705; ' : '&#x1F6E0; '; ?>Student Discipline</h3>

                    <p class="resource-excerpt">

                        <?php if ($datasetCounts['discipline'] > 0): ?>

                            <?php echo number_format($datasetCounts['discipline']); ?> records. Suspensions, expulsions, and disciplinary actions by district, school, and demographic group.

                        <?php else: ?>

                            Suspension rates, expulsion data, and disciplinary actions broken down by district, school, and demographic subgroup.

                        <?php endif; ?>

                    </p>

                    <div style="display:flex;gap:0.5rem;">

                        <a href="?tab=compare" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">View Comparison</a>

                    </div>

                </article>



                <!-- Enrollment Data Card -->

                <article class="resource-card" style="border-left: 3px solid #06b6d4;">

                    <h3 class="resource-title"><?php echo $datasetCounts['enrollment'] > 0 ? '&#x2705; ' : '&#x1F6E0; '; ?>Enrollment Demographics</h3>

                    <p class="resource-excerpt">

                        <?php if ($datasetCounts['enrollment'] > 0): ?>

                            <?php echo number_format($datasetCounts['enrollment']); ?> records. Enrollment by SPED status, economic disadvantage, English learner, and high-needs across all MA districts.

                        <?php else: ?>

                            District-level enrollment data by grade, gender, race/ethnicity, special education status, and economic disadvantage.

                        <?php endif; ?>

                    </p>

                    <div style="display:flex;gap:0.5rem;">

                        <a href="?tab=compare" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">View Comparison</a>

                    </div>

                </article>



                <!-- Attendance Card -->

                <article class="resource-card" style="border-left: 3px solid #10b981;">

                    <h3 class="resource-title"><?php echo $datasetCounts['attendance'] > 0 ? '&#x2705; ' : '&#x1F6E0; '; ?>Attendance &amp; Chronic Absenteeism</h3>

                    <p class="resource-excerpt">

                        <?php if ($datasetCounts['attendance'] > 0): ?>

                            <?php echo number_format($datasetCounts['attendance']); ?> records. Attendance rates and chronic absenteeism by district. Compare alongside restraint and discipline data in the comparison tool.

                        <?php else: ?>

                            Attendance rates and chronic absenteeism data by district.

                        <?php endif; ?>

                    </p>

                    <div style="display:flex;gap:0.5rem;">

                        <a href="?tab=compare" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">View Comparison</a>

                    </div>

                </article>



                <!-- SPED Results Card -->

                <article class="resource-card" style="border-left: 3px solid #8b5cf6;">

                    <h3 class="resource-title">&#x1F6E0; Special Education Outcomes</h3>

                    <p class="resource-excerpt">

                        Graduation rates, dropout rates, and inclusion percentages for students with IEPs. Compare SPED outcomes against general education populations.

                    </p>

                    <div style="display:flex;gap:0.5rem;">

                        <span class="btn btn-ghost" style="font-size:0.85rem;padding:0.4rem 0.8rem;opacity:0.5;">Coming Soon</span>

                    </div>

                </article>



                <!-- PRS Tracker Card -->

                <article class="resource-card" style="border-left: 3px solid #ec4899;">

                    <h3 class="resource-title">&#x1F6E0; PRS Complaint Tracker</h3>

                    <p class="resource-excerpt">

                        Problem Resolution System complaints tracked across districts. Monitor complaint types, outcomes, timelines, and systemic patterns.

                    </p>

                    <div style="display:flex;gap:0.5rem;">

                        <span class="btn btn-ghost" style="font-size:0.85rem;padding:0.4rem 0.8rem;opacity:0.5;">Coming Soon</span>

                    </div>

                </article>



                <!-- Public Records Card -->

                <article class="resource-card" style="border-left: 3px solid #ef4444;">

                    <h3 class="resource-title">&#x1F6E0; Public Records Tracker</h3>

                    <p class="resource-excerpt">

                        Gantt timeline of all public records requests filed across tracked districts. See response times, compliance rates, and 10-day deadline violations.

                    </p>

                    <div style="display:flex;gap:0.5rem;">

                        <span class="btn btn-ghost" style="font-size:0.85rem;padding:0.4rem 0.8rem;opacity:0.5;">Coming Soon</span>

                    </div>

                </article>



                <!-- Data Comparison Card -->

                <article class="resource-card" style="border-left: 3px solid var(--accent-glow);background:rgba(255,90,31,0.05);">

                    <h3 class="resource-title">&#x1F4CA; Cross-Dataset Comparison</h3>

                    <p class="resource-excerpt">

                        Compare restraint rates against enrollment, discipline rates, attendance, and SPED outcomes. Identify correlations and systemic patterns across datasets.

                    </p>

                    <div style="display:flex;gap:0.5rem;">

                        <a href="?tab=compare" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">Compare Districts</a>

                    </div>

                </article>

            </div>

        </div>



<?php elseif ($activeTab === 'restraint'): ?>

        <!-- ===== RESTRAINT DATA EXPLORER ===== -->

        <div class="data-tab-content active" data-animate>

            <div class="data-browser-intro">

                <h3>Student Restraint Records — All Massachusetts Public Schools</h3>

                <p>

                    Data sourced live from the <a href="https://profiles.doe.mass.edu/statereport/restraints.aspx" target="_blank" rel="noopener" style="color:var(--accent-glow);">DESE Profiles website</a>.

                    <?php if ($hasRestraint): ?>

                        Currently showing <?php echo number_format($datasetCounts['restraint']); ?> school-level records across <?php echo count($years); ?> school years.

                    <?php endif; ?>

                </p>

                <p style="color:var(--text-muted);font-size:0.85rem;">

                    <strong>Suppression rule:</strong> Cells are suppressed (dash) when fewer than 6 students were restrained or 

                    injuries are between 1 and 5. Suppressed rows are excluded from rate calculations.

                    Schools with zero reported restraints are not listed by DESE.

                </p>

            </div>



            <?php if ($hasRestraint): ?>

                <div class="data-controls" data-table-controls data-target-table="restraint-body">

                    <div class="data-control-row" style="margin-bottom:0.6rem;">

                        <input type="text" class="form-input" data-table-search placeholder="Filter by school, district, or year..." style="max-width:380px;">

                        <span class="datatable-count" data-table-count></span>

                    </div>

                    <div class="data-control-row">

                        <select class="repo-select" data-table-filter-key="year" data-table-populate onchange="this.form && this.form.dispatchEvent(new Event('input',{bubbles:true}))">

                            <option value="all">All Years</option>

                        </select>

                        <select class="repo-select" data-table-filter-key="district" data-table-populate onchange="this.form && this.form.dispatchEvent(new Event('input',{bubbles:true}))">

                            <option value="all">All Districts</option>

                        </select>

                    </div>

                </div>



                <div class="repo-table-wrapper">

                    <table class="repo-table" id="restraint-body">

                        <thead>

                            <tr>

                                <th>Year</th>

                                <th>District</th>

                                <th>School</th>

                                <th>Enrollment</th>

                                <th>Students Restrained</th>

                                <th>Total Restraints</th>

                                <th>Injuries</th>

                                <th>Rate / 100</th>

                                <th>Inj. / Restraint</th>

                            </tr>

                        </thead>

                        <tbody>

                            <?php

                            $allRows = Database::fetchAll(

                                "SELECT * FROM restraint_data WHERE is_summary_row = 0

                                 ORDER BY school_year DESC, restraint_rate_per_100 DESC

                                 LIMIT 500"

                            );

                            foreach ($allRows as $r):

                                $rate = $r['restraint_rate_per_100'] !== null ? number_format((float)$r['restraint_rate_per_100'], 2) : '—';

                                $ipr  = $r['injuries_per_restraint'] !== null ? number_format((float)$r['injuries_per_restraint'], 3) : '—';

                                $stu  = $r['students_restrained_suppressed'] ? '<6' : number_format((int)$r['students_restrained']);

                                $tot  = $r['total_restraints_suppressed'] ? '—' : number_format((int)$r['total_restraints']);

                                $inj  = $r['total_injuries_suppressed'] ? '—' : number_format((int)$r['total_injuries']);

                            ?>

                                <tr

                                    data-search="<?php echo h(strtolower($r['school_year'] . ' ' . $r['district_name'] . ' ' . $r['school_name'])); ?>"

                                    data-year="<?php echo h($r['school_year']); ?>"

                                    data-district="<?php echo h($r['district_name']); ?>"

                                    data-district-label="<?php echo h($r['district_name']); ?>"

                                >

                                    <td><?php echo h($r['school_year']); ?></td>

                                    <td><?php echo h($r['district_name']); ?></td>

                                    <td><?php echo h($r['school_name']); ?></td>

                                    <td><?php echo number_format((int)$r['enrollment']); ?></td>

                                    <td><?php echo $stu; ?></td>

                                    <td><?php echo $tot; ?></td>

                                    <td><?php echo $inj; ?></td>

                                    <td><?php echo $rate; ?></td>

                                    <td><?php echo $ipr; ?></td>

                                </tr>

                            <?php endforeach; ?>

                        </tbody>

                    </table>

                </div>



                <p style="color:var(--text-muted);font-size:0.8rem;margin-top:0.5rem;">

                    Showing first 500 rows. Use the filters above to narrow results. Full dataset available covering <?php echo count($years); ?> school years.

                </p>

            <?php else: ?>

                <div class="empty-state">

                    <h3>Data Not Loaded</h3>

                    <p>The restraint data pipeline has not been populated. Contact the administrator.</p>

                </div>

            <?php endif; ?>

        </div>



<?php elseif ($activeTab === 'trends'): ?>

        <!-- ===== STATEWIDE TRENDS ===== -->

        <div class="data-tab-content active" data-animate>

            <div class="data-chart-area">

                <h3>Statewide Restraint Trends (2016–2025)</h3>

                <p style="color:var(--text-muted);margin-bottom:1rem;">

                    Computed live from <?php echo number_format($datasetCounts['restraint']); ?> school-level records across <?php echo count($years); ?> years.

                </p>

                <div style="max-width:100%;height:450px;">

                    <canvas id="restraintTrendsChart"></canvas>

                </div>

            </div>



            <?php if ($hasRestraint): ?>

                <div style="margin-top:1.5rem;">

                    <h3 style="margin-bottom:0.75rem;">Year-over-Year Statewide Totals</h3>

                    <div class="repo-table-wrapper">

                        <table class="repo-table">

                            <thead>

                                <tr>

                                    <th>Year</th>

                                    <th>Schools Reporting</th>

                                    <th>Total Restraints</th>

                                    <th>Students Restrained</th>

                                    <th>Total Injuries</th>

                                    <th>Avg Rate / 100</th>

                                </tr>

                            </thead>

                            <tbody>

                                <?php

                                $trends = Database::fetchAll(

                                    "SELECT school_year, COUNT(*) as school_count,

                                        COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN total_restraints ELSE 0 END), 0) as sum_restraints,

                                        COALESCE(SUM(CASE WHEN students_restrained_suppressed = 0 THEN students_restrained ELSE 0 END), 0) as sum_students,

                                        COALESCE(SUM(CASE WHEN total_injuries_suppressed = 0 THEN total_injuries ELSE 0 END), 0) as sum_injuries,

                                        COALESCE(SUM(CASE WHEN total_restraints_suppressed = 0 THEN enrollment ELSE 0 END), 0) as sum_enrollment

                                     FROM restraint_data

                                     WHERE is_summary_row = 0

                                     GROUP BY school_year

                                     ORDER BY school_year DESC"

                                );

                                foreach ($trends as $agg):

                                    $avgRate = $agg['sum_enrollment'] > 0 && $agg['sum_restraints'] > 0

                                        ? number_format(($agg['sum_restraints'] / $agg['sum_enrollment']) * 100, 2)

                                        : '—';

                                ?>

                                    <tr>

                                        <td><strong><?php echo h($agg['school_year']); ?></strong></td>

                                        <td><?php echo number_format((int)$agg['school_count']); ?></td>

                                        <td><?php echo number_format((int)$agg['sum_restraints']); ?></td>

                                        <td><?php echo number_format((int)$agg['sum_students']); ?></td>

                                        <td><?php echo number_format((int)$agg['sum_injuries']); ?></td>

                                        <td><?php echo $avgRate; ?></td>

                                    </tr>

                                <?php endforeach; ?>

                            </tbody>

                        </table>

                    </div>

                </div>

            <?php endif; ?>

        </div>



<?php elseif ($activeTab === 'compare'): ?>

        <!-- ===== CROSS-DATASET COMPARISON ===== -->

        <div class="data-tab-content active" data-animate>
            <?php include __DIR__ . '/compare-panel.php'; ?>

            <div class="data-browser-intro">

                <h3>Cross-Dataset District Comparison (2024-25)</h3>

                <p>

                    Restraint data alongside enrollment demographics, discipline rates, and attendance — all sourced from DESE. Find correlations between physical restraint usage and other district characteristics.

                </p>

            </div>



            <?php

            // Try to build enriched cross-dataset comparison

            $hasEnrollment = false;

            try { $hasEnrollment = (bool)Database::fetchColumn("SELECT COUNT(*) FROM enrollment_data LIMIT 1"); } catch (Exception $e) {}

            $hasDiscipline = false;

            try { $hasDiscipline = (bool)Database::fetchColumn("SELECT COUNT(*) FROM discipline_data LIMIT 1"); } catch (Exception $e) {}



            if ($hasRestraint && $hasEnrollment):

                // Build enriched comparison from restraint + enrollment + discipline

                $compareRows = Database::fetchAll(

                    "SELECT r.district_name, r.district_code,

                        COUNT(DISTINCT r.school_name) as school_count,

                        COALESCE(SUM(CASE WHEN r.total_restraints_suppressed = 0 THEN r.total_restraints ELSE 0 END), 0) as sum_restraints,

                        COALESCE(SUM(CASE WHEN r.students_restrained_suppressed = 0 THEN r.students_restrained ELSE 0 END), 0) as sum_students,

                        COALESCE(SUM(CASE WHEN r.total_injuries_suppressed = 0 THEN r.total_injuries ELSE 0 END), 0) as sum_injuries,

                        COALESCE(SUM(CASE WHEN r.total_restraints_suppressed = 0 THEN r.enrollment ELSE 0 END), 0) as sum_enrollment

                     FROM restraint_data r

                     WHERE r.is_summary_row = 0 AND r.school_year = '2024-25' AND r.district_name != 'State Total'

                     GROUP BY r.district_name, r.district_code

                     HAVING sum_restraints > 50

                     ORDER BY sum_restraints DESC

                     LIMIT 30"

                );



                // Pre-fetch enrollment and discipline lookups

            ?>

                <div style="background:var(--bg-elevated);border-radius:12px;padding:1.5rem;margin-top:1rem;overflow-x:auto;">

                    <h4 style="margin-bottom:1rem;">Restraint vs Enrollment vs Discipline — Top 30 Districts by Total Restraints</h4>

                    <div class="repo-table-wrapper">

                        <table class="repo-table" style="font-size:0.82rem;">

                            <thead>

                                <tr>

                                    <th>District</th>

                                    <th>Restraints</th>

                                    <th>Rate/100</th>

                                    <th>District Size</th>

                                    <th>SPED %</th>

                                    <th>Low Income %</th>

                                    <th>EL %</th>

                                    <?php if ($hasDiscipline): ?><th>OSS %</th><?php endif; ?>

                                    <th>Attendance</th>

                                    <th>Chr. Absent%</th>

                                </tr>

                            </thead>

                            <tbody>

                                <?php foreach ($compareRows as $cr):

                                    $crate = $cr['sum_enrollment'] > 0 ? number_format(($cr['sum_restraints'] / $cr['sum_enrollment']) * 100, 2) : '—';



                                    // Lookup enrollment demographics

                                    $enr = Database::fetch(

                                        "SELECT sped_pct, low_income_pct, el_pct, high_needs_num

                                         FROM enrollment_data

                                         WHERE district_name = ? AND school_year = '2024-25' LIMIT 1",

                                        [$cr['district_name']]

                                    );



                                    // Lookup discipline

                                    $disc = null;

                                    if ($hasDiscipline) {

                                        $disc = Database::fetch(

                                            "SELECT students, pct_out_school_susp

                                             FROM discipline_data

                                             WHERE district_name = ? AND school_year = '2024-25' LIMIT 1",

                                            [$cr['district_name']]

                                        );

                                    }



                                    // Lookup attendance

                                    $att = Database::fetch(

                                        "SELECT attendance_rate, chronically_absent_10_pct

                                         FROM attendance_data

                                         WHERE district_name = ? AND school_year = '2024-25' LIMIT 1",

                                        [$cr['district_name']]

                                    );



                                    $sped = $enr['sped_pct'] ?? null;

                                    $lowInc = $enr['low_income_pct'] ?? null;

                                    $el = $enr['el_pct'] ?? null;

                                    $districtSize = $disc['students'] ?? $cr['sum_enrollment'];

                                    $oss = $disc['pct_out_school_susp'] ?? null;

                                    $attend = $att['attendance_rate'] ?? null;

                                    $chronic = $att['chronically_absent_10_pct'] ?? null;



                                    // County lookup

                                    $town = strtolower(explode(' ', $cr['district_name'])[0]);

                                    $countyMap = [

                                        'attleboro' => 'Bristol', 'fall' => 'Bristol', 'bridgewater' => 'Plymouth',

                                        'whitman' => 'Plymouth', 'norton' => 'Bristol', 'boston' => 'Suffolk',

                                        'springfield' => 'Hampden', 'worcester' => 'Worcester', 'lowell' => 'Middlesex',

                                        'lawrence' => 'Essex', 'pittsfield' => 'Berkshire',

                                        'holyoke' => 'Hampden', 'brockton' => 'Plymouth', 'newton' => 'Middlesex',

                                        'framingham' => 'Middlesex', 'somerville' => 'Middlesex', 'malden' => 'Middlesex',

                                        'westfield' => 'Hampden', 'beverly' => 'Essex', 'somerset' => 'Bristol',

                                        'wilmington' => 'Middlesex', 'weymouth' => 'Norfolk', 'braintree' => 'Norfolk',

                                    ];

                                    $county = $countyMap[$town] ?? '';

                                ?>

                                    <tr>

                                        <td>

                                            <strong><?php echo h($cr['district_name']); ?></strong>

                                            <?php if ($county): ?><br><span style="font-size:0.7rem;color:var(--text-muted);"><?php echo h($county); ?> Co.</span><?php endif; ?>

                                        </td>

                                        <td><?php echo number_format((int)$cr['sum_restraints']); ?></td>

                                        <td style="color:var(--accent-glow);font-weight:600;"><?php echo $crate; ?></td>

                                        <td><?php echo $districtSize > 0 ? number_format((int)$districtSize) : '—'; ?></td>

                                        <td><?php echo $sped !== null ? number_format((float)$sped, 1) . '%' : '—'; ?></td>

                                        <td><?php echo $lowInc !== null ? number_format((float)$lowInc, 1) . '%' : '—'; ?></td>

                                        <td><?php echo $el !== null ? number_format((float)$el, 1) . '%' : '—'; ?></td>

                                        <?php if ($hasDiscipline): ?><td><?php echo $oss !== null ? number_format((float)$oss, 1) . '%' : '—'; ?></td><?php endif; ?>

                                        <td><?php echo $attend !== null ? number_format((float)$attend, 1) . '%' : '—'; ?></td>

                                        <td><?php echo $chronic !== null ? number_format((float)$chronic, 1) . '%' : '—'; ?></td>

                                    </tr>

                                <?php endforeach; ?>

                            </tbody>

                        </table>

                    </div>



                    <p style="color:var(--text-muted);font-size:0.85rem;margin-top:0.75rem;">

                        <strong>Columns:</strong> Restraints = total physical restraints. Rate = restraints per 100 enrolled (schools with restraint data). SPED% = students with IEPs. Low Income% = economically disadvantaged. EL% = English Learners. OSS% = out-of-school suspension rate. Attendance = average daily attendance rate. Chr. Absent% = chronically absent (10+ days). All data from DESE 2024-25.

                    </p>

                </div>

            <?php else: ?>

                <div class="empty-state">

                    <h3>Comparison Data Loading</h3>

                    <p>Enrollment and discipline data required for cross-dataset comparison.</p>

                </div>

            <?php endif; ?>

        </div>



<?php else: ?>

        <!-- ===== MORE DATA COMING ===== -->

        <div class="data-tab-content active" data-animate>

            <div class="empty-state">

                <h3>More Datasets Coming</h3>

                <p>Additional datasets — including public records request response analytics, district compliance comparisons, and cross-district pattern analysis — will be added as data pipelines are activated.</p>

                <p style="margin-top:0.5rem;">Have data to contribute? <a href="/submit/#upload" style="color:var(--accent-glow);">Upload it here.</a></p>

            </div>

        </div>

<?php endif; ?>

    </div>

</section>



<?php include __DIR__ . '/../includes/footer.php'; ?>


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
            <a href="?tab=restraint" class="data-tab<?= $activeTab === 'restraint' ? ' active' : '' ?>">Restraint Data</a>
            <a href="?tab=trends" class="data-tab<?= $activeTab === 'trends' ? ' active' : '' ?>">Statewide Trends</a>
            <a href="?tab=compare" class="data-tab<?= $activeTab === 'compare' ? ' active' : '' ?>">Compare Districts</a>
            <a href="?tab=more" class="data-tab<?= $activeTab === 'more' ? ' active' : '' ?>">More Data</a>
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
                    <h3 class="resource-title"><?= $datasetCounts['restraint'] > 0 ? '&#x2705; ' : '' ?>Student Restraint &amp; Seclusion</h3>
                    <p class="resource-excerpt">
                        <?php if ($datasetCounts['restraint'] > 0): ?>
                            <?= number_format($datasetCounts['restraint']) ?> school-level records across multiple school years. Track physical restraints, injuries, and suppression patterns.
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
                    <h3 class="resource-title"><?= $datasetCounts['discipline'] > 0 ? '&#x2705; ' : '&#x1F6E0; ' ?>Student Discipline</h3>
                    <p class="resource-excerpt">
                        <?php if ($datasetCounts['discipline'] > 0): ?>
                            <?= number_format($datasetCounts['discipline']) ?> records. Suspensions, expulsions, and disciplinary actions by district, school, and demographic group.
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
                    <h3 class="resource-title"><?= $datasetCounts['enrollment'] > 0 ? '&#x2705; ' : '&#x1F6E0; ' ?>Enrollment Demographics</h3>
                    <p class="resource-excerpt">
                        <?php if ($datasetCounts['enrollment'] > 0): ?>
                            <?= number_format($datasetCounts['enrollment']) ?> records. Enrollment by SPED status, economic disadvantage, English learner, and high-needs across all MA districts.
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
                    <h3 class="resource-title"><?= $datasetCounts['attendance'] > 0 ? '&#x2705; ' : '&#x1F6E0; ' ?>Attendance &amp; Chronic Absenteeism</h3>
                    <p class="resource-excerpt">
                        <?php if ($datasetCounts['attendance'] > 0): ?>
                            <?= number_format($datasetCounts['attendance']) ?> records. Attendance rates and chronic absenteeism by district.
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
            </div>
        </div>
        <?php endif; ?>

        <?php if ($activeTab === 'restraint'): ?>
        <!-- ===== RESTRAINT DATA TAB ===== -->
        <div class="data-tab-content active" data-animate>
            <form method="GET" action="/data/" class="filter-bar" style="display:flex;gap:1rem;flex-wrap:wrap;align-items:end;margin-bottom:1.5rem;padding:1rem;background:var(--bg-glass);border-radius:var(--radius-md);border:1px solid var(--border);">
                <input type="hidden" name="tab" value="restraint">
                <div class="form-group" style="margin-bottom:0;">
                    <label class="form-label">School Year</label>
                    <select name="school_year" class="form-select">
                        <?php foreach ($schoolYears as $sy): ?>
                            <option value="<?= h($sy['school_year']) ?>" <?= ($restraintData['schoolYear'] ?? '') === $sy['school_year'] ? 'selected' : '' ?>><?= h($sy['school_year']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="form-group" style="margin-bottom:0;">
                    <label class="form-label">District</label>
                    <select name="district" class="form-select">
                        <option value="">All Districts</option>
                        <?php foreach ($restraintDistricts as $d): ?>
                            <option value="<?= h($d['district_code']) ?>" <?= ($restraintData['districtCode'] ?? '') === $d['district_code'] ? 'selected' : '' ?>><?= h($d['district_name']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">Filter</button>
            </form>

            <?php if ($restraintData && !empty($restraintData['rows'])): ?>
                <div style="overflow-x:auto;">
                    <table class="data-table" style="width:100%;border-collapse:collapse;">
                        <thead>
                            <tr>
                                <th>District</th>
                                <th>School</th>
                                <th>Total Restraints</th>
                                <th>Students Restrained</th>
                                <th>Injuries</th>
                                <th>Enrollment</th>
                                <th>Rate per 100</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($restraintData['rows'] as $row):
                                $enrollment = (int)($row['enrollment'] ?? 0);
                                $totalRestraints = (int)($row['total_restraints'] ?? 0);
                                $rate = $enrollment > 0 ? round(($totalRestraints / $enrollment) * 100, 1) : null;
                            ?>
                            <tr>
                                <td><?= h($row['district_name']) ?></td>
                                <td><?= h($row['school_name']) ?><?= ($row['total_restraints_suppressed'] ?? 0) ? ' <span title="Data suppressed" style="color:var(--text-muted);font-size:0.75rem;">*</span>' : '' ?></td>
                                <td><?= number_format($totalRestraints) ?></td>
                                <td><?= number_format((int)($row['students_restrained'] ?? 0)) ?></td>
                                <td><?= number_format((int)($row['total_injuries'] ?? 0)) ?></td>
                                <td><?= number_format($enrollment) ?></td>
                                <td><?= $rate !== null ? $rate : '—' ?></td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
                <p style="color:var(--text-muted);margin-top:0.75rem;">Showing <?= count($restraintData['rows']) ?> schools<?= ($restraintData['districtCode'] ?? '') ? ' in selected district' : '' ?>.</p>
            <?php elseif ($activeTab === 'restraint'): ?>
                <div class="empty-state">
                    <h3>No restraint data found</h3>
                    <p>Try selecting a different school year or district.</p>
                </div>
            <?php endif; ?>
        </div>
        <?php endif; ?>

        <?php if ($activeTab === 'trends'): ?>
        <!-- ===== STATEWIDE TRENDS TAB ===== -->
        <div class="data-tab-content active" data-animate>
            <div class="restraint-charts">
                <div class="restraint-chart-card" style="min-height:400px;">
                    <h3 class="restraint-chart-title">Statewide Restraint Trends</h3>
                    <div class="restraint-info-box" style="margin-bottom:1rem;">
                        <strong>Multi-year restraint and injury data</strong> — aggregated across all Massachusetts public schools. Each bar shows total restraints; the line shows total injuries.
                    </div>
                    <div style="position:relative;height:400px;">
                        <canvas id="restraintTrendsChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        <?php endif; ?>

        <?php if ($activeTab === 'compare'): ?>
        <div class="data-tab-content active" data-animate>
            <p><a href="/compare" class="btn btn-primary">Open Full Comparison Tool</a></p>
        </div>
        <?php endif; ?>

        <?php if ($activeTab === 'more'): ?>
        <div class="data-tab-content active" data-animate>
            <div class="resources-grid" style="margin-top:1rem;">
                <article class="resource-card" style="border-left: 3px solid var(--accent);">
                    <h3 class="resource-title">Restraint Data Browser</h3>
                    <p class="resource-excerpt">Full restraint &amp; seclusion data with filters, pagination, and search.</p>
                    <a href="/data/restraint" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">Browse Data</a>
                </article>
                <article class="resource-card" style="border-left: 3px solid #ec4899;">
                    <h3 class="resource-title">PRS Intake Browser</h3>
                    <p class="resource-excerpt">Problem Resolution System intake data with status and outcome tracking.</p>
                    <a href="/data/prs" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">Browse PRS Data</a>
                </article>
                <article class="resource-card" style="border-left: 3px solid #f59e0b;">
                    <h3 class="resource-title">Discipline Browser</h3>
                    <p class="resource-excerpt">Student discipline data by district, school, and demographic group.</p>
                    <a href="/data/discipline" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">Browse Data</a>
                </article>
                <article class="resource-card" style="border-left: 3px solid #06b6d4;">
                    <h3 class="resource-title">Enrollment Browser</h3>
                    <p class="resource-excerpt">Enrollment demographics including SPED, EL, and low-income percentages.</p>
                    <a href="/data/enrollment" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">Browse Data</a>
                </article>
                <article class="resource-card" style="border-left: 3px solid #10b981;">
                    <h3 class="resource-title">Attendance Browser</h3>
                    <p class="resource-excerpt">Attendance rates and chronic absenteeism data by district.</p>
                    <a href="/data/attendance" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">Browse Data</a>
                </article>
                <article class="resource-card" style="border-left: 3px solid #8b5cf6;">
                    <h3 class="resource-title">SPED Results Browser</h3>
                    <p class="resource-excerpt">Special education outcomes — graduation rates, dropout rates, inclusion data.</p>
                    <a href="/data/sped-results" class="btn btn-primary" style="font-size:0.85rem;padding:0.4rem 0.8rem;">Browse Data</a>
                </article>
            </div>
        </div>
        <?php endif; ?>
    </div>
</section>

<section class="section">
    <div class="container">
        <div class="section-header">
            <span class="section-tag">Data &amp; Analytics</span>
            <h2 class="section-title">Restraint Data Browser</h2>
            <p class="section-subtitle">Full restraint &amp; seclusion data with school year filters, search, and pagination.</p>
        </div>

        <div style="display:flex;gap:1rem;flex-wrap:wrap;align-items:end;margin-bottom:1.5rem;padding:1rem;background:var(--bg-glass);border-radius:var(--radius-md);border:1px solid var(--border);">
            <div class="form-group" style="margin-bottom:0;">
                <label class="form-label">School Year</label>
                <select onchange="window.location='?school_year='+this.value<?= $search ? '+' . urlencode($search) : '' ?>" class="form-select">
                    <?php foreach ($schoolYears as $sy): ?>
                        <option value="<?= h($sy['school_year']) ?>" <?= $schoolYear === $sy['school_year'] ? 'selected' : '' ?>><?= h($sy['school_year']) ?></option>
                    <?php endforeach; ?>
                </select>
            </div>
            <form method="GET" style="display:flex;gap:0.5rem;align-items:end;">
                <input type="hidden" name="school_year" value="<?= h($schoolYear) ?>">
                <div class="form-group" style="margin-bottom:0;">
                    <label class="form-label">Search Schools</label>
                    <input type="text" name="search" class="form-input" value="<?= h($search) ?>" placeholder="School or district name...">
                </div>
                <button type="submit" class="btn btn-primary">Search</button>
            </form>
        </div>

        <?php if (empty($rows)): ?>
            <div class="empty-state"><h3>No results</h3><p>Try a different search or school year.</p></div>
        <?php else: ?>
            <p style="color:var(--text-muted);margin-bottom:1rem;">Showing <?= count($rows) ?> of <?= number_format($total) ?> records.</p>
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
                            <th>Rate/100</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($rows as $r):
                            $enr = (int)($r['enrollment'] ?? 0);
                            $tr = (int)($r['total_restraints'] ?? 0);
                        ?>
                        <tr>
                            <td><?= h($r['district_name']) ?></td>
                            <td><?= h($r['school_name']) ?><?= ($r['total_restraints_suppressed'] ?? 0) ? ' *' : '' ?></td>
                            <td><?= number_format($tr) ?></td>
                            <td><?= number_format((int)($r['students_restrained'] ?? 0)) ?></td>
                            <td><?= number_format((int)($r['total_injuries'] ?? 0)) ?></td>
                            <td><?= number_format($enr) ?></td>
                            <td><?= $enr > 0 ? round(($tr / $enr) * 100, 1) : '—' ?></td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            <?php if ($total > $perPage): ?>
                <?php $pages = (int)ceil($total / $perPage); ?>
                <nav style="margin-top:1.5rem;display:flex;gap:0.5rem;justify-content:center;">
                    <?php if ($page > 1): ?>
                        <a href="?school_year=<?= urlencode($schoolYear) ?>&page=<?= $page - 1 ?><?= $search ? '&search=' . urlencode($search) : '' ?>" class="btn btn-secondary">&laquo; Prev</a>
                    <?php endif; ?>
                    <span style="color:var(--text-muted);padding:0.5rem 1rem;">Page <?= $page ?> of <?= $pages ?></span>
                    <?php if ($page < $pages): ?>
                        <a href="?school_year=<?= urlencode($schoolYear) ?>&page=<?= $page + 1 ?><?= $search ? '&search=' . urlencode($search) : '' ?>" class="btn btn-secondary">Next &raquo;</a>
                    <?php endif; ?>
                </nav>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</section>

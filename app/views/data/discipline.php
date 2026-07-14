<section class="section">
    <div class="container">
        <div class="section-header">
            <span class="section-tag">Data &amp; Analytics</span>
            <h2 class="section-title">Discipline Data Browser</h2>
            <p class="section-subtitle">Student discipline data — suspensions, expulsions, and disciplinary actions by district.</p>
        </div>

        <form method="GET" style="display:flex;gap:1rem;flex-wrap:wrap;align-items:end;margin-bottom:1.5rem;padding:1rem;background:var(--bg-glass);border-radius:var(--radius-md);border:1px solid var(--border);">
            <div class="form-group" style="margin-bottom:0;">
                <label class="form-label">Search District</label>
                <input type="text" name="search" class="form-input" value="<?= h($search) ?>" placeholder="District name...">
            </div>
            <button type="submit" class="btn btn-primary">Filter</button>
        </form>

        <?php if (empty($rows)): ?>
            <div class="empty-state"><h3>No results</h3><p>Try a different search.</p></div>
        <?php else: ?>
            <p style="color:var(--text-muted);margin-bottom:1rem;">Showing <?= count($rows) ?> of <?= number_format($total) ?> records.</p>
            <div style="overflow-x:auto;">
                <table class="data-table" style="width:100%;border-collapse:collapse;">
                    <thead><tr><th>District</th><th>Year</th><th>Students</th><th>Disciplined</th><th>In-School %</th><th>Out-of-School %</th><th>Expulsion %</th></tr></thead>
                    <tbody>
                        <?php foreach ($rows as $r): ?>
                        <tr>
                            <td><?= h($r['district_name']) ?></td>
                            <td><?= h($r['school_year']) ?></td>
                            <td><?= number_format((int)($r['students'] ?? 0)) ?></td>
                            <td><?= number_format((int)($r['students_disciplined'] ?? 0)) ?></td>
                            <td><?= number_format((float)($r['pct_in_school_susp'] ?? 0), 1) ?>%</td>
                            <td><?= number_format((float)($r['pct_out_school_susp'] ?? 0), 1) ?>%</td>
                            <td><?= number_format((float)($r['pct_expulsion'] ?? 0), 1) ?>%</td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            <?php if ($total > $perPage): ?>
                <?php $pages = (int)ceil($total / $perPage); ?>
                <nav style="margin-top:1.5rem;display:flex;gap:0.5rem;justify-content:center;">
                    <?php if ($page > 1): ?><a href="?page=<?= $page - 1 ?><?= $search ? '&search=' . urlencode($search) : '' ?>" class="btn btn-secondary">&laquo; Prev</a><?php endif; ?>
                    <span style="color:var(--text-muted);padding:0.5rem 1rem;">Page <?= $page ?> of <?= $pages ?></span>
                    <?php if ($page < $pages): ?><a href="?page=<?= $page + 1 ?><?= $search ? '&search=' . urlencode($search) : '' ?>" class="btn btn-secondary">Next &raquo;</a><?php endif; ?>
                </nav>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</section>

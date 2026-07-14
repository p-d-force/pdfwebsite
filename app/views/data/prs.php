<section class="section">
    <div class="container">
        <div class="section-header">
            <span class="section-tag">Data &amp; Analytics</span>
            <h2 class="section-title">PRS Intake Browser</h2>
            <p class="section-subtitle">Problem Resolution System complaint intake data — search, filter by status, and browse outcomes.</p>
        </div>

        <form method="GET" style="display:flex;gap:1rem;flex-wrap:wrap;align-items:end;margin-bottom:1.5rem;padding:1rem;background:var(--bg-glass);border-radius:var(--radius-md);border:1px solid var(--border);">
            <div class="form-group" style="margin-bottom:0;">
                <label class="form-label">Search</label>
                <input type="text" name="search" class="form-input" value="<?= h($search) ?>" placeholder="District, PRS#, or category...">
            </div>
            <div class="form-group" style="margin-bottom:0;">
                <label class="form-label">Status</label>
                <select name="status" class="form-select">
                    <option value="">All</option>
                    <option value="Open" <?= $status === 'Open' ? 'selected' : '' ?>>Open</option>
                    <option value="Closed" <?= $status === 'Closed' ? 'selected' : '' ?>>Closed</option>
                    <option value="Pending" <?= $status === 'Pending' ? 'selected' : '' ?>>Pending</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary">Filter</button>
        </form>

        <?php if (empty($rows)): ?>
            <div class="empty-state"><h3>No results</h3><p>Try different filters.</p></div>
        <?php else: ?>
            <p style="color:var(--text-muted);margin-bottom:1rem;">Showing <?= count($rows) ?> of <?= number_format($total) ?> records.</p>
            <div style="overflow-x:auto;">
                <table class="data-table" style="width:100%;border-collapse:collapse;">
                    <thead><tr><th>PRS #</th><th>District</th><th>Intake Date</th><th>Status</th><th>Category</th><th>Subcategory</th><th>Closure</th></tr></thead>
                    <tbody>
                        <?php foreach ($rows as $r): ?>
                        <tr>
                            <td><?= h($r['prs_number']) ?></td>
                            <td><?= h($r['district']) ?></td>
                            <td><?= $r['intake_date'] ? date('M j, Y', strtotime($r['intake_date'])) : '—' ?></td>
                            <td><?= h($r['status'] ?? '—') ?></td>
                            <td><?= h($r['category'] ?? '—') ?></td>
                            <td><?= h($r['subcategory'] ?? '—') ?></td>
                            <td><?= h($r['closure_code'] ?? '—') ?></td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            <?php if ($total > $perPage): ?>
                <?php $pages = (int)ceil($total / $perPage); ?>
                <nav style="margin-top:1.5rem;display:flex;gap:0.5rem;justify-content:center;">
                    <?php if ($page > 1): ?><a href="?page=<?= $page - 1 ?><?= $search ? '&search=' . urlencode($search) : '' ?><?= $status ? '&status=' . urlencode($status) : '' ?>" class="btn btn-secondary">&laquo; Prev</a><?php endif; ?>
                    <span style="color:var(--text-muted);padding:0.5rem 1rem;">Page <?= $page ?> of <?= $pages ?></span>
                    <?php if ($page < $pages): ?><a href="?page=<?= $page + 1 ?><?= $search ? '&search=' . urlencode($search) : '' ?><?= $status ? '&status=' . urlencode($status) : '' ?>" class="btn btn-secondary">Next &raquo;</a><?php endif; ?>
                </nav>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</section>

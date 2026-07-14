<?php
declare(strict_types=1);

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

// ── Filter parameters ──
$search         = trim($_GET['search'] ?? '');
$status_filter  = trim($_GET['status'] ?? '');
$cat_filter     = trim($_GET['category'] ?? '');
$closure_filter = trim($_GET['closure'] ?? '');
$sort_by        = $_GET['sort'] ?? 'intake_date_desc';
$page           = max(1, (int)($_GET['page'] ?? 1));
$per_page       = min(200, max(10, (int)($_GET['per_page'] ?? 50)));
$district_filter = trim($_GET['district'] ?? '');
$date_from      = trim($_GET['date_from'] ?? '');
$date_to        = trim($_GET['date_to'] ?? '');

// ── Build WHERE clause ──
$where  = [];
$params = [];

if ($search !== '') {
    $where[]  = '(prs_number LIKE ? OR district LIKE ? OR category LIKE ? OR subcategory LIKE ?)';
    $p         = '%' . $search . '%';
    $params[]  = $p;
    $params[]  = $p;
    $params[]  = $p;
    $params[]  = $p;
}
if ($status_filter !== '') {
    $selected = explode(',', $status_filter);
    $placeholders = implode(',', array_fill(0, count($selected), '?'));
    $where[]  = "status IN ($placeholders)";
    $params   = array_merge($params, $selected);
}
if ($cat_filter !== '') {
    $selected = explode(',', $cat_filter);
    $placeholders = implode(',', array_fill(0, count($selected), '?'));
    $where[]  = "category IN ($placeholders)";
    $params   = array_merge($params, $selected);
}
if ($closure_filter !== '') {
    $where[]  = 'closure_code = ?';
    $params[] = $closure_filter;
}
if ($district_filter !== '') {
    $where[]  = 'district LIKE ?';
    $params[] = '%' . $district_filter . '%';
}
if ($date_from !== '') {
    $where[]  = 'intake_date >= ?';
    $params[] = $date_from;
}
if ($date_to !== '') {
    $where[]  = 'intake_date <= ?';
    $params[] = $date_to;
}

$where_clause = $where ? ' WHERE ' . implode(' AND ', $where) : '';

// ── Get filter dropdown values ──
$statuses  = Database::fetchAll("SELECT DISTINCT status FROM prs_intakes_data WHERE status IS NOT NULL AND status != '' ORDER BY status");
$categories = Database::fetchAll("SELECT DISTINCT category FROM prs_intakes_data WHERE category IS NOT NULL AND category != '' ORDER BY category");
$closures  = Database::fetchAll("SELECT DISTINCT closure_code FROM prs_intakes_data WHERE closure_code IS NOT NULL AND closure_code != '' ORDER BY closure_code");

// ── Counts ──
$total_all    = (int)Database::fetchColumn("SELECT COUNT(*) FROM prs_intakes_data");
$total_filtered = (int)Database::fetchColumn("SELECT COUNT(*) FROM prs_intakes_data{$where_clause}", $params);

$stats_open   = $where
    ? (int)Database::fetchColumn("SELECT COUNT(*) FROM prs_intakes_data{$where_clause} AND status NOT IN ('Closed','Case Inactive: Pending BSEA')", $params)
    : (int)Database::fetchColumn("SELECT COUNT(*) FROM prs_intakes_data WHERE status NOT IN ('Closed','Case Inactive: Pending BSEA')");
$stats_closed = $total_filtered - $stats_open;

// ── Sort ──
$sort_map = [
    'intake_date_desc'  => 'intake_date DESC',
    'intake_date_asc'   => 'intake_date ASC',
    'prs_number_asc'    => 'prs_number ASC',
    'prs_number_desc'   => 'prs_number DESC',
    'district_asc'      => 'district ASC',
    'district_desc'     => 'district DESC',
    'status_asc'        => 'status ASC',
];
$order = $sort_map[$sort_by] ?? 'intake_date DESC';

// ── Pagination ──
$total_pages = max(1, (int)ceil($total_filtered / $per_page));
$offset = ($page - 1) * $per_page;

$rows = Database::fetchAll(
    "SELECT * FROM prs_intakes_data{$where_clause} ORDER BY {$order} LIMIT ? OFFSET ?",
    array_merge($params, [$per_page, $offset])
);

// ── Page helpers ──
function pageLink(int $p): string {
    $qs = $_GET;
    $qs['page'] = (string)$p;
    return '/data/prs.php?' . http_build_query($qs);
}

$page_title       = 'PRS Data Dashboard';
$page_description = 'DESE Problem Resolution System — complaint intake, findings, and closure data across Massachusetts school districts.';
include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="prs-dashboard">
    <div class="container">
        <div class="section-header" data-animate>
            <span class="section-tag">DESE Problem Resolution System</span>
            <h2 class="section-title">PRS Data Dashboard</h2>
            <p class="section-subtitle">
                Complaint intake, findings, and closure data from the Massachusetts DESE Problem Resolution System.
                <?php echo number_format($total_all); ?> records spanning all MA school districts.
            </p>
        </div>

        <!-- Stats Row -->
        <div class="hero-stats mb-1" data-animate>
            <div class="stat">
                <span class="stat-value"><?php echo number_format($total_filtered); ?></span>
                <span class="stat-label">Filtered Records</span>
            </div>
            <div class="stat">
                <span class="stat-value"><?php echo number_format($total_all); ?></span>
                <span class="stat-label">Total Database</span>
            </div>
            <div class="stat">
                <span class="stat-value"><?php echo number_format($stats_open); ?></span>
                <span class="stat-label">Open / Active</span>
            </div>
            <div class="stat">
                <span class="stat-value"><?php echo number_format($stats_closed); ?></span>
                <span class="stat-label">Closed</span>
            </div>
            <div class="stat">
                <span class="stat-value"><?php echo $total_pages; ?></span>
                <span class="stat-label">Pages (<?php echo $per_page; ?>/pg)</span>
            </div>
        </div>

        <!-- Search + Filter Bar -->
        <form method="get" action="/data/prs.php" class="mb-1" data-animate>
            <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:flex-end;">
                <div style="flex:2;min-width:200px;">
                    <label class="stat-link">Search</label>
                    <input type="text" name="search" value="<?php echo h($search); ?>"
                        placeholder="PRS number, district, category..."
                        class="form-input">
                </div>
                <div style="flex:1;min-width:140px;">
                    <label class="stat-link">Status</label>
                    <select name="status" multiple
                        style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;min-height:36px;"
                        size="3">
                        <option value="">All Statuses</option>
                        <?php foreach ($statuses as $s):
                            $val = $s['status'];
                            $sel = in_array($val, explode(',', $status_filter)) ? 'selected' : '';
                        ?>
                            <option value="<?php echo h($val); ?>" <?php echo $sel; ?>><?php echo h($val); ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div style="flex:1;min-width:140px;">
                    <label class="stat-link">Category</label>
                    <select name="category" multiple
                        style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;min-height:36px;"
                        size="3">
                        <option value="">All Categories</option>
                        <?php foreach ($categories as $c):
                            $val = $c['category'];
                            $sel = in_array($val, explode(',', $cat_filter)) ? 'selected' : '';
                        ?>
                            <option value="<?php echo h($val); ?>" <?php echo $sel; ?>><?php echo h($val); ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div style="flex:1;min-width:120px;">
                    <label class="stat-link">Closure Code</label>
                    <select name="closure" class="form-input-sm">
                        <option value="">All</option>
                        <?php foreach ($closures as $cl):
                            $val = $cl['closure_code'];
                            $sel = ($val === $closure_filter) ? 'selected' : '';
                        ?>
                            <option value="<?php echo h($val); ?>" <?php echo $sel; ?>><?php echo h($val); ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div style="flex:1;min-width:100px;">
                    <label class="stat-link">Sort By</label>
                    <select name="sort" class="form-input-sm">
                        <?php
                        $sort_opts = [
                            'intake_date_desc'  => 'Date (Newest)',
                            'intake_date_asc'   => 'Date (Oldest)',
                            'prs_number_asc'    => 'PRS # (A-Z)',
                            'prs_number_desc'   => 'PRS # (Z-A)',
                            'district_asc'      => 'District (A-Z)',
                            'district_desc'     => 'District (Z-A)',
                            'status_asc'        => 'Status',
                        ];
                        foreach ($sort_opts as $val => $label):
                            $sel = ($sort_by === $val) ? 'selected' : '';
                        ?>
                            <option value="<?php echo $val; ?>" <?php echo $sel; ?>><?php echo $label; ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div style="flex:1;min-width:80px;">
                    <label class="stat-link">Per Page</label>
                    <select name="per_page" class="form-input-sm">
                        <?php foreach ([25, 50, 100, 200] as $pp):
                            $sel = ($per_page === $pp) ? 'selected' : '';
                        ?>
                            <option value="<?php echo $pp; ?>" <?php echo $sel; ?>><?php echo $pp; ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div style="flex:0;min-width:80px;display:flex;align-items:flex-end;">
                    <button type="submit" class="btn btn-primary btn-sm font-sm">Filter</button>
                </div>
            </div>
        </form>

        <?php if (empty($rows)): ?>
            <div class="empty-state" data-animate>
                <p>No PRS records match your filters.</p>
                <a href="/data/prs.php" class="btn btn-ghost mt-1">Clear Filters</a>
            </div>
        <?php else: ?>
            <p style="color:var(--text-muted);font-size:0.8rem;margin-bottom:0.5rem;" data-animate>
                Showing <?php echo $offset + 1; ?>&ndash;<?php echo min($offset + $per_page, $total_filtered); ?>
                of <?php echo number_format($total_filtered); ?> records
            </p>

            <div class="repo-table-wrapper" data-animate>
                <table class="repo-table">
                    <thead>
                        <tr>
                            <th>PRS #</th>
                            <th>District</th>
                            <th>Intake Date</th>
                            <th>Status</th>
                            <th>Findings Date</th>
                            <th>Category</th>
                            <th>Subcategory</th>
                            <th>Closure Code</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($rows as $r): ?>
                        <tr>
                            <td><strong><?php echo h($r['prs_number']); ?></strong></td>
                            <td><?php echo h($r['district']); ?></td>
                            <td><?php echo h($r['intake_date'] ?? ''); ?></td>
                            <td>
                                <span class="
                                    <?php echo ($r['status'] === 'Closed') ? 'status-closed' : 'status-open'; ?>
                                "><?php echo h($r['status'] ?? ''); ?></span>
                            </td>
                            <td><?php echo h($r['findings_date'] ?? ''); ?></td>
                            <td><?php echo h($r['category'] ?? ''); ?></td>
                            <td><?php echo h($r['subcategory'] ?? ''); ?></td>
                            <td><?php echo h($r['closure_code'] ?? ''); ?></td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>

            <?php if ($total_pages > 1): ?>
            <div class="pagination" style="display:flex;gap:0.5rem;justify-content:center;align-items:center;margin-top:1rem;" data-animate>
                <?php if ($page > 1): ?>
                    <a href="<?php echo pageLink(1); ?>" class="btn btn-ghost btn-sm font-xs">&laquo; First</a>
                <?php endif; ?>
                <?php
                $start = max(1, $page - 2);
                $end   = min($total_pages, $page + 2);
                for ($p = $start; $p <= $end; $p++):
                    $cls = ($p === $page) ? 'btn-primary' : 'btn-ghost';
                ?>
                    <a href="<?php echo pageLink($p); ?>" class="btn <?php echo $cls; ?> btn-sm font-xs"><?php echo $p; ?></a>
                <?php endfor; ?>
                <?php if ($page < $total_pages): ?>
                    <a href="<?php echo pageLink($total_pages); ?>" class="btn btn-ghost btn-sm font-xs">Last &raquo;</a>
                <?php endif; ?>
            </div>
            <?php endif; ?>
        <?php endif; ?>

        <div class="mt-2">
            <a href="/data/" class="btn btn-ghost">&larr; Data Hub</a>
        </div>
    </div>
</section>

<?php
include __DIR__ . '/../includes/footer.php';

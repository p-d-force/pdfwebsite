<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

$district_code = $_GET['district'] ?? '';
$type          = $_GET['type'] ?? '';
$status        = $_GET['status'] ?? '';
$search        = $_GET['search'] ?? '';
$page          = max(1, (int)($_GET['page'] ?? 1));
$perPage       = CASES_PER_PAGE;
$offset        = ($page - 1) * $perPage;

$where  = ['c.status != ?'];
$params = ['archived'];

if ($district_code && $district_code !== 'all') {
    $where[]  = 'c.district_code = ?';
    $params[] = $district_code;
}
if ($type && $type !== 'all') {
    $where[]  = 'c.type = ?';
    $params[] = $type;
}
if ($status && $status !== 'all') {
    $where[]  = 'c.status = ?';
    $params[] = $status;
}
if ($search) {
    $where[]  = '(c.title LIKE ? OR c.summary LIKE ? OR c.case_id LIKE ?)';
    $searchTerm = '%' . $search . '%';
    $params[] = $searchTerm;
    $params[] = $searchTerm;
    $params[] = $searchTerm;
}

$whereClause = implode(' AND ', $where);

$total       = (int)Database::fetchColumn("SELECT COUNT(*) FROM cases c WHERE {$whereClause}", $params);
$totalPages  = (int)ceil($total / $perPage);

$cases = Database::fetchAll(
    "SELECT c.*, COUNT(cd.id) as document_count
     FROM cases c
     LEFT JOIN case_documents cd ON c.id = cd.case_id
     WHERE {$whereClause}
     GROUP BY c.id
     ORDER BY c.filed_date DESC
     LIMIT ? OFFSET ?",
    array_merge($params, [$perPage, $offset])
);

$districts = Database::fetchAll('SELECT code, name FROM districts WHERE status = ? ORDER BY name', ['active']);
$types     = Database::fetchAll("SELECT DISTINCT type, COUNT(*) as total FROM cases WHERE status != 'archived' GROUP BY type ORDER BY type");

$page_title       = 'Case Directory';
$page_description = 'Active investigations, public records requests, appeals, and state determinations across Massachusetts districts.';
include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="cases">
    <div class="container">
        <div class="section-header" data-animate>
            <span class="section-tag">Case Portfolio</span>
            <h2 class="section-title">Case Directory</h2>
            <p class="section-subtitle">
                Active investigations, public records requests, appeals, and state determinations. 
                Every case documented with timelines, evidence, and linked analysis.
            </p>
        </div>

        <div class="case-filters" data-animate>
            <form method="get" class="articles-search-form">
                <div class="repo-search" style="flex:1;max-width:400px;">
                    <svg class="repo-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                    <input type="text" name="search" class="repo-search-input" placeholder="Search cases..." value="<?php echo h($search); ?>">
                </div>
                <select name="district" class="repo-select" onchange="this.form.submit()" style="max-width:200px;">
                    <option value="all">All Districts</option>
                    <?php foreach ($districts as $d): ?>
                        <option value="<?php echo h($d['code']); ?>" <?php echo $district_code === $d['code'] ? 'selected' : ''; ?>>
                            <?php echo h($d['name']); ?>
                        </option>
                    <?php endforeach; ?>
                </select>
                <select name="type" class="repo-select" onchange="this.form.submit()" style="max-width:200px;">
                    <option value="all">All Types</option>
                    <?php foreach ($types as $t): ?>
                        <option value="<?php echo h($t['type']); ?>" <?php echo $type === $t['type'] ? 'selected' : ''; ?>>
                            <?php echo case_type_label($t['type']); ?> (<?php echo $t['total']; ?>)
                        </option>
                    <?php endforeach; ?>
                </select>
                <select name="status" class="repo-select" onchange="this.form.submit()" style="max-width:160px;">
                    <option value="all">All Statuses</option>
                    <option value="open" <?php echo $status === 'open' ? 'selected' : ''; ?>>Open</option>
                    <option value="pending" <?php echo $status === 'pending' ? 'selected' : ''; ?>>Pending</option>
                    <option value="closed" <?php echo $status === 'closed' ? 'selected' : ''; ?>>Closed</option>
                    <option value="overdue" <?php echo $status === 'overdue' ? 'selected' : ''; ?>>Overdue</option>
                </select>
                <button type="submit" class="btn btn-ghost" style="padding:0.63rem 1rem;">Filter</button>
                <?php if ($search || $district_code || $type || $status): ?>
                    <a href="/cases/" class="btn btn-ghost" style="padding:0.63rem 1rem;">Clear</a>
                <?php endif; ?>
            </form>
        </div>

        <?php if (empty($cases)): ?>
            <div class="empty-state" data-animate>
                <h3>No cases found</h3>
                <p><?php echo $search ? 'No cases matching "' . h($search) . '".' : 'Cases will be added here as investigations progress.'; ?></p>
            </div>
        <?php else: ?>
            <div class="cases-grid" data-animate>
                <?php foreach ($cases as $case): ?>
                    <div class="case-card">
                        <div class="case-card-header">
                            <div class="case-district"><?php echo h($case['district_code']); ?>, MA</div>
                            <?php echo status_badge($case['status']); ?>
                        </div>
                        <div class="case-card-id"><?php echo h($case['case_id']); ?></div>
                        <h3 class="case-card-title"><?php echo h($case['title']); ?></h3>
                        <p class="case-card-summary"><?php echo h(truncate($case['summary'] ?: 'Details pending.', 150)); ?></p>
                        <div class="case-card-meta">
                            <div class="meta-item">
                                <span class="meta-label">Type</span>
                                <span class="meta-value"><?php echo case_type_label($case['type']); ?></span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">Filed</span>
                                <span class="meta-value"><?php echo format_date($case['filed_date']); ?></span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">Deadline</span>
                                <span class="meta-value"><?php echo format_date($case['deadline']); ?></span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">Docs</span>
                                <span class="meta-value"><?php echo $case['document_count']; ?></span>
                            </div>
                        </div>
                        <a href="/cases/<?php echo h($case['case_id']); ?>" class="case-card-btn">
                            View Case Details
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14"><path d="M9 5l7 7-7 7"/></svg>
                        </a>
                    </div>
                <?php endforeach; ?>
            </div>

            <?php if ($totalPages > 1): ?>
                <div class="pagination" data-animate>
                    <?php if ($page > 1): ?>
                        <a href="?page=<?php echo $page - 1; ?><?php echo $district_code ? '&district=' . urlencode($district_code) : ''; ?><?php echo $type ? '&type=' . urlencode($type) : ''; ?><?php echo $status ? '&status=' . urlencode($status) : ''; ?><?php echo $search ? '&search=' . urlencode($search) : ''; ?>" class="btn btn-ghost">&larr; Previous</a>
                    <?php endif; ?>
                    <span class="pagination-info">Page <?php echo $page; ?> of <?php echo $totalPages; ?> (<?php echo $total; ?> cases)</span>
                    <?php if ($page < $totalPages): ?>
                        <a href="?page=<?php echo $page + 1; ?><?php echo $district_code ? '&district=' . urlencode($district_code) : ''; ?><?php echo $type ? '&type=' . urlencode($type) : ''; ?><?php echo $status ? '&status=' . urlencode($status) : ''; ?><?php echo $search ? '&search=' . urlencode($search) : ''; ?>" class="btn btn-ghost">Next &rarr;</a>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</section>

<?php
include __DIR__ . '/../includes/footer.php';

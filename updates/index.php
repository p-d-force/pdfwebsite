<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

$page    = max(1, (int)($_GET['page'] ?? 1));
$perPage = UPDATES_PER_PAGE;
$offset  = ($page - 1) * $perPage;

$total       = (int)Database::fetchColumn('SELECT COUNT(*) FROM updates');
$totalPages  = (int)ceil($total / $perPage);

$updates = Database::fetchAll(
    'SELECT u.*, c.case_id as case_ref
     FROM updates u
     LEFT JOIN cases c ON u.related_case_id = c.case_id
     ORDER BY u.created_at DESC
     LIMIT ? OFFSET ?',
    [$perPage, $offset]
);

$page_title       = 'Updates';
$page_description = 'Chronological activity feed tracking case filings, document releases, determinations, and advocacy milestones.';
include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="updates">
    <div class="container">
        <div class="section-header" data-animate>
            <span class="section-tag">Activity Feed</span>
            <h2 class="section-title">Updates</h2>
            <p class="section-subtitle">
                Chronological feed of case activity, document releases, determinations, and advocacy milestones.
            </p>
        </div>

        <?php if (empty($updates)): ?>
            <div class="empty-state" data-animate>
                <p>Updates will appear here as cases progress and new information becomes available.</p>
            </div>
        <?php else: ?>
            <div class="updates-list" data-animate>
                <?php foreach ($updates as $update): ?>
                    <div class="update-item">
                        <div class="update-item-head">
                            <span class="update-date"><?php echo format_date($update['event_date'] ?? $update['created_at']); ?></span>
                            <?php echo severity_badge($update['severity']); ?>
                            <span class="update-source"><?php echo $update['source'] === 'auto' ? 'Auto-generated' : 'Manual'; ?></span>
                            <?php if ($update['related_case_id']): ?>
                                <a href="/cases/<?php echo h($update['case_ref'] ?? $update['related_case_id']); ?>" class="update-case-link"><?php echo h($update['related_case_id']); ?></a>
                            <?php endif; ?>
                        </div>
                        <h4 class="update-title"><?php echo h($update['title']); ?></h4>
                        <?php if ($update['body']): ?>
                            <p class="update-body"><?php echo nl2br(h($update['body'])); ?></p>
                        <?php endif; ?>
                        <?php if ($update['related_district_code']): ?>
                            <div style="margin-top:0.35rem;">
                                <a href="/districts/<?php echo h(strtolower($update['related_district_code'])); ?>" class="related-link">District: <?php echo h($update['related_district_code']); ?></a>
                            </div>
                        <?php endif; ?>
                    </div>
                <?php endforeach; ?>
            </div>

            <?php if ($totalPages > 1): ?>
                <div class="pagination" data-animate>
                    <?php if ($page > 1): ?>
                        <a href="?page=<?php echo $page - 1; ?>" class="btn btn-ghost">&larr; Previous</a>
                    <?php endif; ?>
                    <span class="pagination-info">Page <?php echo $page; ?> of <?php echo $totalPages; ?></span>
                    <?php if ($page < $totalPages): ?>
                        <a href="?page=<?php echo $page + 1; ?>" class="btn btn-ghost">Next &rarr;</a>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</section>

<?php
include __DIR__ . '/../includes/footer.php';

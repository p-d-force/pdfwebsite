<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

$caseId = $_GET['id'] ?? '';
if (!$caseId) {
    http_response_code(404);
    die('Case not found.');
}

$case = Database::fetch(
    'SELECT c.*, GROUP_CONCAT(DISTINCT cd2.case_id) as related_list
     FROM cases c
     LEFT JOIN cases cd2 ON cd2.id != c.id AND cd2.district_code = c.district_code AND cd2.status != ?
     WHERE c.case_id = ?
     GROUP BY c.id',
    ['archived', $caseId]
);

if (!$case) {
    http_response_code(404);
    $page_title       = 'Case Not Found';
    $page_description = 'The requested case could not be found.';
    include __DIR__ . '/../includes/head.php';
    include __DIR__ . '/../includes/header.php';
    echo '<section class="section"><div class="container"><div class="empty-state"><h2>Case Not Found</h2><p>The case you\'re looking for doesn\'t exist or has been removed.</p><a href="/cases/" class="btn btn-secondary" style="margin-top:1rem;">Browse Cases</a></div></div></section>';
    include __DIR__ . '/../includes/footer.php';
    exit;
}

$documents = Database::fetchAll(
    'SELECT * FROM case_documents WHERE case_id = ? ORDER BY sort_order ASC, document_date DESC',
    [$case['id']]
);

$related_articles = Database::fetchAll(
    'SELECT a.id, a.title, a.slug, a.excerpt, a.category, a.published_at, a.read_time
     FROM articles a
     JOIN article_case_links acl ON a.id = acl.article_id
     WHERE acl.case_id = ? AND a.status = ?
     ORDER BY a.published_at DESC',
    [$case['id'], 'published']
);

$timeline   = json_decode($case['timeline'] ?? '[]', true) ?: [];
$requested  = json_decode($case['requested_items'] ?? '[]', true) ?: [];
$relatedIds = array_filter(explode(',', $case['related_list'] ?? ''));

$page_title       = $case['title'];
$page_description = $case['summary'];
$page_type        = 'article';
include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="case-detail">
    <div class="container">
        <div class="case-detail-header" data-animate>
            <div class="case-detail-meta">
                <a href="/districts/<?php echo h(strtolower($case['district_code'])); ?>" class="case-district"><?php echo h($case['district_code']); ?>, MA</a>
                <?php echo status_badge($case['status']); ?>
                <?php if ($case['priority']): ?>
                    <span class="status-badge status-<?php echo $case['priority'] === 'high' ? 'closed' : ($case['priority'] === 'medium' ? 'pending' : 'open'); ?>"><?php echo ucfirst($case['priority']); ?> Priority</span>
                <?php endif; ?>
            </div>
            <span class="case-detail-id"><?php echo h($case['case_id']); ?></span>
            <h1 class="case-detail-title"><?php echo h($case['title']); ?></h1>
            <p class="case-detail-summary"><?php echo h($case['summary']); ?></p>

            <div class="case-detail-stats">
                <div class="stat">
                    <span class="stat-label">Type</span>
                    <span class="stat-value" style="font-size:0.95rem;"><?php echo case_type_label($case['type']); ?></span>
                </div>
                <div class="stat">
                    <span class="stat-label">Filed</span>
                    <span class="stat-value" style="font-size:0.95rem;"><?php echo format_date($case['filed_date'], 'M j, Y'); ?></span>
                </div>
                <div class="stat">
                    <span class="stat-label">Deadline</span>
                    <span class="stat-value" style="font-size:0.95rem;"><?php echo format_date($case['deadline'], 'M j, Y'); ?></span>
                </div>
                <div class="stat">
                    <span class="stat-label">Current Stage</span>
                    <span class="stat-value" style="font-size:0.95rem;"><?php echo h($case['current_stage'] ?: 'In Progress'); ?></span>
                </div>
            </div>
        </div>

        <?php if (!empty($requested)): ?>
            <div class="case-detail-section" data-animate>
                <h3>Requested Records / Scope</h3>
                <ul>
                    <?php foreach ($requested as $item): ?>
                        <li><?php echo h($item); ?></li>
                    <?php endforeach; ?>
                </ul>
            </div>
        <?php endif; ?>

        <?php if (!empty($timeline)): ?>
            <div class="case-detail-section" data-animate>
                <h3>Case Timeline</h3>
                <ul class="timeline-list">
                    <?php foreach ($timeline as $event): ?>
                        <li class="timeline-item">
                            <div class="timeline-item-head">
                                <span class="timeline-item-title"><?php echo h($event['title'] ?? ''); ?></span>
                                <span class="timeline-item-date"><?php echo h($event['date'] ?? ''); ?></span>
                            </div>
                            <p><?php echo h($event['description'] ?? ''); ?></p>
                            <?php if (!empty($event['docs'])): ?>
                                <div class="timeline-docs">
                                    <?php foreach ($event['docs'] as $doc): ?>
                                        <?php if (is_string($doc)): ?>
                                            <span class="timeline-doc"><?php echo h($doc); ?></span>
                                        <?php else: ?>
                                            <a class="timeline-doc" href="<?php echo h($doc['url'] ?? '#'); ?>" target="_blank" rel="noopener"><?php echo h($doc['label'] ?? 'Document'); ?></a>
                                        <?php endif; ?>
                                    <?php endforeach; ?>
                                </div>
                            <?php endif; ?>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </div>
        <?php endif; ?>

        <?php if (!empty($documents)): ?>
            <div class="case-detail-section" data-animate>
                <h3>Documents</h3>
                <div class="repo-table-wrapper">
                    <table class="repo-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Type</th>
                                <th>Title</th>
                                <th>File</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($documents as $doc): ?>
                                <tr>
                                    <td class="repo-date"><?php echo format_date($doc['document_date']); ?></td>
                                    <td><?php echo h(ucfirst(str_replace('_', ' ', $doc['document_type']))); ?></td>
                                    <td><?php echo h($doc['title']); ?></td>
                                    <td>
                                        <?php if ($doc['file_path']): ?>
                                            <a href="<?php echo h($doc['file_path']); ?>" class="doc-link" target="_blank" rel="noopener">
                                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14">
                                                    <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                                                </svg>
                                                <?php echo h(strtoupper($doc['file_type'] ?? 'FILE')); ?>
                                            </a>
                                        <?php else: ?>
                                            <span style="color:var(--text-muted);">—</span>
                                        <?php endif; ?>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
            </div>
        <?php endif; ?>

        <?php if (!empty($related_articles)): ?>
            <div class="case-detail-section" data-animate>
                <h3>Related Articles</h3>
                <div class="articles-grid" style="grid-template-columns:repeat(2, minmax(0, 1fr));">
                    <?php foreach ($related_articles as $ra): ?>
                        <article class="article-card">
                            <div class="article-card-body">
                                <div class="article-card-meta">
                                    <span class="article-category"><?php echo category_label($ra['category']); ?></span>
                                    <span class="article-date"><?php echo format_date($ra['published_at']); ?></span>
                                </div>
                                <h3 class="article-card-title">
                                    <a href="/articles/<?php echo h($ra['slug']); ?>"><?php echo h($ra['title']); ?></a>
                                </h3>
                            </div>
                        </article>
                    <?php endforeach; ?>
                </div>
            </div>
        <?php endif; ?>

        <?php if (!empty($relatedIds)): ?>
            <div class="case-detail-section" data-animate>
                <h3>Related Cases</h3>
                <div class="case-detail-links">
                    <?php foreach ($relatedIds as $rid): ?>
                        <a href="/cases/<?php echo h($rid); ?>" class="related-link"><?php echo h($rid); ?></a>
                    <?php endforeach; ?>
                </div>
            </div>
        <?php endif; ?>

        <div style="margin-top:2rem;" data-animate>
            <a href="/cases/" class="btn btn-ghost">&larr; Back to Case Directory</a>
        </div>
    </div>
</section>

<?php
include __DIR__ . '/../includes/footer.php';

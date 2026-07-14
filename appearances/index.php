<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

$type = $_GET['type'] ?? '';

$where  = '';
$params = [];
if ($type && $type !== 'all') {
    $where   = 'WHERE type = ?';
    $params[] = $type;
}

$appearances = Database::fetchAll(
    "SELECT * FROM media_appearances {$where} ORDER BY date DESC",
    $params
);

$typeCounts = Database::fetchAll(
    'SELECT type, COUNT(*) as total FROM media_appearances GROUP BY type ORDER BY type'
);

$page_title       = 'Appearances';
$page_description = 'News articles, radio interviews, public comments, and media coverage of Parent Data Force and its members.';
include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="appearances">
    <div class="container">
        <div class="section-header" data-animate>
            <span class="section-tag">Media &amp; Public Engagement</span>
            <h2 class="section-title">Appearances</h2>
            <p class="section-subtitle">
                News articles, radio interviews, public comments, and media coverage featuring 
                Parent Data Force and its members across Massachusetts.
            </p>
        </div>

        <div class="articles-controls" data-animate style="margin-bottom:1.5rem;">
            <form method="get" class="articles-search-form">
                <select name="type" class="repo-select" onchange="this.form.submit()" style="max-width:250px;">
                    <option value="all">All Types</option>
                    <?php foreach ($typeCounts as $tc): ?>
                        <option value="<?php echo h($tc['type']); ?>" <?php echo $type === $tc['type'] ? 'selected' : ''; ?>>
                            <?php echo h(ucfirst(str_replace('_', ' ', $tc['type']))); ?> (<?php echo $tc['total']; ?>)
                        </option>
                    <?php endforeach; ?>
                </select>
                <?php if ($type): ?>
                    <a href="/appearances/" class="btn btn-ghost" style="padding:0.63rem 1rem;">Clear</a>
                <?php endif; ?>
            </form>
        </div>

        <?php if (empty($appearances)): ?>
            <div class="empty-state" data-animate>
                <p>Media appearances will appear here as Parent Data Force engages with press, radio, and public meetings.</p>
            </div>
        <?php else: ?>
            <div class="appearances-grid" data-animate>
                <?php foreach ($appearances as $a): ?>
                    <article class="appearance-card">
                        <div class="appearance-meta">
                            <span class="appearance-type" style="
                                display:inline-block;
                                font-size:0.72rem;
                                font-weight:600;
                                text-transform:uppercase;
                                letter-spacing:0.06em;
                                padding:0.2rem 0.55rem;
                                border-radius:999px;
                                margin-right:0.5rem;
                                <?php
                                $colors = [
                                    'news_article'  => 'background:rgba(6,182,212,0.12);color:#06b6d4;border:1px solid rgba(6,182,212,0.3);',
                                    'radio'         => 'background:rgba(245,158,11,0.12);color:#f59e0b;border:1px solid rgba(245,158,11,0.3);',
                                    'public_comment'=> 'background:rgba(34,197,94,0.12);color:#22c55e;border:1px solid rgba(34,197,94,0.3);',
                                    'tv'            => 'background:rgba(139,92,246,0.12);color:#8b5cf6;border:1px solid rgba(139,92,246,0.3);',
                                    'podcast'       => 'background:rgba(236,72,153,0.12);color:#ec4899;border:1px solid rgba(236,72,153,0.3);',
                                    'other'         => 'background:rgba(161,161,170,0.12);color:#a1a1aa;border:1px solid rgba(161,161,170,0.3);',
                                ];
                                echo $colors[$a['type']] ?? $colors['other'];
                                ?>">
                                <?php echo h(ucfirst(str_replace('_', ' ', $a['type']))); ?>
                            </span>
                            <span class="appearance-date" style="color:var(--text-muted);font-size:0.82rem;">
                                <?php echo date('M j, Y', strtotime($a['date'])); ?>
                            </span>
                            <?php if ($a['district_code']): ?>
                                <a href="/districts/<?php echo h(strtolower($a['district_code'])); ?>/" 
                                   style="color:var(--accent-glow);font-size:0.78rem;margin-left:0.5rem;text-decoration:underline;">
                                    <?php echo h($a['district_code']); ?>
                                </a>
                            <?php endif; ?>
                        </div>
                        <h3 class="appearance-title">
                            <?php if ($a['source_url']): ?>
                                <a href="<?php echo h($a['source_url']); ?>" target="_blank" rel="noopener">
                                    <?php echo h($a['title']); ?>
                                </a>
                            <?php else: ?>
                                <?php echo h($a['title']); ?>
                            <?php endif; ?>
                        </h3>
                        <?php if ($a['description']): ?>
                            <p class="appearance-summary" style="color:var(--text-secondary);font-size:0.9rem;line-height:1.5;">
                                <?php echo h($a['description']); ?>
                            </p>
                        <?php endif; ?>
                        <div style="margin-top:0.5rem;font-size:0.8rem;color:var(--text-muted);">
                            <strong>Source:</strong> <?php echo h($a['source_name']); ?>
                            <?php if ($a['person']): ?>
                                &middot; <?php echo h($a['person']); ?>
                            <?php endif; ?>
                        </div>
                    </article>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
    </div>
</section>

<?php
include __DIR__ . '/../includes/footer.php';

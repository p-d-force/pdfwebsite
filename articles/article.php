<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';
require_once __DIR__ . '/../includes/shortcodes.php';

$slug = $_GET['slug'] ?? '';
if (!$slug) {
    http_response_code(404);
    die('Article not found.');
}

$article = Database::fetch(
    "SELECT a.*, GROUP_CONCAT(DISTINCT d.code) as district_codes
     FROM articles a
     LEFT JOIN article_district_links adl ON a.id = adl.article_id
     LEFT JOIN districts d ON adl.district_id = d.id
     WHERE a.slug = ? AND a.status = ?
     GROUP BY a.id",
    [$slug, 'published']
);

if (!$article) {
    http_response_code(404);
    $page_title       = 'Article Not Found';
    $page_description = 'The requested article could not be found.';
    include __DIR__ . '/../includes/head.php';
    include __DIR__ . '/../includes/header.php';
    echo '<section class="section"><div class="container"><div class="empty-state"><h2>Article Not Found</h2><p>The article you\'re looking for doesn\'t exist or has been removed.</p><a href="/articles/" class="btn btn-secondary" style="margin-top:1rem;">Browse Articles</a></div></div></section>';
    include __DIR__ . '/../includes/footer.php';
    exit;
}

$related_cases = Database::fetchAll(
    'SELECT c.* FROM cases c
     JOIN article_case_links acl ON c.id = acl.case_id
     WHERE acl.article_id = ?
     ORDER BY c.filed_date DESC',
    [$article['id']]
);

$related_articles = Database::fetchAll(
    "SELECT id, title, slug, excerpt, body, category, published_at, read_time
     FROM articles
     WHERE category = ? AND id != ? AND status = ?
     ORDER BY published_at DESC
     LIMIT 3",
    [$article['category'], $article['id'], 'published']
);

$body = render_shortcodes($article['body']);

$page_title       = $article['seo_title'] ?: $article['title'];
$page_description = $article['seo_description'] ?: ($article['excerpt'] ?: excerpt($article['body'], 200));
$page_type        = 'article';
$canonical_url    = SITE_URL . '/articles/' . $article['slug'];
$og_image         = $article['featured_image'] ?: null;

include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="article">
    <div class="container">
        <article class="article-full">
            <header class="article-header" data-animate>
                <div class="article-header-meta">
                    <span class="article-category article-category-large"><?php echo category_label($article['category']); ?></span>
                    <span class="article-date"><?php echo format_date($article['published_at']); ?></span>
                    <span class="article-read-time"><?php echo $article['read_time'] ?: read_time($article['body']); ?> min read</span>
                    <?php if ($article['author']): ?>
                        <span class="article-author">by <?php echo h($article['author']); ?></span>
                    <?php endif; ?>
                </div>
                <h1 class="article-title"><?php echo h($article['title']); ?></h1>
                <?php if ($article['excerpt']): ?>
                    <p class="article-excerpt"><?php echo h($article['excerpt']); ?></p>
                <?php endif; ?>
            </header>

            <?php if ($article['featured_image']): ?>
                <div class="article-featured-image" data-animate>
                    <img src="<?php echo h($article['featured_image']); ?>" alt="<?php echo h($article['title']); ?>">
                </div>
            <?php endif; ?>

            <div class="article-body" data-animate>
                <?php echo $body; ?>
            </div>

            <?php if ($article['district_codes']): ?>
                <div class="article-tags" data-animate>
                    <span class="article-tags-label">Districts:</span>
                    <?php foreach (explode(',', $article['district_codes']) as $code): ?>
                        <a href="/districts/<?php echo h(strtolower($code)); ?>" class="article-tag"><?php echo h($code); ?></a>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>

            <div class="article-share" data-animate>
                <span class="article-share-label">Share:</span>
                <a href="https://twitter.com/intent/tweet?url=<?php echo urlencode($canonical_url); ?>&text=<?php echo urlencode($article['title']); ?>" target="_blank" rel="noopener" class="social-link">
                    <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                </a>
                <a href="https://www.facebook.com/sharer/sharer.php?u=<?php echo urlencode($canonical_url); ?>" target="_blank" rel="noopener" class="social-link">
                    <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                </a>
                <a href="mailto:?subject=<?php echo urlencode($article['title']); ?>&body=<?php echo urlencode($canonical_url); ?>" class="social-link">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><path d="M22 6l-10 7L2 6"/></svg>
                </a>
            </div>
        </article>

        <?php if (!empty($related_cases)): ?>
            <div class="article-related" data-animate>
                <h3 class="article-related-title">Related Cases</h3>
                <div class="cases-grid" style="grid-template-columns:repeat(2, minmax(0, 1fr));">
                    <?php foreach ($related_cases as $case): ?>
                        <div class="case-card">
                            <div class="case-card-header">
                                <div class="case-district"><?php echo h($case['district_code']); ?>, MA</div>
                                <?php echo status_badge($case['status']); ?>
                            </div>
                            <div class="case-card-id"><?php echo h($case['case_id']); ?></div>
                            <h3 class="case-card-title"><?php echo h($case['title']); ?></h3>
                            <p class="case-card-summary"><?php echo h(truncate($case['summary'], 150)); ?></p>
                            <a href="/cases/<?php echo h($case['case_id']); ?>" class="case-card-btn">
                                View Case Details
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14"><path d="M9 5l7 7-7 7"/></svg>
                            </a>
                        </div>
                    <?php endforeach; ?>
                </div>
            </div>
        <?php endif; ?>

        <?php if (!empty($related_articles)): ?>
            <div class="article-related" data-animate>
                <h3 class="article-related-title">Related Articles</h3>
                <div class="articles-grid" style="grid-template-columns:repeat(3, minmax(0, 1fr));">
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
                                <p class="article-card-excerpt"><?php echo h(truncate($ra['excerpt'] ?: '', 150)); ?></p>
                                <div class="article-card-footer">
                                    <span class="article-read-time"><?php echo $ra['read_time'] ?: read_time($ra['body'] ?? ''); ?> min read</span>
                                    <a href="/articles/<?php echo h($ra['slug']); ?>" class="resource-link">Read Article</a>
                                </div>
                            </div>
                        </article>
                    <?php endforeach; ?>
                </div>
            </div>
        <?php endif; ?>
    </div>
</section>

<?php
include __DIR__ . '/../includes/footer.php';

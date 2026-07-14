<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

$page        = max(1, (int)($_GET['page'] ?? 1));
$category    = $_GET['category'] ?? '';
$search      = $_GET['search'] ?? '';
$per_page    = ARTICLES_PER_PAGE;
$offset      = ($page - 1) * $per_page;

$where  = ['a.status = ?'];
$params = ['published'];

if ($category && $category !== 'all') {
    $where[]  = 'a.category = ?';
    $params[] = $category;
}
if ($search) {
    $where[]  = '(a.title LIKE ? OR a.excerpt LIKE ? OR a.body LIKE ?)';
    $searchTerm = '%' . $search . '%';
    $params[] = $searchTerm;
    $params[] = $searchTerm;
    $params[] = $searchTerm;
}

$whereClause = implode(' AND ', $where);

$total       = (int)Database::fetchColumn("SELECT COUNT(*) FROM articles a WHERE {$whereClause}", $params);
$total_pages = (int)ceil($total / $per_page);

$articles = Database::fetchAll(
    "SELECT a.*, GROUP_CONCAT(DISTINCT d.code) as district_codes
     FROM articles a
     LEFT JOIN article_district_links adl ON a.id = adl.article_id
     LEFT JOIN districts d ON adl.district_id = d.id
     WHERE {$whereClause}
     GROUP BY a.id
     ORDER BY a.featured DESC, a.published_at DESC
     LIMIT ? OFFSET ?",
    array_merge($params, [$per_page, $offset])
);

$categories = Database::fetchAll("SELECT DISTINCT category, COUNT(*) as total FROM articles WHERE status = 'published' GROUP BY category ORDER BY category");

// Featured article (first one when no category/search filter)
$featured = (!$category && !$search && $page === 1 && !empty($articles)) ? array_shift($articles) : null;

$page_title       = 'Articles';
$page_description = 'Data-driven reporting on special education, public records, and systemic accountability across Massachusetts districts.';
include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="articles">
    <div class="container">
        <div class="section-header" data-animate>
            <span class="section-tag">Research &amp; Analysis</span>
            <h2 class="section-title">Articles</h2>
            <p class="section-subtitle">
                Investigative reporting, data analysis, methodology guides, and policy commentary on special education and public accountability.
            </p>
        </div>

        <!-- Quick-filter category pills -->
        <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:2rem;justify-content:center;" data-animate>
            <a href="/articles/" class="article-category<?php echo !$category ? ' article-category-active' : ''; ?>" style="padding:0.4rem 0.9rem;font-size:0.8rem;text-decoration:none;<?php echo !$category ? 'background:var(--accent);color:#fff;' : ''; ?>">
                All (<?php echo $total; ?>)
            </a>
            <?php foreach ($categories as $cat): ?>
                <a href="?category=<?php echo h($cat['category']); ?>" class="article-category" style="padding:0.4rem 0.9rem;font-size:0.8rem;text-decoration:none;<?php echo $category === $cat['category'] ? 'background:var(--accent);color:#fff;' : ''; ?>">
                    <?php echo category_label($cat['category']); ?> (<?php echo $cat['total']; ?>)
                </a>
            <?php endforeach; ?>
        </div>

        <!-- Featured Article Hero -->
        <?php if ($featured): ?>
        <div class="article-featured" data-animate style="margin-bottom:2.5rem;">
            <article style="background:var(--bg-elevated);border-radius:20px;overflow:hidden;border:1px solid var(--border);">
                <?php if ($featured['featured_image']): ?>
                    <div style="width:100%;max-height:400px;overflow:hidden;">
                        <img src="<?php echo h($featured['featured_image']); ?>" alt="<?php echo h($featured['title']); ?>" style="width:100%;height:100%;object-fit:cover;" loading="eager">
                    </div>
                <?php endif; ?>
                <div style="padding:2rem;">
                    <div style="display:flex;gap:0.75rem;align-items:center;margin-bottom:0.75rem;">
                        <span class="article-category article-category-large"><?php echo category_label($featured['category']); ?></span>
                        <span class="article-date"><?php echo format_date($featured['published_at']); ?></span>
                        <span style="color:var(--text-muted);font-size:0.8rem;">· <?php echo $featured['read_time'] ?: read_time($featured['body']); ?> min read</span>
                    </div>
                    <h2 style="font-size:1.8rem;margin-bottom:0.75rem;line-height:1.3;">
                        <a href="/articles/<?php echo h($featured['slug']); ?>" style="color:inherit;text-decoration:none;"><?php echo h($featured['title']); ?></a>
                    </h2>
                    <p style="color:var(--text-muted);font-size:1.05rem;line-height:1.6;margin-bottom:1rem;">
                        <?php echo h($featured['excerpt'] ?: excerpt($featured['body'], 250)); ?>
                    </p>
                    <a href="/articles/<?php echo h($featured['slug']); ?>" class="btn btn-primary">Read Full Article →</a>
                </div>
            </article>
        </div>
        <?php endif; ?>

        <!-- Search -->
        <div class="articles-controls" data-animate style="margin-bottom:1.5rem;">
            <form method="get" class="articles-search-form" style="display:flex;gap:0.5rem;align-items:center;">
                <?php if ($category): ?><input type="hidden" name="category" value="<?php echo h($category); ?>"><?php endif; ?>
                <div class="repo-search" style="flex:1;max-width:400px;">
                    <svg class="repo-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                    <input type="text" name="search" class="repo-search-input" placeholder="Search articles..." value="<?php echo h($search); ?>">
                </div>
                <button type="submit" class="btn btn-ghost" style="padding:0.63rem 1rem;">Search</button>
                <?php if ($search): ?>
                    <a href="/articles/<?php echo $category ? '?category=' . h($category) : ''; ?>" class="btn btn-ghost" style="padding:0.63rem 1rem;">Clear</a>
                <?php endif; ?>
            </form>
        </div>

        <?php if (empty($articles) && !$featured): ?>
            <div class="empty-state" data-animate>
                <h3>No articles found</h3>
                <p><?php echo $search ? 'No articles matching "' . h($search) . '".' : 'Articles will appear here once published.'; ?></p>
            </div>
        <?php else: ?>
            <!-- AdSense-ready: top banner placement -->
            <div class="ad-placeholder" style="background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.08);border-radius:12px;padding:1.5rem;text-align:center;color:var(--text-muted);font-size:0.8rem;margin-bottom:2rem;" data-animate>
                Advertisement — AdSense placement
            </div>

            <div class="articles-grid" data-animate>
                <?php $count = 0; foreach ($articles as $article): $count++; ?>
                    <article class="article-card">
                        <?php if ($article['featured_image']): ?>
                            <div class="article-card-image">
                                <img src="<?php echo h($article['featured_image']); ?>" alt="<?php echo h($article['title']); ?>" loading="lazy">
                            </div>
                        <?php endif; ?>
                        <div class="article-card-body">
                            <div class="article-card-meta">
                                <span class="article-category"><?php echo category_label($article['category']); ?></span>
                                <span class="article-date"><?php echo format_date($article['published_at']); ?></span>
                                <span style="color:var(--text-muted);font-size:0.75rem;"><?php echo $article['read_time'] ?: read_time($article['body']); ?> min</span>
                            </div>
                            <h3 class="article-card-title">
                                <a href="/articles/<?php echo h($article['slug']); ?>"><?php echo h($article['title']); ?></a>
                            </h3>
                            <p class="article-card-excerpt">
                                <?php echo h($article['excerpt'] ?: excerpt($article['body'])); ?>
                            </p>
                            <div class="article-card-footer">
                                <a href="/articles/<?php echo h($article['slug']); ?>" class="resource-link">Read Article →</a>
                            </div>
                        </div>
                    </article>
                    
                    <!-- Inline AdSense after every 3rd card -->
                    <?php if ($count % 3 === 0 && $count < count($articles)): ?>
                        <div class="ad-placeholder" style="background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.08);border-radius:12px;padding:1rem;text-align:center;color:var(--text-muted);font-size:0.75rem;grid-column:1/-1;">
                            Advertisement — AdSense inline placement
                        </div>
                    <?php endif; ?>
                <?php endforeach; ?>
            </div>

            <!-- Newsletter CTA -->
            <div style="background:rgba(255,90,31,0.06);border:1px solid rgba(255,90,31,0.15);border-radius:16px;padding:2rem;text-align:center;margin:2rem 0;" data-animate>
                <h3 style="margin-bottom:0.5rem;">Stay Updated</h3>
                <p style="color:var(--text-muted);margin-bottom:1rem;">Get new articles, case updates, and data releases delivered to your inbox.</p>
                <form action="/api/subscribe.php" method="post" style="display:flex;gap:0.5rem;justify-content:center;max-width:450px;margin:0 auto;">
                    <input type="hidden" name="csrf_token" value="<?php echo csrf_token(); ?>">
                    <input type="email" name="email" class="form-input" placeholder="Your email address" required style="flex:1;">
                    <button type="submit" class="btn btn-primary">Subscribe</button>
                </form>
            </div>

            <?php if ($total_pages > 1): ?>
                <div class="pagination" data-animate style="display:flex;justify-content:center;align-items:center;gap:0.75rem;">
                    <?php if ($page > 1): ?>
                        <a href="?page=<?php echo $page - 1; ?><?php echo $category ? '&category=' . urlencode($category) : ''; ?><?php echo $search ? '&search=' . urlencode($search) : ''; ?>" class="btn btn-ghost">← Previous</a>
                    <?php endif; ?>
                    <span class="pagination-info" style="color:var(--text-muted);">Page <?php echo $page; ?> of <?php echo $total_pages; ?> (<?php echo $total; ?> articles)</span>
                    <?php if ($page < $total_pages): ?>
                        <a href="?page=<?php echo $page + 1; ?><?php echo $category ? '&category=' . urlencode($category) : ''; ?><?php echo $search ? '&search=' . urlencode($search) : ''; ?>" class="btn btn-ghost">Next →</a>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</section>

<?php include __DIR__ . '/../includes/footer.php'; ?>

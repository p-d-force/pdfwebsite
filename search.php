<?php
declare(strict_types=1);
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/includes/Database.php';
require_once __DIR__ . '/includes/helpers.php';

$query   = trim($_GET['q'] ?? '');
$results = [];
$total   = 0;

if (mb_strlen($query) >= 2) {
    $search = '%' . $query . '%';

    $articles = Database::fetchAll(
        "SELECT id, title, slug, excerpt, category, published_at, 'article' as result_type
         FROM articles WHERE status = 'published' AND (title LIKE ? OR excerpt LIKE ? OR body LIKE ?)
         ORDER BY published_at DESC LIMIT 15",
        [$search, $search, $search]
    );

    $cases = Database::fetchAll(
        "SELECT id, case_id, title, summary as excerpt, type as category, filed_date as published_at, status, district_code, 'case' as result_type
         FROM cases WHERE status != 'archived' AND (title LIKE ? OR summary LIKE ? OR case_id LIKE ?)
         ORDER BY filed_date DESC LIMIT 15",
        [$search, $search, $search]
    );

    $speeches = Database::fetchAll(
        "SELECT id, title, description as excerpt, category, published_at, video_id, url, 'speech' as result_type
         FROM speeches WHERE title LIKE ? OR description LIKE ?
         ORDER BY published_at DESC LIMIT 10",
        [$search, $search]
    );

    $results = array_merge($articles, $cases, $speeches);
    $total   = count($results);
}

$page_title       = 'Search Results' . ($query ? ' for "' . $query . '"' : '');
$page_description = 'Search across Parent Data Force articles, cases, and speeches.';
include __DIR__ . '/includes/head.php';
include __DIR__ . '/includes/header.php';
?>

<section class="section">
    <div class="container">
        <div class="section-header">
            <span class="section-tag">Search</span>
            <h2 class="section-title"><?php echo $query ? 'Results for "' . h($query) . '"' : 'Search the Site'; ?></h2>
            <p class="section-subtitle">Search across articles, cases, and speeches.</p>
        </div>

        <form method="get" style="margin-bottom:2rem;">
            <div class="repo-search" style="max-width:600px;">
                <svg class="repo-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                <input type="text" name="q" class="repo-search-input" value="<?php echo h($query); ?>" placeholder="Search articles, cases, and speeches..." autofocus>
            </div>
            <button type="submit" class="btn btn-primary" style="margin-top:0.6rem;">Search</button>
        </form>

        <?php if ($query && mb_strlen($query) < 2): ?>
            <p style="color:var(--text-muted);">Please enter at least 2 characters to search.</p>
        <?php elseif ($query && $total === 0): ?>
            <div class="empty-state">
                <h3>No results for "<?php echo h($query); ?>"</h3>
                <p>Try different keywords or browse by category.</p>
                <div style="margin-top:1rem;display:flex;gap:0.75rem;justify-content:center;">
                    <a href="/articles/" class="btn btn-secondary">Browse Articles</a>
                    <a href="/cases/" class="btn btn-ghost">Browse Cases</a>
                </div>
            </div>
        <?php elseif ($total > 0): ?>
            <p style="color:var(--text-muted);margin-bottom:1rem;"><?php echo $total; ?> result<?php echo $total !== 1 ? 's' : ''; ?> found.</p>
            <div class="search-results-list">
                <?php foreach ($results as $r): ?>
                    <?php
                    $typeLabel = '';
                    $url = '#';
                    $date = format_date($r['published_at'] ?? '');

                    if ($r['result_type'] === 'article') {
                        $typeLabel = 'Article';
                        $url = '/articles/' . h($r['slug']);
                    } elseif ($r['result_type'] === 'case') {
                        $typeLabel = 'Case';
                        $url = '/cases/' . h($r['case_id'] ?? $r['slug'] ?? '');
                    } else {
                        $typeLabel = 'Speech';
                        $url = '/speeches/';
                    }
                    ?>
                    <a href="<?php echo $url; ?>" class="search-result-item">
                        <div class="search-result-head">
                            <span class="search-type"><?php echo $typeLabel; ?></span>
                            <span class="search-result-date"><?php echo $date; ?></span>
                        </div>
                        <h3 class="search-result-title"><?php echo h($r['title']); ?></h3>
                        <p class="search-result-excerpt"><?php echo h(truncate($r['excerpt'] ?? '', 200)); ?></p>
                        <?php if (!empty($r['district_code'])): ?>
                            <span class="search-result-district"><?php echo h($r['district_code']); ?></span>
                        <?php endif; ?>
                    </a>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
    </div>
</section>

<style>
.search-results-list { display:flex; flex-direction:column; gap:0.8rem; }
.search-result-item { display:block; border:1px solid var(--border); border-radius:var(--radius-md); padding:1.2rem; background:var(--bg-glass); transition:all var(--transition); text-decoration:none; }
.search-result-item:hover { border-color:rgba(255,90,31,0.45); transform:translateY(-2px); box-shadow:var(--shadow-soft); }
.search-result-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem; }
.search-type { font-size:0.7rem; padding:0.15rem 0.5rem; border-radius:999px; background:rgba(255,90,31,0.12); color:var(--accent-glow); font-weight:600; }
.search-result-date { font-size:0.8rem; color:var(--text-muted); }
.search-result-title { font-size:1.05rem; color:var(--text-primary); margin-bottom:0.35rem; }
.search-result-excerpt { font-size:0.88rem; color:var(--text-secondary); line-height:1.5; }
.search-result-district { display:inline-block; font-size:0.72rem; color:var(--accent-glow); font-family:'JetBrains Mono',monospace; margin-top:0.4rem; padding:0.15rem 0.45rem; border:1px solid var(--border); border-radius:999px; }
</style>

<?php include __DIR__ . '/includes/footer.php'; ?>

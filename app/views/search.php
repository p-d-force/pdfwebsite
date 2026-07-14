<section class="section">
    <div class="container">
        <div class="section-header">
            <span class="section-tag">Search</span>
            <h2 class="section-title"><?= $query ? 'Results for "' . h($query) . '"' : 'Search the Site' ?></h2>
            <p class="section-subtitle">Search across articles, cases, and more.</p>
        </div>

        <form method="get" action="/search" style="margin-bottom:2rem;">
            <div class="repo-search" style="max-width:600px;">
                <svg class="repo-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                <input type="text" name="q" class="repo-search-input" value="<?= h($query) ?>" placeholder="Search articles and cases..." autofocus>
            </div>
            <button type="submit" class="btn btn-primary" style="margin-top:0.6rem;">Search</button>
        </form>

        <?php if (!$query): ?>
            <p class="text-muted">Enter a search term to find articles and cases.</p>
        <?php elseif ($total === 0): ?>
            <div class="empty-state">
                <h3>No results for "<?= h($query) ?>"</h3>
                <p>Try different keywords or browse by category.</p>
                <div style="margin-top:1rem;display:flex;gap:0.75rem;justify-content:center;">
                    <a href="/articles/" class="btn btn-secondary">Browse Articles</a>
                    <a href="/cases/" class="btn btn-ghost">Browse Cases</a>
                </div>
            </div>
        <?php else: ?>
            <p style="color:var(--text-muted);margin-bottom:1rem;"><?= $total ?> result<?= $total !== 1 ? 's' : '' ?> found.</p>
            <div class="search-results-list">
                <?php foreach ($results as $r): ?>
                    <?php
                    $typeLabel = $r['type'] === 'article' ? 'Article' : 'Case';
                    $url = $r['type'] === 'article'
                        ? '/articles/' . h($r['slug'])
                        : '/cases/' . h($r['slug']);
                    $ts = $r['date'] ? strtotime($r['date']) : false;
                    $date = $ts ? date('M j, Y', $ts) : '';
                    ?>
                    <a href="<?= $url ?>" class="search-result-item">
                        <div class="search-result-head">
                            <span class="search-type"><?= $typeLabel ?></span>
                            <span class="search-result-date"><?= $date ?></span>
                        </div>
                        <h3 class="search-result-title"><?= h($r['title']) ?></h3>
                        <?php if (!empty($r['excerpt'])): ?>
                            <p class="search-result-excerpt"><?= h(truncate($r['excerpt'], 200)) ?></p>
                        <?php endif; ?>
                    </a>
                <?php endforeach; ?>
            </div>

            <?php if ($total > $perPage): ?>
                <?php $totalPages = (int)ceil($total / $perPage); ?>
                <nav class="pagination" style="margin-top:2rem;display:flex;gap:0.5rem;justify-content:center;align-items:center;">
                    <?php if ($page > 1): ?>
                        <a href="/search?q=<?= urlencode($query) ?>&page=<?= $page - 1 ?>" class="btn btn-secondary">&laquo; Previous</a>
                    <?php endif; ?>
                    <span style="color:var(--text-muted);padding:0 1rem;">Page <?= $page ?> of <?= $totalPages ?></span>
                    <?php if ($page < $totalPages): ?>
                        <a href="/search?q=<?= urlencode($query) ?>&page=<?= $page + 1 ?>" class="btn btn-secondary">Next &raquo;</a>
                    <?php endif; ?>
                </nav>
            <?php endif; ?>
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
</style>

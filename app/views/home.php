<section class="section hero">
    <div class="container">
        <h1>Parent Data Force</h1>
        <p class="hero-lead">Independent special education and public accountability advocacy. Tracking complaints, records, outcomes, and systemic patterns across Massachusetts.</p>
        <div class="hero-stats">
            <div class="hero-stat"><span class="stat-number"><?= $districtCount ?? 0 ?></span> Districts Tracked</div>
        </div>
    </div>
</section>

<?php if (!empty($featured)): ?>
<section class="section">
    <div class="container">
        <h2>Featured Articles</h2>
        <div class="article-list">
            <?php foreach ($featured as $a): ?>
            <article class="article-card">
                <a href="/articles/<?= h($a['slug']) ?>">
                    <h3><?= h($a['title']) ?></h3>
                    <?php if (!empty($a['excerpt'])): ?><p><?= h(truncate($a['excerpt'], 200)) ?></p><?php endif; ?>
                    <time><?= h(format_date($a['published_date'])) ?></time>
                </a>
            </article>
            <?php endforeach; ?>
        </div>
    </div>
</section>
<?php endif; ?>

<?php if (!empty($recentCases)): ?>
<section class="section">
    <div class="container">
        <h2>Recent Cases</h2>
        <div class="case-list">
            <?php foreach ($recentCases as $c): ?>
            <article class="case-card">
                <a href="/cases/<?= h($c['slug'] ?? $c['case_number']) ?>">
                    <h3><?= h($c['title']) ?></h3>
                    <div class="case-card-meta">
                        <span class="badge status-<?= h($c['status']) ?>"><?= h(ucfirst($c['status'])) ?></span>
                        <span><?= h(format_date($c['filed_date'])) ?></span>
                    </div>
                </a>
            </article>
            <?php endforeach; ?>
        </div>
    </div>
</section>
<?php endif; ?>

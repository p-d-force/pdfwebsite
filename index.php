<?php







declare(strict_types=1);







require_once __DIR__ . '/config.php';







require_once __DIR__ . '/includes/Database.php';







require_once __DIR__ . '/includes/helpers.php';







require_once __DIR__ . '/includes/shortcodes.php';















$featured_articles = Database::fetchAll(







    'SELECT a.*, GROUP_CONCAT(DISTINCT d.code) as district_codes







     FROM articles a







     LEFT JOIN article_district_links adl ON a.id = adl.article_id







     LEFT JOIN districts d ON adl.district_id = d.id







     WHERE a.status = ?







     GROUP BY a.id







     ORDER BY a.featured DESC, a.published_at DESC







     LIMIT 6',







    ['published']







);















$recent_updates = Database::fetchAll(







    'SELECT u.*, c.case_id as case_ref







     FROM updates u







     LEFT JOIN cases c ON u.related_case_id = c.case_id







     ORDER BY u.created_at DESC







     LIMIT 6'







);















$stats = [







    'articles'   => (int)Database::fetchColumn('SELECT COUNT(*) FROM articles WHERE status = ?', ['published']),







    'cases'      => (int)Database::fetchColumn('SELECT COUNT(*) FROM cases WHERE status != ?', ['archived']),







    'districts'  => (int)Database::fetchColumn('SELECT COUNT(*) FROM districts WHERE status = ?', ['active']),







    'active_interests' => (int)Database::fetchColumn('SELECT COUNT(*) FROM active_interests WHERE status = ?', ['active']),







    'prr_entries' => 0,







];







// Try to get PRR tracker count if table exists







try {







    $stats['prr_entries'] = (int)Database::fetchColumn('SELECT COUNT(*) FROM case_documents');







} catch (Exception $e) {}







if ($stats['prr_entries'] == 0) {







    try {







        $stats['prr_entries'] = (int)Database::fetchColumn('SELECT COUNT(*) FROM case_events');







    } catch (Exception $e) {}







}















$subscribed  = isset($_GET['subscribed']);







$subError    = isset($_GET['subscribe_error']);















$page_title       = 'Home';







$page_description = 'Parent Data Force — Data-driven advocacy for families. Tracking complaints, records, outcomes, and systemic patterns across Massachusetts districts.';







include __DIR__ . '/includes/head.php';







include __DIR__ . '/includes/header.php';















if ($subscribed): ?>







    <div style="background:rgba(34,197,94,0.1);border-bottom:1px solid rgba(34,197,94,0.3);padding:0.8rem;text-align:center;color:var(--success);font-size:0.9rem;">







        Subscribed successfully! You'll receive updates on new articles, case filings, and data releases.







    </div>







<?php elseif ($subError): ?>







    <div style="background:rgba(239,68,68,0.1);border-bottom:1px solid rgba(239,68,68,0.3);padding:0.8rem;text-align:center;color:var(--danger);font-size:0.9rem;">







        Subscription failed. Please try again with a valid email address.







    </div>







<?php endif; ?>




























<section class="hero" id="hero">







    <div class="hero-bg"></div>







    <div class="hero-overlay"></div>







    <div class="hero-content">







        <div class="hero-tagline"><?php echo SITE_TAGLINE; ?></div>







        <h1 class="hero-title">







            <span class="hero-title-line">Data-Driven Advocacy</span>







            <span class="hero-title-accent">for Families</span>







        </h1>







        <p class="hero-subtitle">







            Independent special education and public accountability advocacy. 







            Tracking complaints, records, outcomes, and systemic patterns across Massachusetts districts.







        </p>







        <div class="hero-cta">







            <a href="/cases/" class="btn btn-primary">







                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">







                    <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>







                </svg>







                View Cases







            </a>







            <a href="/articles/" class="btn btn-secondary">







                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">







                    <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>







                </svg>







                Read Articles







            </a>







            <a href="/submit/" class="btn btn-tip">







                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">







                    <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>







                </svg>







                Submit a Tip







            </a>







            <a href="/data/" class="btn btn-ghost">







                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">







                    <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>







                </svg>







                Explore Data







            </a>







        </div>







        <div class="hero-stats">







            <div class="stat" data-animate>







                <span class="stat-value"><?php echo $stats['districts']; ?></span>







                <span class="stat-label">Districts Tracked</span>







            </div>







            <div class="stat" data-animate>







                <span class="stat-value"><?php echo $stats['active_interests']; ?></span>







                <span class="stat-label">Active Interests</span>







            </div>







            <div class="stat" data-animate>







                <span class="stat-value"><?php echo $stats['articles']; ?></span>







                <span class="stat-label">Articles Published</span>







            </div>







            <div class="stat" data-animate>







                <span class="stat-value"><?php echo $stats['prr_entries'] ?: $stats['cases']; ?></span>







                <span class="stat-label">Evidence Items</span>







            </div>







        </div>







    </div>







    <div class="hero-scroll-indicator">







        <span>Scroll to explore</span>







        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">







            <path d="M19 14l-7 7m0 0l-7-7m7 7V3"/>







        </svg>







    </div>







</section>















<section class="section" id="featured">







    <div class="container">







        <div class="section-header" data-animate>







            <span class="section-tag">Latest Articles</span>







            <h2 class="section-title">Research, Analysis &amp; Advocacy</h2>







            <p class="section-subtitle">







                Data-driven reporting on special education, public records, and systemic accountability across Massachusetts.







            </p>







        </div>















        <?php if (empty($featured_articles)): ?>







            <div class="empty-state" data-animate>







                <p>Articles coming soon. Our research and advocacy reporting will appear here.</p>







                <a href="/cases/" class="btn btn-secondary" style="margin-top:1rem;">Browse Cases Instead</a>







            </div>







        <?php else: ?>







            <div class="articles-grid" data-animate>







                <?php foreach ($featured_articles as $article): ?>







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







                            </div>







                            <h3 class="article-card-title">







                                <a href="/articles/<?php echo h($article['slug']); ?>"><?php echo h($article['title']); ?></a>







                            </h3>







                            <p class="article-card-excerpt">







                                <?php echo h($article['excerpt'] ?: excerpt($article['body'])); ?>







                            </p>







                            <div class="article-card-footer">







                                <span class="article-read-time"><?php echo $article['read_time'] ?: read_time($article['body']); ?> min read</span>







                                <a href="/articles/<?php echo h($article['slug']); ?>" class="resource-link">Read Article</a>







                            </div>







                        </div>







                    </article>







                <?php endforeach; ?>







            </div>







        <?php endif; ?>















        <div style="text-align:center;margin-top:2rem;" data-animate>







            <a href="/articles/" class="btn btn-secondary">View All Articles</a>







        </div>







    </div>







</section>















<section class="section section-dark" id="quick-links">







    <div class="container">







        <div class="section-header" data-animate>







            <span class="section-tag">Explore</span>







            <h2 class="section-title">What We Track</h2>







            <p class="section-subtitle">







                Every investigation, public records request, state determination, and systemic pattern — organized and accessible.







            </p>







        </div>







        <div class="resources-grid" data-animate>







            <article class="resource-card">







                <h3 class="resource-title">Case Directory</h3>







                <p class="resource-excerpt">Active investigations, public records requests, appeals, and state determinations with full timelines and documents.</p>







                <a href="/cases/" class="resource-link">View Cases</a>







            </article>







            <article class="resource-card">







                <h3 class="resource-title">Data Browser</h3>







                <p class="resource-excerpt">Interactive exploration of DESE restraint and seclusion data, district analytics, and statewide patterns.</p>







                <a href="/data/" class="resource-link">Explore Data</a>







            </article>







            <article class="resource-card">







                <h3 class="resource-title">District Profiles</h3>







                <p class="resource-excerpt">Per-district pages aggregating cases, data summaries, and advocacy activity across Massachusetts.</p>







                <a href="/districts/" class="resource-link">View Districts</a>







            </article>







            <article class="resource-card">







                <h3 class="resource-title">Appearances &amp; Media</h3>







                <p class="resource-excerpt">Public comments, school committee testimony, press coverage, and advocacy media appearances.</p>







                <a href="/appearances/" class="resource-link">View Appearances</a>







            </article>







        </div>







    </div>







</section>















<!-- Tracked Districts Coverage -->







<section class="section" id="district-coverage">







    <div class="container">







        <div class="section-header" data-animate>







            <span class="section-tag">Tracked Districts</span>







            <h2 class="section-title">District Coverage</h2>







            <p class="section-subtitle">







                Each district profiled with case activity, restraint data, and demographic context. Click through for detailed analytics.







            </p>







        </div>







        <div class="resources-grid" data-animate>







            <?php







            $districtCards = Database::fetchAll(







                "SELECT d.code, d.name, d.location,







                    COUNT(DISTINCT c.id) as case_count,







                    COALESCE(COUNT(DISTINCT ai.id), 0) as active_interests







                 FROM districts d







                 LEFT JOIN cases c ON d.code = c.district_code AND c.status != 'archived'







                 LEFT JOIN active_interests ai ON d.code = ai.related_district_code AND ai.status = 'active'







                 WHERE d.status = 'active'







                 GROUP BY d.code, d.name, d.location







                 ORDER BY case_count DESC"







            );







            foreach ($districtCards as $dc):







                $enrollment = 0; $gradeRange = '';







                try {







                    $enrRow = Database::fetch("SELECT COALESCE(SUM(enrollment),0) as total_enr, COUNT(DISTINCT school_name) as school_count FROM restraint_data WHERE (district_name LIKE ? OR district_code = ?) AND school_year='2024-25'", ['%'.$dc['name'].'%', $dc['code']]);







                    if ($enrRow) { $enrollment = (int)$enrRow['total_enr']; $gradeRange = $enrRow['school_count'].' schools'; }







                } catch (Exception $e) {}







            ?>







                <a href="/districts/<?php echo h(strtolower($dc['code'])); ?>/" class="resource-card" style="text-decoration:none;border-left:3px solid var(--accent);">







                    <h3 class="resource-title"><?php echo h($dc['name']); ?></h3>







                    <p class="resource-excerpt" style="font-size:0.85rem;color:var(--text-muted);">







                        <?php if ($gradeRange): echo h($gradeRange); endif; ?>







                        <?php if ($enrollment > 0): echo ' | ' . number_format($enrollment) . ' students'; endif; ?>







                        <?php echo ' | ' . h($dc['location']); ?>







                    </p>







                    <div style="display:flex;gap:0.75rem;margin-top:0.5rem;font-size:0.8rem;">







                        <span style="color:var(--accent-glow);"><?php echo (int)$dc['active_interests']; ?> active interests</span>







                        <span style="color:var(--text-muted);"><?php echo (int)$dc['case_count']; ?> total cases</span>







                    </div>







                </a>







            <?php endforeach; ?>







        </div>







    </div>







</section>















<!-- Data at a Glance: Restraint Trends Chart -->







<?php







$hasRestraintData = false;







try {







    $hasRestraintData = (bool)Database::fetchColumn("SELECT COUNT(*) FROM restraint_data LIMIT 1");







} catch (Exception $e) {}







?>







<?php if ($hasRestraintData): ?>







<section class="section section-dark" id="data-glance">







    <div class="container">







        <div class="section-header" data-animate>







            <span class="section-tag">Data at a Glance</span>







            <h2 class="section-title">Statewide Restraint Trends</h2>







            <p class="section-subtitle">







                Live-computed from over <?php 







                    try { echo number_format((int)Database::fetchColumn("SELECT COUNT(*) FROM restraint_data WHERE is_summary_row=0")); } 







                    catch(Exception $e) { echo '7,800'; }







                ?> school-level records across 9 years. See how restraint rates have changed across Massachusetts.







            </p>







        </div>







        <div style="max-width:900px;margin:0 auto;" data-animate>







            <div style="background:var(--bg-card, var(--bg-elevated));border-radius:16px;padding:1.5rem;border:1px solid var(--border);">







                <div style="height:380px;">







                    <canvas id="homepageRestraintChart"></canvas>







                </div>







                <p style="text-align:center;color:var(--text-muted);font-size:0.85rem;margin-top:0.75rem;">







                    Bars show total physical restraints per school year. Line shows injuries during restraint incidents. 







                    <a href="/data/?tab=restraint" style="color:var(--accent-glow);">Explore the full dataset →</a>







                </p>







            </div>







        </div>







    </div>







</section>







<?php endif; ?>















<?php if (!empty($recent_updates)): ?>







<section class="section" id="updates-ticker">







    <div class="container">







        <div class="section-header" data-animate>







            <span class="section-tag">Recent Activity</span>







            <h2 class="section-title">Latest Updates</h2>







        </div>







        <div class="updates-list" data-animate>







            <?php foreach ($recent_updates as $update): ?>







                <div class="update-item">







                    <div class="update-item-head">







                        <span class="update-date"><?php echo format_date($update['event_date'] ?? $update['created_at']); ?></span>







                        <?php echo severity_badge($update['severity']); ?>







                        <?php if ($update['related_case_id']): ?>







                            <a href="/cases/<?php echo h($update['case_ref'] ?? $update['related_case_id']); ?>" class="update-case-link"><?php echo h($update['related_case_id']); ?></a>







                        <?php endif; ?>







                    </div>







                    <h4 class="update-title"><?php echo h($update['title']); ?></h4>







                    <?php if ($update['body']): ?>







                        <p class="update-body"><?php echo h(truncate($update['body'], 300)); ?></p>







                    <?php endif; ?>







                </div>







            <?php endforeach; ?>







        </div>







        <div style="text-align:center;margin-top:1.5rem;" data-animate>







            <a href="/cases/" class="btn btn-ghost">View All Cases</a>







        </div>







    </div>







</section>







<?php endif; ?>















<section class="section section-accent" id="cta-bottom">







    <div class="container" data-animate>







        <div class="cta-banner">







            <h2 class="section-title">Have Information to Share?</h2>







            <p class="section-subtitle" style="max-width:100%;">







                If you have tips, documents, or data about special education practices, public records concerns, 







                or systemic issues in Massachusetts school districts, we want to hear from you.







            </p>







            <div class="hero-cta" style="margin-top:1rem;">







                <a href="/submit/" class="btn btn-primary">Submit a Tip</a>







                <a href="/submit/#help" class="btn btn-secondary">Request Help</a>







            </div>







        </div>







    </div>







</section>















<?php







include __DIR__ . '/includes/footer.php';








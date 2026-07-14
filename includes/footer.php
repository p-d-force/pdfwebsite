<?php declare(strict_types=1); ?>
    </main>

    <footer class="footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-brand">
                    <div class="footer-logo">
                        <img src="<?php echo asset('images/logo.png'); ?>" alt="Parent Data Force Logo" class="footer-logo-img">
                        <span class="footer-logo-text">PARENT DATA FORCE</span>
                    </div>
                    <p class="footer-tagline"><?php echo SITE_TAGLINE; ?></p>
                    <p class="footer-description">
                        Independent special education and public accountability advocacy. 
                        Tracking complaints, records, outcomes, and systemic patterns across Massachusetts districts.
                    </p>
                </div>

                <div class="footer-nav">
                    <h4 class="footer-nav-title">Content</h4>
                    <ul class="footer-nav-list">
                        <li><a href="/articles/">Articles</a></li>
                        <li><a href="/cases/">Case Directory</a></li>
                        <li><a href="/districts/">Districts</a></li>
                        <li><a href="/data/">Data Browser</a></li>
                        <li><a href="/appearances/">Appearances</a></li>
                        <li><a href="/updates/">Updates</a></li>
                    </ul>
                </div>

                <div class="footer-nav">
                    <h4 class="footer-nav-title">Get Involved</h4>
                    <ul class="footer-nav-list">
                        <li><a href="/submit/">Submit a Tip</a></li>
                        <li><a href="/submit/#help">Request Help</a></li>
                        <li><a href="/submit/#upload">Upload Data</a></li>
                        <li><a href="/about/">About Us</a></li>
                    </ul>
                </div>

                <div class="footer-contact">
                    <h4 class="footer-nav-title">Stay Updated</h4>
                    <form class="subscribe-form" action="/api/subscribe.php" method="post" id="footerSubscribe">
                        <?php echo csrf_field(); ?>
                        <input type="email" name="email" class="form-input" placeholder="Your email address" required style="margin-bottom:0.5rem;">
                        <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;">Subscribe</button>
                    </form>
                    <div class="footer-social" style="margin-top:0.75rem;">
                        <span style="color:var(--text-muted);font-size:0.8rem;">Updates on new articles, case filings, and data releases.</span>
                    </div>
                </div>
            </div>

            <div class="footer-disclaimer">
                <div class="disclaimer-box">
                    <p>
                        Parent Data Force is an independent advocacy initiative. Information provided on this site is for 
                        informational purposes only and does not constitute legal advice. Always consult with a qualified 
                        attorney for legal matters involving special education or public records law.
                    </p>
                </div>
            </div>

            <div class="footer-bottom">
                <p class="copyright">&copy; <?php echo date('Y'); ?> Parent Data Force. All rights reserved.</p>
                <div class="footer-legal">
                    <a href="/about/#privacy">Privacy Policy</a>
                </div>
            </div>
        </div>
    </footer>

    <script src="<?php echo asset('js/main.js'); ?>"></script>
    <script src="<?php echo asset('js/charts.js'); ?>"></script>
    <script src="<?php echo asset('js/charts-compare.js'); ?>"></script>
</body>
</html>

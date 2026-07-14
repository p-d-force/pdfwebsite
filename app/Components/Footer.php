<?php declare(strict_types=1);
namespace App\Components;

/**
 * Footer component.
 * Extracted from includes/footer.php — renders the site footer.
 */
class Footer
{
    public function render(): void
    {
        ?>
        <footer class="footer">
            <div class="footer-container">
                <div class="footer-grid">
                    <div class="footer-col">
                        <h4>Parent Data Force</h4>
                        <p>Independent special education and public accountability advocacy. Tracking complaints, records, and systemic patterns across Massachusetts.</p>
                    </div>
                    <div class="footer-col">
                        <h4>Navigate</h4>
                        <ul class="footer-links">
                            <li><a href="/districts/">Districts</a></li>
                            <li><a href="/cases/">Cases</a></li>
                            <li><a href="/articles/">Articles</a></li>
                            <li><a href="/data/">Data Portal</a></li>
                            <li><a href="/appearances/">Appearances</a></li>
                            <li><a href="/about/">About</a></li>
                        </ul>
                    </div>
                    <div class="footer-col">
                        <h4>Connect</h4>
                        <ul class="footer-links">
                            <li><a href="/submit/">Submit a Tip</a></li>
                            <li><a href="/rss">RSS Feed</a></li>
                            <li><a href="https://www.facebook.com/profile.php?id=61575068592291" target="_blank" rel="noopener">Facebook</a></li>
                        </ul>
                    </div>
                    <div class="footer-col">
                        <h4>Stay Updated</h4>
                        <form action="/api/subscribe" method="POST" class="subscribe-form">
                            <input type="hidden" name="csrf_token" value="<?= csrf_token() ?>">
                            <input type="email" name="email" placeholder="Your email address" required class="subscribe-input">
                            <button type="submit" class="btn btn-primary subscribe-btn">Subscribe</button>
                        </form>
                    </div>
                </div>
                <div class="footer-bottom">
                    <p>&copy; <?= date('Y') ?> Parent Data Force. All rights reserved.</p>
                </div>
            </div>
        </footer>
        <?php
    }
}

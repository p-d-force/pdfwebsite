<?php declare(strict_types=1);
namespace App\Components;

/**
 * Navigation bar component.
 * Extracted from includes/header.php — renders the main site nav.
 */
class Nav
{
    public function render(): void
    {
        $currentPath = $_SERVER['REQUEST_URI'] ?? '/';
        ?>
        <nav class="nav" id="nav">
            <div class="nav-container">
                <a href="/" class="nav-logo">
                    <img src="<?= asset('images/logo.png') ?>" alt="Parent Data Force Logo" class="nav-logo-img">
                </a>

                <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false">
                    <span class="nav-toggle-bar"></span>
                    <span class="nav-toggle-bar"></span>
                    <span class="nav-toggle-bar"></span>
                </button>

                <div class="nav-links" id="nav-links">
                    <a href="/districts/" class="nav-link <?= str_starts_with($currentPath, '/districts') ? 'active' : '' ?>">Districts</a>
                    <a href="/cases/" class="nav-link <?= str_starts_with($currentPath, '/cases') ? 'active' : '' ?>">Cases</a>
                    <a href="/articles/" class="nav-link <?= str_starts_with($currentPath, '/articles') ? 'active' : '' ?>">Articles</a>
                    <a href="/data/" class="nav-link <?= str_starts_with($currentPath, '/data') ? 'active' : '' ?>">Data Portal</a>
                    <a href="/appearances/" class="nav-link <?= str_starts_with($currentPath, '/appearances') ? 'active' : '' ?>">Appearances</a>
                    <a href="/about/" class="nav-link <?= str_starts_with($currentPath, '/about') ? 'active' : '' ?>">About</a>
                    <a href="/submit/" class="nav-link <?= str_starts_with($currentPath, '/submit') ? 'active' : '' ?>">Submit a Tip</a>
                    <a href="https://www.facebook.com/profile.php?id=61575068592291" class="nav-link nav-link-external" target="_blank" rel="noopener">Facebook</a>
                    <a href="/about#donate" class="btn btn-primary nav-cta">Donate</a>
                </div>
            </div>
        </nav>
        <?php
    }
}

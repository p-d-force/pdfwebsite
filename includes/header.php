<?php declare(strict_types=1); ?>







<body>
    <?php if (defined('SITE_UNDER_CONSTRUCTION') && SITE_UNDER_CONSTRUCTION): ?>
    <div class="construction-notice">
        &#x1f6a7; This site is under active development. Some features may be incomplete &mdash; check back as we expand.
    </div>
    <?php endif; ?>
    <?php if (!empty($page_under_development)): ?>
    <div class="construction-notice" style="background:rgba(239,68,68,0.08);border-bottom:1px solid rgba(239,68,68,0.25);color:var(--danger);">
        &#x1f6a7; This page is under development. Content may change or be incomplete.
    </div>
    <?php endif; ?>







    <nav class="nav" id="nav">







        <div class="nav-container">







            <a href="/" class="nav-logo">







                <img src="<?php echo asset('images/logo.png'); ?>" alt="Parent Data Force Logo" class="nav-logo-img">







                <span class="nav-logo-text">PARENT DATA FORCE</span>







            </a>







            <button class="nav-toggle" id="navToggle" aria-label="Toggle navigation">







                <span class="hamburger"></span>







            </button>







            <ul class="nav-menu" id="navMenu">
                <li><a href="/data/" class="nav-link<?php echo str_starts_with($_SERVER['REQUEST_URI'] ?? '', '/data') ? ' active' : ''; ?>">Data</a></li>







                <li><a href="/districts/" class="nav-link<?php echo str_starts_with($_SERVER['REQUEST_URI'] ?? '', '/districts') ? ' active' : ''; ?>">Districts</a></li>







                <li><a href="/cases/" class="nav-link<?php echo str_starts_with($_SERVER['REQUEST_URI'] ?? '', '/cases') ? ' active' : ''; ?>">Current Focus</a></li>







                <li><a href="/articles/" class="nav-link<?php echo str_starts_with($_SERVER['REQUEST_URI'] ?? '', '/articles') ? ' active' : ''; ?>">Articles</a></li>







                <li><a href="/appearances/" class="nav-link<?php echo str_starts_with($_SERVER['REQUEST_URI'] ?? '', '/speeches') ? ' active' : ''; ?>">Appearances</a></li>







                <li><a href="/resources/" class="nav-link<?php echo str_starts_with($_SERVER['REQUEST_URI'] ?? '', '/resources') ? ' active' : ''; ?>">Resources</a></li>







                <li><a href="/about/" class="nav-link<?php echo str_starts_with($_SERVER['REQUEST_URI'] ?? '', '/about') ? ' active' : ''; ?>">About</a></li>







                <li>







                    <a href="/search.php" class="nav-icon" aria-label="Search" title="Search">







                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">







                            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>







                        </svg>







                    </a>







                </li>







                <li>







                    <a href="https://www.facebook.com/ParentDataForce" class="nav-icon" aria-label="Facebook" title="Parent Data Force on Facebook" target="_blank" rel="noopener">







                        <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">







                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>







                        </svg>







                    </a>







                </li>







                <li><a href="/submit/" class="nav-link nav-link-tip">Submit Data</a></li>







                <li><a href="/donate/" class="btn btn-primary" style="font-size:0.85rem;padding:0.45rem 0.85rem;">❤ Donate</a></li>















                        <circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>







                    </svg>











                        <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>







                    </svg>







                </button></li>







            </ul>







        </div>







    </nav>















    <main>








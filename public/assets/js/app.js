// Parent Data Force — Main JavaScript
(function () {
    'use strict';


    function initNav() {
        const nav = document.getElementById('nav');
        const toggle = document.getElementById('navToggle');
        const menu = document.getElementById('navMenu');

        if (!nav || !toggle || !menu) return;

        toggle.addEventListener('click', () => {
            menu.classList.toggle('open');
            toggle.setAttribute('aria-expanded', String(menu.classList.contains('open')));
        });

        menu.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                menu.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
            });
        });

        window.addEventListener('scroll', () => {
            nav.classList.toggle('nav-scrolled', window.scrollY > 8);
        });
    }

    function initRevealAnimations() {
        const targets = document.querySelectorAll('[data-animate]');
        if (!targets.length) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        targets.forEach(target => observer.observe(target));
    }

    function initDataBrowser() {
        const tabs = document.querySelectorAll('.data-tab');
        if (!tabs.length) return;

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                document.querySelectorAll('.data-tab-content').forEach(c => c.classList.remove('active'));
                const target = document.getElementById('tab-' + tab.dataset.tab);
                if (target) target.classList.add('active');
            });
        });
    }

    function initTableControls() {
        const blocks = document.querySelectorAll('[data-table-controls]');
        if (!blocks.length) return;

        blocks.forEach(block => {
            const tableId = block.getAttribute('data-target-table');
            if (!tableId) return;

            const table = document.getElementById(tableId);
            const tbody = table ? table.querySelector('tbody') : null;
            if (!tbody) return;

            const rows = [...tbody.querySelectorAll('tr')];
            if (!rows.length) return;

            rows.forEach(row => {
                if (!row.dataset.search) {
                    row.dataset.search = row.textContent.toLowerCase();
                }
            });

            const searchInput = block.querySelector('[data-table-search]');
            const countNode = block.querySelector('[data-table-count]');

            if (searchInput) {
                searchInput.addEventListener('input', () => {
                    const q = searchInput.value.toLowerCase();
                    let visible = 0;
                    rows.forEach(row => {
                        const match = row.dataset.search.includes(q);
                        row.style.display = match ? '' : 'none';
                        if (match) visible++;
                    });
                    if (countNode) countNode.textContent = visible + ' of ' + rows.length + ' rows';
                });
            }

            if (countNode) countNode.textContent = rows.length + ' rows';
        });
    }

    function initSearch() {
        const searchField = document.getElementById('siteSearch');
        const searchResults = document.getElementById('searchResults');
        if (!searchField || !searchResults) return;

        let debounceTimer;
        searchField.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            const query = searchField.value.trim();

            if (query.length < 2) {
                searchResults.innerHTML = '';
                searchResults.style.display = 'none';
                return;
            }

            debounceTimer = setTimeout(async () => {
                try {
                    const resp = await fetch('/api/search.php?q=' + encodeURIComponent(query));
                    const data = await resp.json();

                    if (!data.results.length) {
                        searchResults.innerHTML = '<div class="search-empty">No results found.</div>';
                    } else {
                        searchResults.innerHTML = '';
                        data.results.forEach(r => {
                            const url = r.result_type === 'article'
                                ? '/articles/' + encodeURIComponent(r.slug || '')
                                : r.result_type === 'case'
                                    ? '/cases/' + encodeURIComponent(r.case_id || r.slug || '')
                                    : '/speeches/';
                            const label = r.result_type === 'article'
                                ? 'Article'
                                : r.result_type === 'case'
                                    ? 'Case'
                                    : 'Speech';

                            const item = document.createElement('a');
                            item.className = 'search-result-item';
                            item.href = url;

                            const head = document.createElement('div');
                            head.className = 'search-result-head';

                            const typeSpan = document.createElement('span');
                            typeSpan.className = 'search-type';
                            typeSpan.textContent = label;

                            const titleSpan = document.createElement('span');
                            titleSpan.textContent = (r.title || r.slug || '');

                            head.appendChild(typeSpan);
                            head.appendChild(titleSpan);

                            const excerpt = document.createElement('p');
                            excerpt.textContent = ((r.excerpt || '').substring(0, 150));

                            item.appendChild(head);
                            item.appendChild(excerpt);
                            searchResults.appendChild(item);
                        });
                    }
                    searchResults.style.display = 'block';
                } catch (e) {
                    searchResults.innerHTML = '<div class="search-empty">Search unavailable.</div>';
                }
            }, 300);
        });

        document.addEventListener('click', (e) => {
            if (!searchField.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = 'none';
            }
        });
    }

    function initSubscribeForm() {
        const form = document.getElementById('footerSubscribe');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = form.querySelector('button');
            const emailInput = form.querySelector('input[type="email"]');
            const orig = btn.textContent;

            btn.textContent = 'Subscribing...';
            btn.disabled = true;

            try {
                const formData = new FormData(form);
                const resp = await fetch('/api/subscribe.php', {
                    method: 'POST',
                    body: formData,
                    headers: { 'Accept': 'application/json' }
                });
                const data = await resp.json();

                if (data.success) {
                    btn.textContent = 'Subscribed!';
                    btn.classList.add('btn-primary');
                    btn.classList.remove('btn-ghost');
                    emailInput.value = '';
                } else {
                    btn.textContent = orig;
                    btn.disabled = false;
                    alert(data.error || 'Subscription failed. Try again.');
                }
            } catch (err) {
                btn.textContent = orig;
                btn.disabled = false;
            }
        });
    }

    function init() {
        initNav();
        initRevealAnimations();
        initDataBrowser();
        initTableControls();
        initSearch();
        initSubscribeForm();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

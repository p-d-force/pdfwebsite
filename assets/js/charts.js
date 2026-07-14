// Parent Data Force — Chart.js Integration
(function () {
    'use strict';

    // Colors
    const EMBER = 'rgba(255, 90, 31, 0.7)';
    const EMBER_SOLID = 'rgba(255, 90, 31, 1)';
    const GLOW = 'rgba(255, 163, 102, 0.5)';
    const GLOW_SOLID = 'rgba(255, 163, 102, 1)';
    const MUTED = '#a0a0a0';
    const GRID = 'rgba(255,255,255,0.05)';

    function initCharts() {
        initShortcodeCharts();
        initRestraintTrendsChart();
        initHomepageRestraintChart();
    }

    function initShortcodeCharts() {
        const chartWrappers = document.querySelectorAll('.shortcode-chart');
        if (!chartWrappers.length) return;

        chartWrappers.forEach(wrapper => {
            const type = wrapper.dataset.chartType;
            const district = wrapper.dataset.chartDistrict || '';
            const canvas = wrapper.querySelector('canvas');
            if (!canvas) return;

            if (type === 'restraint-years') {
                loadRestraintTrends(canvas);
            } else if (type === 'restraint-district') {
                loadDistrictRestraint(canvas, district);
            }
        });
    }

    function initRestraintTrendsChart() {
        const canvas = document.getElementById('restraintTrendsChart');
        if (!canvas) return;
        loadRestraintTrends(canvas);
    }

    function initHomepageRestraintChart() {
        const canvas = document.getElementById('homepageRestraintChart');
        if (!canvas) return;
        loadRestraintTrends(canvas, true);
    }

    async function loadRestraintTrends(canvas, compact) {
        try {
            const resp = await fetch('/api/data.php?action=restraint');
            if (!resp.ok) throw new Error('API error');
            const result = await resp.json();

            // Use computed chart data if available, else fallback
            let chartData = result.chart;
            if (!chartData || !chartData.labels || !chartData.labels.length) {
                chartData = result.fallback;
            }
            if (!chartData || !chartData.labels) {
                throw new Error('No data');
            }

            const fontFamily = 'Inter, -apple-system, BlinkMacSystemFont, sans-serif';

            new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: chartData.labels,
                    datasets: [
                        {
                            label: 'Total Restraints',
                            data: chartData.restraints,
                            backgroundColor: EMBER,
                            borderColor: EMBER_SOLID,
                            borderWidth: 1,
                            borderRadius: compact ? 2 : 3,
                            yAxisID: 'y',
                        },
                        {
                            label: 'Total Injuries',
                            data: chartData.injuries,
                            backgroundColor: GLOW,
                            borderColor: GLOW_SOLID,
                            borderWidth: 1,
                            yAxisID: 'y1',
                            type: 'line',
                            tension: 0.3,
                            pointRadius: compact ? 2 : 3,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index',
                    },
                    plugins: {
                        legend: {
                            display: !compact,
                            position: compact ? 'bottom' : 'top',
                            labels: {
                                color: MUTED,
                                font: { family: fontFamily, size: compact ? 10 : 12 },
                                usePointStyle: true,
                                padding: compact ? 10 : 16,
                            },
                        },
                        tooltip: {
                            backgroundColor: 'rgba(20, 20, 20, 0.95)',
                            titleColor: '#fff',
                            bodyColor: '#ccc',
                            borderColor: 'rgba(255, 90, 31, 0.3)',
                            borderWidth: 1,
                        },
                    },
                    scales: {
                        y: {
                            type: 'linear',
                            position: 'left',
                            title: {
                                display: !compact,
                                text: 'Total Restraints',
                                color: MUTED,
                                font: { family: fontFamily, size: 11 },
                            },
                            ticks: {
                                color: MUTED,
                                font: { family: fontFamily, size: compact ? 9 : 10 },
                                callback: function(v) { return v >= 1000 ? (v/1000).toFixed(0) + 'k' : v; },
                            },
                            grid: { color: GRID },
                            beginAtZero: true,
                        },
                        y1: {
                            type: 'linear',
                            position: 'right',
                            title: {
                                display: !compact,
                                text: 'Total Injuries',
                                color: MUTED,
                                font: { family: fontFamily, size: 11 },
                            },
                            ticks: {
                                color: MUTED,
                                font: { family: fontFamily, size: compact ? 9 : 10 },
                            },
                            grid: { display: false },
                            beginAtZero: true,
                        },
                        x: {
                            ticks: {
                                color: MUTED,
                                font: { family: fontFamily, size: compact ? 9 : 10 },
                                maxRotation: compact ? 45 : 0,
                            },
                            grid: { color: GRID },
                        },
                    },
                },
            });
        } catch (e) {
            console.warn('Chart load failed:', e);
            canvas.parentElement.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:1.5rem;">Chart data loading from live database...</p>';
        }
    }

    async function loadDistrictRestraint(canvas, district) {
        try {
            const resp = await fetch('/api/data.php?action=restraint_districts&district=' + encodeURIComponent(district));
            if (!resp.ok) throw new Error('API error');
            const result = await resp.json();

            if (!result.districts || !result.districts.length) {
                canvas.parentElement.innerHTML = '<p style="color:var(--text-muted);text-align:center;">No restraint data for this district yet.</p>';
                return;
            }

            // Group by year
            const byYear = {};
            result.districts.forEach(r => {
                const yr = r.school_year;
                if (!byYear[yr]) byYear[yr] = { restraints: 0, injuries: 0 };
                if (!r.total_restraints_suppressed) byYear[yr].restraints += parseInt(r.total_restraints) || 0;
                if (!r.total_injuries_suppressed) byYear[yr].injuries += parseInt(r.total_injuries) || 0;
            });

            const years = Object.keys(byYear).sort();
            const restraints = years.map(y => byYear[y].restraints);
            const injuries = years.map(y => byYear[y].injuries);

            new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: years,
                    datasets: [
                        { label: 'Restraints', data: restraints, backgroundColor: EMBER, yAxisID: 'y' },
                        { label: 'Injuries', data: injuries, backgroundColor: GLOW, yAxisID: 'y1', type: 'line', tension: 0.3 },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: MUTED } } },
                    scales: {
                        y: { ticks: { color: MUTED }, grid: { color: GRID } },
                        y1: { position: 'right', ticks: { color: MUTED }, grid: { display: false } },
                        x: { ticks: { color: MUTED }, grid: { color: GRID } },
                    },
                },
            });
        } catch (e) {
            canvas.parentElement.innerHTML = '<p style="color:var(--text-muted);text-align:center;">District data loading...</p>';
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCharts);
    } else {
        initCharts();
    }
})();

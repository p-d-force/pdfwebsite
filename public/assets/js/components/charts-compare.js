// Parent Data Force — District Comparison Chart
// Include AFTER charts.js on pages with the compare panel.
(function () {
    'use strict';

    var _compareSelections = [];
    var _allDistrictsData = [];
    var _compareChart = null;

    var COMPARE_COLORS = [
        'rgba(255,90,31,0.7)',    // EMBER
        'rgba(255,163,102,0.7)',  // GLOW
        'rgba(80,160,255,0.7)',   // BLUE
        'rgba(120,200,80,0.7)',   // GREEN
        'rgba(200,140,255,0.7)',  // PURPLE
        'rgba(255,210,60,0.7)',   // GOLD
    ];

    var COMPARE_BORDERS = [
        'rgba(255,90,31,1)',
        'rgba(255,163,102,1)',
        'rgba(80,160,255,1)',
        'rgba(120,200,80,1)',
        'rgba(200,140,255,1)',
        'rgba(255,210,60,1)',
    ];

    var COUNT_METRICS = [
        { key: 'total_restraints', label: 'Total Restraints' },
        { key: 'enrollment',       label: 'Enrollment' },
    ];

    var PCT_METRICS = [
        { key: 'restraint_rate',    label: 'Rate/100' },
        { key: 'sped_pct',          label: 'SPED%' },
        { key: 'low_income_pct',    label: 'Low Income%' },
        { key: 'el_pct',            label: 'EL%' },
        { key: 'oss_pct',           label: 'OSS%' },
        { key: 'attendance_rate',   label: 'Attendance%' },
        { key: 'chr_absent_pct',    label: 'Chr Absent%' },
    ];

    function _parseVal(raw) {
        if (raw === null || raw === undefined || raw === '-' || raw === '') return null;
        var n = Number(raw);
        return isNaN(n) ? null : n;
    }

    function _rebuildDropdownSelections() {
        var selA = document.getElementById('compare-district-a');
        var selB = document.getElementById('compare-district-b');
        var aVal = selA ? selA.value : '';
        var bVal = selB ? selB.value : '';
        var similar = _compareSelections.slice(2);
        _compareSelections = [];
        if (aVal) _compareSelections.push(aVal);
        if (bVal && bVal !== aVal) _compareSelections.push(bVal);
        similar.forEach(function(name) {
            if (_compareSelections.indexOf(name) === -1) {
                _compareSelections.push(name);
            }
        });
    }

    function _renderSimilarTags() {
        var listEl = document.getElementById('similar-districts-list');
        if (!listEl) return;
        var similar = _compareSelections.slice(2);
        listEl.innerHTML = '';
        similar.forEach(function(name) {
            var tag = document.createElement('span');
            tag.className = 'similar-district-tag';
            var txt = document.createTextNode(name);
            var btn = document.createElement('button');
            btn.textContent = '\u00D7';
            btn.addEventListener('click', (function(n) {
                return function() { _removeSimilarDistrict(n); };
            })(name));
            tag.appendChild(txt);
            tag.appendChild(btn);
            listEl.appendChild(tag);
        });
    }

    function _removeSimilarDistrict(name) {
        var idx = _compareSelections.indexOf(name);
        if (idx >= 2) {
            _compareSelections.splice(idx, 1);
            _renderSimilarTags();
            if (_compareSelections.length >= 2) {
                renderCompareChart(_allDistrictsData, _compareSelections);
            }
        }
    }

    function initDistrictCompare() {
        var dataEl = document.getElementById('compare-districts-data');
        if (!dataEl) return;

        try {
            _allDistrictsData = JSON.parse(dataEl.textContent);
        } catch (e) {
            return;
        }

        if (!_allDistrictsData.length) return;

        var selA = document.getElementById('compare-district-a');
        var selB = document.getElementById('compare-district-b');
        if (!selA || !selB) return;

        var names = _allDistrictsData.map(function(d) { return d.district_name; }).sort();

        var optHtml = '<option value="">-- Select District --</option>';
        names.forEach(function(n) {
            optHtml += '<option value="' + n.replace(/"/g, '&quot;') + '">' + n + '</option>';
        });
        selA.innerHTML = optHtml;
        selB.innerHTML = optHtml;

        function onDropdownChange() {
            _rebuildDropdownSelections();
            _renderSimilarTags();
            if (_compareSelections.length >= 2) {
                renderCompareChart(_allDistrictsData, _compareSelections);
            }
        }

        selA.addEventListener('change', onDropdownChange);
        selB.addEventListener('change', onDropdownChange);

        var similarSelect = document.getElementById('similar-district-select');
        var similarAdd    = document.getElementById('similar-district-add');

        if (similarSelect) {
            similarSelect.innerHTML = optHtml;
        }

        if (similarAdd && similarSelect) {
            similarAdd.addEventListener('click', function() {
                var name = similarSelect.value;
                if (!name) return;
                if (_compareSelections.indexOf(name) !== -1) return;
                addDistrictToCompare(name);
            });
        }
    }

    function addDistrictToCompare(name) {
        if (_compareSelections.indexOf(name) !== -1) return;
        _compareSelections.push(name);
        _renderSimilarTags();
        if (_compareSelections.length >= 2) {
            renderCompareChart(_allDistrictsData, _compareSelections);
        }
    }

    function renderCompareChart(data, selectedNames) {
        var canvas = document.getElementById('districtCompareChart');
        if (!canvas) return;

        if (_compareChart) {
            _compareChart.destroy();
            _compareChart = null;
        }

        var selected = [];
        selectedNames.forEach(function(name) {
            var match = null;
            for (var i = 0; i < data.length; i++) {
                if (data[i].district_name === name) { match = data[i]; break; }
            }
            if (match) selected.push(match);
        });

        if (selected.length < 2) return;

        var allMetricLabels = COUNT_METRICS.concat(PCT_METRICS).map(function(m) { return m.label; });
        var nCount = COUNT_METRICS.length;
        var nPct = PCT_METRICS.length;

        var datasets = [];

        selected.forEach(function(district, i) {
            var colorIdx = i % COMPARE_COLORS.length;
            var bg = COMPARE_COLORS[colorIdx];
            var border = COMPARE_BORDERS[colorIdx];
            var bgFaded = bg.replace(/[\d.]+\)$/, function(m) {
                var v = parseFloat(m);
                return Math.min(v * 0.55, 0.55).toFixed(2) + ')';
            });

            var countValues = COUNT_METRICS.map(function(m) { return _parseVal(district[m.key]); })
                .concat(new Array(nPct).fill(null));

            datasets.push({
                label: district.district_name,
                data: countValues,
                backgroundColor: bg,
                borderColor: border,
                borderWidth: 1,
                borderRadius: 4,
                yAxisID: 'yCounts',
                order: 1,
            });

            var pctValues = new Array(nCount).fill(null)
                .concat(PCT_METRICS.map(function(m) { return _parseVal(district[m.key]); }));

            datasets.push({
                label: district.district_name + ' %',
                data: pctValues,
                backgroundColor: bgFaded,
                borderColor: border,
                borderWidth: 1,
                borderRadius: 4,
                yAxisID: 'yPcts',
                order: 0,
            });
        });

        _compareChart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: allMetricLabels,
                datasets: datasets,
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#a0a0a0',
                            font: { family: 'Inter, sans-serif' },
                            filter: function(item) {
                                return item.text.indexOf(' %') === -1;
                            },
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                if (ctx.raw === null) return '';
                                var name = ctx.dataset.label.replace(' %', '');
                                var val = ctx.raw;
                                return name + ': ' + val.toLocaleString();
                            },
                        },
                    },
                },
                scales: {
                    yCounts: {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Count',
                            color: '#a0a0a0',
                            font: { family: 'Inter, sans-serif' },
                        },
                        ticks: { color: '#a0a0a0' },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        beginAtZero: true,
                    },
                    yPcts: {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Percentage / Rate',
                            color: '#a0a0a0',
                            font: { family: 'Inter, sans-serif' },
                        },
                        ticks: {
                            color: '#a0a0a0',
                            callback: function(v) { return v + '%'; },
                        },
                        grid: { display: false },
                        beginAtZero: true,
                        max: 100,
                    },
                    x: {
                        ticks: {
                            color: '#a0a0a0',
                            maxRotation: 45,
                            minRotation: 0,
                            font: { size: 10 },
                        },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                    },
                },
            },
        });
    }

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDistrictCompare);
    } else {
        initDistrictCompare();
    }
})();

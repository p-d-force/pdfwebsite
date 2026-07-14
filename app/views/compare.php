<section class="section">
    <div class="container">
        <div class="section-header">
            <span class="section-tag">Data &amp; Analytics</span>
            <h2 class="section-title">Compare Districts</h2>
            <p class="section-subtitle">Side-by-side comparison of restraint data, enrollment, and demographics across Massachusetts school districts.</p>
        </div>

        <div class="filter-bar" style="display:flex;gap:1rem;flex-wrap:wrap;align-items:end;margin-bottom:1.5rem;padding:1rem;background:var(--bg-glass);border-radius:var(--radius-md);border:1px solid var(--border);">
            <div class="form-group" style="margin-bottom:0;">
                <label class="form-label">School Year</label>
                <select name="school_year" class="form-select" onchange="window.location='?school_year='+this.value">
                    <?php foreach ($schoolYears as $sy): ?>
                        <option value="<?= h($sy['school_year']) ?>" <?= $schoolYear === $sy['school_year'] ? 'selected' : '' ?>><?= h($sy['school_year']) ?></option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="form-group" style="margin-bottom:0;">
                <label class="form-label">Filter Districts</label>
                <input type="text" id="districtFilter" class="form-input" placeholder="Type a district name..." style="min-width:250px;">
            </div>
        </div>

        <?php if (empty($compareMap)): ?>
            <div class="empty-state">
                <h3>No comparison data available</h3>
                <p>Try selecting a different school year.</p>
            </div>
        <?php else: ?>
            <div style="overflow-x:auto;">
                <table id="compareTable" class="data-table" style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr>
                            <th data-sort="district" style="cursor:pointer;">District <span class="sort-indicator">⇅</span></th>
                            <th data-sort="enrollment" style="cursor:pointer;">Enrollment <span class="sort-indicator">⇅</span></th>
                            <th data-sort="restraints" style="cursor:pointer;">Total Restraints <span class="sort-indicator">⇅</span></th>
                            <th data-sort="students" style="cursor:pointer;">Students Restrained <span class="sort-indicator">⇅</span></th>
                            <th data-sort="injuries" style="cursor:pointer;">Injuries <span class="sort-indicator">⇅</span></th>
                            <th data-sort="rate" style="cursor:pointer;">Restraint Rate/100 <span class="sort-indicator">⇅</span></th>
                            <th data-sort="sped" style="cursor:pointer;">SPED % <span class="sort-indicator">⇅</span></th>
                            <th data-sort="lowincome" style="cursor:pointer;">Low Income % <span class="sort-indicator">⇅</span></th>
                            <th data-sort="el" style="cursor:pointer;">EL % <span class="sort-indicator">⇅</span></th>
                        </tr>
                    </thead>
                    <tbody id="compareTableBody">
                        <?php foreach ($compareMap as $districtName => $data):
                            $d = $demographicsMap[$districtName] ?? [];
                        ?>
                        <tr data-district="<?= h($districtName) ?>"
                            data-enrollment="<?= $data['enrollment'] ?>"
                            data-restraints="<?= $data['total_restraints'] ?>"
                            data-students="<?= $data['students_restrained'] ?>"
                            data-injuries="<?= $data['total_injuries'] ?>"
                            data-rate="<?= $data['restraint_rate'] ?>"
                            data-sped="<?= h($d['sped_pct'] ?? '0') ?>"
                            data-lowincome="<?= h($d['low_income_pct'] ?? '0') ?>"
                            data-el="<?= h($d['el_pct'] ?? '0') ?>">
                            <td><?= h($districtName) ?></td>
                            <td><?= number_format($data['enrollment']) ?></td>
                            <td><?= number_format($data['total_restraints']) ?></td>
                            <td><?= number_format($data['students_restrained']) ?></td>
                            <td><?= number_format($data['total_injuries']) ?></td>
                            <td><?= number_format($data['restraint_rate'], 2) ?></td>
                            <td><?= isset($d['sped_pct']) ? number_format((float)$d['sped_pct'], 1) . '%' : '—' ?></td>
                            <td><?= isset($d['low_income_pct']) ? number_format((float)$d['low_income_pct'], 1) . '%' : '—' ?></td>
                            <td><?= isset($d['el_pct']) ? number_format((float)$d['el_pct'], 1) . '%' : '—' ?></td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        <?php endif; ?>
    </div>
</section>

<script>
(function() {
    'use strict';

    // District name filter
    var filter = document.getElementById('districtFilter');
    if (filter) {
        filter.addEventListener('input', function() {
            var q = this.value.toLowerCase();
            var rows = document.querySelectorAll('#compareTableBody tr');
            rows.forEach(function(row) {
                var name = (row.getAttribute('data-district') || '').toLowerCase();
                row.style.display = name.indexOf(q) !== -1 ? '' : 'none';
            });
        });
    }

    // Column sorting
    var headers = document.querySelectorAll('#compareTable th[data-sort]');
    headers.forEach(function(header) {
        header.addEventListener('click', function() {
            var sortKey = this.getAttribute('data-sort');
            var tbody = document.getElementById('compareTableBody');
            var rows = Array.from(tbody.querySelectorAll('tr')).filter(function(r) {
                return r.style.display !== 'none';
            });

            var isAsc = this.classList.contains('sort-asc');
            // Reset all headers
            headers.forEach(function(h) { h.classList.remove('sort-asc', 'sort-desc'); });

            rows.sort(function(a, b) {
                var aVal = a.getAttribute('data-' + sortKey) || '';
                var bVal = b.getAttribute('data-' + sortKey) || '';
                var aNum = parseFloat(aVal);
                var bNum = parseFloat(bVal);
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAsc ? bNum - aNum : aNum - bNum;
                }
                return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
            });

            if (isAsc) {
                this.classList.add('sort-desc');
            } else {
                this.classList.add('sort-asc');
            }

            rows.forEach(function(row) { tbody.appendChild(row); });
        });
    });
})();
</script>

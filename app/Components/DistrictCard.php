<?php declare(strict_types=1);
namespace App\Components;

/**
 * DistrictCard — list-view card for the districts index page.
 */
class DistrictCard
{
    public function __construct(private array $district) {}

    public function render(): void
    {
        ?>
        <article class="district-card">
            <a href="/districts/<?= h($this->district['slug']) ?>">
                <h3><?= h($this->district['district_name']) ?></h3>
            </a>
            <div class="card-meta">
                <?php if (!empty($this->district['county'])): ?>
                <span class="badge"><?= h($this->district['county']) ?></span>
                <?php endif; ?>
                <?php if (!empty($this->district['grade_span'])): ?>
                <span class="badge"><?= h($this->district['grade_span']) ?></span>
                <?php endif; ?>
                <?php if (($this->district['case_count'] ?? 0) > 0): ?>
                <span class="badge case-count"><?= $this->district['case_count'] ?> case(s)<?= ($this->district['open_cases'] ?? 0) > 0 ? ' (' . $this->district['open_cases'] . ' open)' : '' ?></span>
                <?php endif; ?>
            </div>
        </article>
        <?php
    }
}

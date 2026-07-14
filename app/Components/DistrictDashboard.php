<?php declare(strict_types=1);
namespace App\Components;

use App\Models\District;

/**
 * DistrictDashboard — reusable district profile page.
 * DB data determines which metrics show, which sections render.
 * Used by DistrictController::show() and anywhere a district profile is needed.
 */
class DistrictDashboard
{
    private array $district;
    private array $cases;
    private array $articles;
    private array $dataSummary;

    public function __construct(array $district)
    {
        $this->district = $district;
        $this->cases = District::cases($district['district_code']);
        $this->articles = District::articles($district['district_code']);
        $this->dataSummary = District::dataSummary(
            $district['district_code'], $district['district_name']
        );
    }

    public function render(): void
    {
        ?>
        <section class="district-dashboard">
            <div class="district-hero">
                <h1><?= h($this->district['district_name']) ?></h1>
                <div class="district-meta">
                    <?php if (!empty($this->district['county'])): ?>
                    <span class="badge"><?= h($this->district['county']) ?></span>
                    <?php endif; ?>
                    <?php if (!empty($this->district['grade_span'])): ?>
                    <span class="badge"><?= h($this->district['grade_span']) ?></span>
                    <?php endif; ?>
                    <?php if (!empty($this->district['total_students'])): ?>
                    <span class="badge"><?= number_format((int)$this->district['total_students']) ?> students</span>
                    <?php endif; ?>
                </div>
                <?php if (!empty($this->district['description'])): ?>
                <p class="district-description"><?= h($this->district['description']) ?></p>
                <?php endif; ?>
            </div>

            <?php $this->renderDataCards(); ?>
            <?php $this->renderCases(); ?>
            <?php $this->renderArticles(); ?>
        </section>
        <?php
    }

    private function renderDataCards(): void
    {
        if (!$this->dataSummary['has_any']) return;
        ?>
        <div class="dashboard-cards">
            <?php if ($r = $this->dataSummary['restraint']): ?>
            <div class="dashboard-card restraint-card">
                <h3>Restraint & Seclusion</h3>
                <div class="card-stat">
                    <span class="stat-value"><?= number_format((int)($r['total_restraints'] ?? 0)) ?></span>
                    <span class="stat-label">Total incidents</span>
                </div>
                <?php if (!empty($r['students_restrained'])): ?>
                <div class="card-stat">
                    <span class="stat-value"><?= number_format((int)$r['students_restrained']) ?></span>
                    <span class="stat-label">Students restrained</span>
                </div>
                <?php endif; ?>
                <?php if (!empty($r['school_count'])): ?>
                <div class="card-stat">
                    <span class="stat-value"><?= number_format((int)$r['school_count']) ?></span>
                    <span class="stat-label">Schools reporting</span>
                </div>
                <?php endif; ?>
            </div>
            <?php endif; ?>

            <?php if ($e = $this->dataSummary['enrollment']): ?>
            <div class="dashboard-card enrollment-card">
                <h3>Enrollment</h3>
                <div class="card-stat">
                    <span class="stat-value"><?= number_format((int)($e['total_enrollment'] ?? 0)) ?></span>
                    <span class="stat-label">Total students</span>
                </div>
                <?php if (isset($e['sped_pct'])): ?>
                <div class="card-stat">
                    <span class="stat-value"><?= number_format((float)$e['sped_pct'], 1) ?>%</span>
                    <span class="stat-label">Students with IEPs</span>
                </div>
                <?php endif; ?>
                <?php if (isset($e['low_income_pct'])): ?>
                <div class="card-stat">
                    <span class="stat-value"><?= number_format((float)$e['low_income_pct'], 1) ?>%</span>
                    <span class="stat-label">Economically disadvantaged</span>
                </div>
                <?php endif; ?>
            </div>
            <?php endif; ?>
        </div>
        <?php
    }

    private function renderCases(): void
    {
        if (empty($this->cases)) return;
        ?>
        <div class="section">
            <h2>Active Cases (<?= count($this->cases) ?>)</h2>
            <div class="case-list">
                <?php foreach ($this->cases as $case): ?>
                <article class="case-card">
                    <a href="/cases/<?= h($case['slug'] ?? $case['case_number']) ?>" class="case-card-link">
                        <h3><?= h($case['title']) ?></h3>
                        <div class="case-card-meta">
                            <span class="badge status-<?= h($case['status'] ?? 'unknown') ?>"><?= h(ucfirst($case['status'] ?? 'Unknown')) ?></span>
                            <?php if (!empty($case['filed_date'])): ?>
                            <span class="case-date">Filed <?= h(format_date($case['filed_date'])) ?></span>
                            <?php endif; ?>
                            <?php if (!empty($case['document_count'])): ?>
                            <span class="case-docs"><?= $case['document_count'] ?> document(s)</span>
                            <?php endif; ?>
                        </div>
                    </a>
                </article>
                <?php endforeach; ?>
            </div>
        </div>
        <?php
    }

    private function renderArticles(): void
    {
        if (empty($this->articles)) return;
        ?>
        <div class="section">
            <h2>Related Articles</h2>
            <div class="article-list">
                <?php foreach ($this->articles as $article): ?>
                <article class="article-card">
                    <a href="/articles/<?= h($article['slug']) ?>">
                        <h3><?= h($article['title']) ?></h3>
                        <?php if (!empty($article['excerpt'])): ?>
                        <p><?= h(truncate($article['excerpt'], 200)) ?></p>
                        <?php endif; ?>
                        <?php if (!empty($article['published_date'])): ?>
                        <time datetime="<?= h($article['published_date']) ?>"><?= h(format_date($article['published_date'])) ?></time>
                        <?php endif; ?>
                    </a>
                </article>
                <?php endforeach; ?>
            </div>
        </div>
        <?php
    }
}

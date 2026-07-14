<?php
declare(strict_types=1);

function render_shortcodes(string $content): string
{
    $shortcodes = [
        '/\[case\s+id="([^"]+)"\]/' => function (array $m): string {
            $case = Database::fetch(
                'SELECT case_id, title, district_code, type, status, summary, current_stage, filed_date, deadline
                 FROM cases WHERE case_id = ? AND status != ?',
                [$m[1], 'archived']
            );
            if (!$case) return '<div class="shortcode-error">Case not found: ' . h($m[1]) . '</div>';

            $statusBadge = status_badge($case['status']);
            $filedDate   = format_date($case['filed_date']);
            $deadline    = format_date($case['deadline']);
            $typeLabel   = case_type_label($case['type']);
            $url         = SITE_URL . '/cases/' . urlencode($case['case_id']);
            $district    = h($case['district_code']);
            $title       = h($case['title']);
            $summary     = h($case['summary']);
            $stage       = h($case['current_stage'] ?: '');

            return <<<HTML
<div class="shortcode-case-card">
    <div class="shortcode-case-header">
        <span class="case-district">{$district}, MA</span>
        {$statusBadge}
    </div>
    <h4 class="shortcode-case-title"><a href="{$url}">{$title}</a></h4>
    <p class="shortcode-case-summary">{$summary}</p>
    <div class="shortcode-case-meta">
        <span><strong>Type:</strong> {$typeLabel}</span>
        <span><strong>Filed:</strong> {$filedDate}</span>
        <span><strong>Deadline:</strong> {$deadline}</span>
        <span><strong>Stage:</strong> {$stage}</span>
    </div>
    <a href="{$url}" class="btn btn-secondary" style="margin-top:0.5rem;font-size:0.85rem;">View Case Details</a>
</div>
HTML;
        },

        '/\[timeline\s+id="([^"]+)"\]/' => function (array $m): string {
            $case = Database::fetch(
                'SELECT timeline FROM cases WHERE case_id = ?',
                [$m[1]]
            );
            if (!$case || !$case['timeline']) return '<div class="shortcode-error">Timeline not found: ' . h($m[1]) . '</div>';

            $events = json_decode($case['timeline'], true);
            if (!$events) return '<div class="shortcode-error">No timeline events available.</div>';

            $items = '';
            foreach ($events as $event) {
                $date = h($event['date'] ?? '');
                $title = h($event['title'] ?? '');
                $desc  = h($event['description'] ?? '');
                $docs  = '';
                if (!empty($event['docs'])) {
                    $docs = '<div class="timeline-docs">';
                    foreach ($event['docs'] as $doc) {
                        if (is_string($doc)) {
                            $docs .= '<span class="timeline-doc">' . h($doc) . '</span>';
                        } else {
                            $docs .= '<a class="timeline-doc" href="' . h($doc['url'] ?? '#') . '" target="_blank" rel="noopener">' . h($doc['label'] ?? 'Document') . '</a>';
                        }
                    }
                    $docs .= '</div>';
                }
                $items .= <<<HTML
<li class="timeline-item">
    <div class="timeline-item-head">
        <span class="timeline-item-title">{$title}</span>
        <span class="timeline-item-date">{$date}</span>
    </div>
    <p>{$desc}</p>
    {$docs}
</li>
HTML;
            }

            return <<<HTML
<div class="shortcode-timeline">
    <h4 class="shortcode-timeline-title">Case Timeline</h4>
    <ul class="timeline-list">{$items}</ul>
</div>
HTML;
        },

        '/\[chart\s+type="([^"]+)"(?:\s+district="([^"]*)")?\]/' => function (array $m): string {
            $type     = $m[1];
            $district = $m[2] ?? '';
            $chartId  = 'chart-' . bin2hex(random_bytes(4));
            return <<<HTML
<div class="shortcode-chart" data-chart-type="{$type}" data-chart-district="{$district}" id="{$chartId}">
    <canvas></canvas>
</div>
HTML;
        },

        '/\[datatable\s+dataset="([^"]+)"\]/' => function (array $m): string {
            $dataset = h($m[1]);
            $tableId = 'datatable-' . bin2hex(random_bytes(4));
            return <<<HTML
<div class="shortcode-datatable" data-dataset="{$dataset}" id="{$tableId}">
    <div class="datatable-controls" data-table-controls data-target-table="{$tableId}-body">
        <input type="text" class="form-input" data-table-search placeholder="Search..." style="max-width:300px;">
        <span class="datatable-count" data-table-count></span>
    </div>
    <div class="repo-table-wrapper">
        <table class="repo-table" id="{$tableId}-body">
            <thead></thead>
            <tbody></tbody>
        </table>
    </div>
</div>
HTML;
        },

        '/\[youtube\s+id="([^"]+)"(?:\s+title="([^"]*)")?\]/' => function (array $m): string {
            $videoId = h($m[1]);
            $title   = !empty($m[2]) ? '<h4 class="shortcode-embed-title">' . h($m[2]) . '</h4>' : '';
            return <<<HTML
<div class="shortcode-video">
    {$title}
    <div class="shortcode-video-wrapper">
        <iframe src="https://www.youtube.com/embed/{$videoId}" allowfullscreen
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            loading="lazy" style="border:none;">
        </iframe>
    </div>
</div>
HTML;
        },
    ];

    foreach ($shortcodes as $pattern => $callback) {
        $content = preg_replace_callback($pattern, $callback, $content);
    }

    return $content;
}

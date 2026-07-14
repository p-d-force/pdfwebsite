<?php
declare(strict_types=1);
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/includes/Database.php';
require_once __DIR__ . '/includes/helpers.php';
require_once __DIR__ . '/includes/shortcodes.php';

header('Content-Type: application/rss+xml; charset=utf-8');

$articles = Database::fetchAll(
    "SELECT title, slug, excerpt, body, category, published_at, author
     FROM articles WHERE status = 'published'
     ORDER BY published_at DESC LIMIT 30"
);

echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
    <title>Parent Data Force</title>
    <link><?php echo SITE_URL; ?>/</link>
    <description>Data-driven advocacy for families navigating special education and public systems. Tracking complaints, records, outcomes, and public accountability.</description>
    <language>en-us</language>
    <lastBuildDate><?php echo date('r'); ?></lastBuildDate>
    <atom:link href="<?php echo SITE_URL; ?>/rss.php" rel="self" type="application/rss+xml"/>
    <generator>Parent Data Force v2</generator>
    <?php foreach ($articles as $article): ?>
    <item>
        <title><?php echo h($article['title']); ?></title>
        <link><?php echo SITE_URL; ?>/articles/<?php echo h($article['slug']); ?></link>
        <guid isPermaLink="true"><?php echo SITE_URL; ?>/articles/<?php echo h($article['slug']); ?></guid>
        <pubDate><?php echo date('r', strtotime($article['published_at'])); ?></pubDate>
        <category><?php echo category_label($article['category']); ?></category>
        <description><?php echo h(truncate($article['excerpt'] ?: strip_tags($article['body']), 300)); ?></description>
        <?php if ($article['author']): ?><author><?php echo h($article['author']); ?></author><?php endif; ?>
        <content:encoded><![CDATA[<?php echo render_shortcodes($article['body']); ?>]]></content:encoded>
    </item>
    <?php endforeach; ?>
</channel>
</rss>

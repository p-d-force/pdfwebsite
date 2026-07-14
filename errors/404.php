<?php require_once __DIR__ . '/../config.php'; require_once __DIR__ . '/../includes/helpers.php'; ?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 — Parent Data Force</title>
    <link rel="icon" type="image/png" href="/assets/images/logo.png">
    <link rel="stylesheet" href="/assets/css/styles.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
    <div style="display:grid;place-items:center;min-height:100vh;text-align:center;padding:2rem;">
        <div>
            <h1 style="font-size:4rem;color:var(--accent-glow);margin-bottom:0.5rem;">404</h1>
            <h2 style="margin-bottom:0.8rem;">Page Not Found</h2>
            <p style="color:var(--text-secondary);margin-bottom:1.5rem;">The page you're looking for doesn't exist or has been moved.</p>
            <div style="display:flex;gap:0.75rem;justify-content:center;flex-wrap:wrap;">
                <a href="/" class="btn btn-primary">Return Home</a>
                <a href="/articles/" class="btn btn-secondary">Browse Articles</a>
            </div>
        </div>
    </div>
</body>
</html>

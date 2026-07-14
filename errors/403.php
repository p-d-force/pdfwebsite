<?php require_once __DIR__ . '/../config.php'; require_once __DIR__ . '/../includes/helpers.php'; ?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>403 — Parent Data Force</title>
    <link rel="icon" type="image/png" href="/assets/images/logo.png">
    <link rel="stylesheet" href="/assets/css/styles.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
    <div style="display:grid;place-items:center;min-height:100vh;text-align:center;padding:2rem;">
        <div>
            <h1 style="font-size:4rem;color:var(--danger);margin-bottom:0.5rem;">403</h1>
            <h2 style="margin-bottom:0.8rem;">Access Denied</h2>
            <p style="color:var(--text-secondary);margin-bottom:1.5rem;">You don't have permission to access this resource.</p>
            <a href="/" class="btn btn-primary">Return Home</a>
        </div>
    </div>
</body>
</html>

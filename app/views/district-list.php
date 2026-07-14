<section class="section">
    <div class="container">
        <h1>Massachusetts School Districts</h1>
        <p class="section-lead">Browse school districts tracked by Parent Data Force. Click any district to view detailed data, active cases, and advocacy history.</p>
        <div class="district-grid">
            <?php foreach ($districts as $d): ?>
            <?php (new App\Components\DistrictCard($d))->render(); ?>
            <?php endforeach; ?>
        </div>
    </div>
</section>

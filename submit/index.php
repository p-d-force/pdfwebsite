<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/helpers.php';

$success  = $_GET['success'] ?? false;
$districts = Database::fetchAll('SELECT code, name FROM districts WHERE status = ? ORDER BY name', ['active']);

$page_title       = 'Submit Information';
$page_description = 'Submit a tip, request help, or upload files to Parent Data Force.';
include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="submit">
    <div class="container">
        <div class="section-header" data-animate>
            <span class="section-tag">Get Involved</span>
            <h2 class="section-title">Submit Information</h2>
            <p class="section-subtitle">
                Share tips, request advocacy help, or upload documents and data for review.
            </p>
        </div>

        <?php if ($success): ?>
            <div class="success-banner" data-animate>
                <h3>Submitted Successfully</h3>
                <p>Your submission has been received. We review every submission and will follow up if needed.</p>
                <a href="/" class="btn btn-secondary" style="margin-top:1rem;">Return Home</a>
            </div>
        <?php endif; ?>

        <div class="submit-tabs" data-animate>
            <button class="submit-tab active" data-tab="tip">Submit a Tip</button>
            <button class="submit-tab" data-tab="help" id="help">Request Help</button>
            <button class="submit-tab" data-tab="upload" id="upload">Upload Data</button>
        </div>

        <div class="submit-content active" id="tab-tip" data-animate>
            <div class="tip-banner" style="grid-template-columns:1fr;">
                <div class="tip-banner-copy">
                    <h3>Report a Concern</h3>
                    <p style="color:var(--text-secondary);margin-bottom:1rem;">
                        Report urgent district concerns, emerging incidents, documentation gaps, or recurring patterns. 
                        All submissions are reviewed. You can remain anonymous.
                    </p>
                </div>
                <form class="submit-form" action="/api/submit.php" method="post" enctype="multipart/form-data">
                    <?php echo csrf_field(); ?>
                    <input type="hidden" name="submission_type" value="tip">
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="tipDistrict" class="form-label">District / Agency *</label>
                            <select id="tipDistrict" name="district" class="form-select">
                                <option value="">Select district...</option>
                                <?php foreach ($districts as $d): ?>
                                    <option value="<?php echo h($d['name']); ?>"><?php echo h($d['name']); ?></option>
                                <?php endforeach; ?>
                                <option value="other">Other / Not Listed</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="tipType" class="form-label">Concern Type</label>
                            <select id="tipType" name="concern_type" class="form-select">
                                <option value="">Select...</option>
                                <option value="records">Public records concern</option>
                                <option value="special-ed">Special education concern</option>
                                <option value="compliance">Compliance failure</option>
                                <option value="safety">Safety incident</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        <div class="form-group form-group-full">
                            <label for="tipMessage" class="form-label">Details *</label>
                            <textarea id="tipMessage" name="message" class="form-textarea" rows="5" placeholder="Describe what happened, when, and what documentation might exist." required></textarea>
                        </div>
                        <div class="form-group">
                            <label for="tipEmail" class="form-label">Email (Optional)</label>
                            <input type="email" id="tipEmail" name="contact_email" class="form-input" placeholder="For follow-up">
                        </div>
                        <div class="form-group">
                            <label for="tipFiles" class="form-label">Attach Files (Optional, max 10)</label>
                            <input type="file" id="tipFiles" name="files[]" class="form-input" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.eml,.png,.jpg,.jpeg,.mp3,.mp4">
                        </div>
                        <button type="submit" class="btn btn-primary form-group-full">Send Tip</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="submit-content" id="tab-help" data-animate>
            <div class="tip-banner" style="grid-template-columns:1fr;">
                <div class="tip-banner-copy">
                    <h3>Request Advocacy Help</h3>
                    <p style="color:var(--text-secondary);margin-bottom:1rem;">
                        Need help with a special education issue, public records request, or advocacy strategy? 
                        Describe your situation and we'll respond.
                    </p>
                </div>
                <form class="submit-form" action="/api/submit.php" method="post" enctype="multipart/form-data">
                    <?php echo csrf_field(); ?>
                    <input type="hidden" name="submission_type" value="help">
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="helpName" class="form-label">Your Name</label>
                            <input type="text" id="helpName" name="contact_name" class="form-input" placeholder="Optional but helpful">
                        </div>
                        <div class="form-group">
                            <label for="helpEmail" class="form-label">Email *</label>
                            <input type="email" id="helpEmail" name="contact_email" class="form-input" placeholder="Where can we reach you?" required>
                        </div>
                        <div class="form-group">
                            <label for="helpDistrict" class="form-label">District / Agency</label>
                            <select id="helpDistrict" name="district" class="form-select">
                                <option value="">Select district...</option>
                                <?php foreach ($districts as $d): ?>
                                    <option value="<?php echo h($d['name']); ?>"><?php echo h($d['name']); ?></option>
                                <?php endforeach; ?>
                                <option value="other">Other / Not Listed</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="helpType" class="form-label">Help Type</label>
                            <select id="helpType" name="concern_type" class="form-select">
                                <option value="">Select...</option>
                                <option value="iep">IEP / 504 concerns</option>
                                <option value="restraint">Restraint / seclusion</option>
                                <option value="records">Public records help</option>
                                <option value="complaint">Filing a complaint</option>
                                <option value="strategy">Advocacy strategy</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        <div class="form-group form-group-full">
                            <label for="helpMessage" class="form-label">Describe Your Situation *</label>
                            <textarea id="helpMessage" name="message" class="form-textarea" rows="5" placeholder="What's happening? What help do you need? Timeline, district, key details..." required></textarea>
                        </div>
                        <div class="form-group">
                            <label for="helpFiles" class="form-label">Attach Files (Optional)</label>
                            <input type="file" id="helpFiles" name="files[]" class="form-input" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.eml,.png,.jpg,.jpeg">
                        </div>
                        <p class="form-group-full" style="color:var(--text-muted);font-size:0.82rem;">
                            Parent Data Force is an independent advocacy initiative. We do not provide legal advice. 
                            For legal matters, consult a qualified attorney.
                        </p>
                        <button type="submit" class="btn btn-primary form-group-full">Request Help</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="submit-content" id="tab-upload" data-animate>
            <div class="tip-banner" style="grid-template-columns:1fr;">
                <div class="tip-banner-copy">
                    <h3>Upload Data or Files</h3>
                    <p style="color:var(--text-secondary);margin-bottom:1rem;">
                        Have public records, district data, or documentation that should be part of our repository? 
                        Upload files for review and potential publication.
                    </p>
                </div>
                <form class="submit-form" action="/api/submit.php" method="post" enctype="multipart/form-data">
                    <?php echo csrf_field(); ?>
                    <input type="hidden" name="submission_type" value="upload">
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="uploadDistrict" class="form-label">District / Agency</label>
                            <select id="uploadDistrict" name="district" class="form-select">
                                <option value="">Select district...</option>
                                <?php foreach ($districts as $d): ?>
                                    <option value="<?php echo h($d['name']); ?>"><?php echo h($d['name']); ?></option>
                                <?php endforeach; ?>
                                <option value="other">Other / Not Listed</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="uploadEmail" class="form-label">Email (Optional)</label>
                            <input type="email" id="uploadEmail" name="contact_email" class="form-input" placeholder="For follow-up if questions">
                        </div>
                        <div class="form-group form-group-full">
                            <label for="uploadMessage" class="form-label">Description *</label>
                            <textarea id="uploadMessage" name="message" class="form-textarea" rows="3" placeholder="What does this data contain? Source, date range, context..." required></textarea>
                        </div>
                        <div class="form-group form-group-full">
                            <label for="uploadFiles" class="form-label">Files * (max 10, up to 256MB total)</label>
                            <input type="file" id="uploadFiles" name="files[]" class="form-input" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.eml,.png,.jpg,.jpeg,.mp3,.mp4" required>
                        </div>
                        <button type="submit" class="btn btn-primary form-group-full">Upload Files</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</section>

<script>
document.querySelectorAll('.submit-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.submit-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.submit-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const target = document.getElementById('tab-' + tab.dataset.tab);
        if (target) target.classList.add('active');
    });
});
</script>

<?php
include __DIR__ . '/../includes/footer.php';

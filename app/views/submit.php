<section class="section">
    <div class="container">
        <div class="section-header">
            <span class="section-tag">Get Involved</span>
            <h2 class="section-title">Submit Information</h2>
            <p class="section-subtitle">Share tips, request advocacy help, or upload documents and data for review.</p>
        </div>

        <div class="submit-tabs">
            <button class="submit-tab active" data-tab="tip">Submit a Tip</button>
            <button class="submit-tab" data-tab="help">Request Help</button>
            <button class="submit-tab" data-tab="upload">Upload Data</button>
        </div>

        <div class="submit-content active" id="tab-tip">
            <div class="tip-banner grid-1col">
                <div class="tip-banner-copy">
                    <h3>Report a Concern</h3>
                    <p class="text-muted mb-1">Report urgent district concerns, emerging incidents, documentation gaps, or recurring patterns. All submissions are reviewed.</p>
                </div>
                <form class="submit-form" method="post" action="/api/submit">
                    <?= csrf_field() ?>
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">District / Agency</label>
                            <input type="text" class="form-input" name="district" placeholder="e.g., Fall River Public Schools">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Concern Type</label>
                            <select class="form-select" name="concern_type">
                                <option value="">Select...</option>
                                <option>Public records concern</option>
                                <option>Special education concern</option>
                                <option>Compliance failure</option>
                                <option>Safety incident</option>
                                <option>Other</option>
                            </select>
                        </div>
                        <div class="form-group form-group-full">
                            <label class="form-label">Details</label>
                            <textarea class="form-textarea" name="details" rows="5" placeholder="Describe what happened, when, and what documentation might exist."></textarea>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Email (Optional)</label>
                            <input type="email" class="form-input" name="email" placeholder="For follow-up">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Attach Files (Optional)</label>
                            <input type="file" class="form-input" name="attachments" multiple>
                        </div>
                        <button type="submit" class="btn btn-primary form-group-full">Send Tip</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="submit-content" id="tab-help">
            <div class="tip-banner grid-1col">
                <div class="tip-banner-copy">
                    <h3>Request Advocacy Help</h3>
                    <p class="text-muted mb-1">Need help with a special education issue, public records request, or advocacy strategy? Describe your situation and we'll respond.</p>
                </div>
                <form class="submit-form" method="post" action="/api/submit">
                    <?= csrf_field() ?>
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Your Name</label>
                            <input type="text" class="form-input" name="name">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-input" name="email" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">District / Agency</label>
                            <input type="text" class="form-input" name="district">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Help Type</label>
                            <select class="form-select" name="help_type">
                                <option value="">Select...</option>
                                <option>IEP / 504 concerns</option>
                                <option>Restraint / seclusion</option>
                                <option>Public records help</option>
                                <option>Filing a complaint</option>
                                <option>Advocacy strategy</option>
                                <option>Other</option>
                            </select>
                        </div>
                        <div class="form-group form-group-full">
                            <label class="form-label">Describe Your Situation</label>
                            <textarea class="form-textarea" name="details" rows="5"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary form-group-full">Request Help</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="submit-content" id="tab-upload">
            <div class="tip-banner grid-1col">
                <div class="tip-banner-copy">
                    <h3>Upload Data or Files</h3>
                    <p class="text-muted mb-1">Have public records, district data, or documentation? Upload files for review and potential publication.</p>
                </div>
                <form class="submit-form" method="post" action="/api/submit" enctype="multipart/form-data">
                    <?= csrf_field() ?>
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">District / Agency</label>
                            <input type="text" class="form-input" name="district">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Email (Optional)</label>
                            <input type="email" class="form-input" name="email">
                        </div>
                        <div class="form-group form-group-full">
                            <label class="form-label">Description</label>
                            <textarea class="form-textarea" name="details" rows="3" placeholder="What does this data contain?"></textarea>
                        </div>
                        <div class="form-group form-group-full">
                            <label class="form-label">Files</label>
                            <input type="file" class="form-input" name="attachments" multiple>
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

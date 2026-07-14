<?php
declare(strict_types=1);
require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/helpers.php';

$page_title       = 'About Parent Data Force';
$page_description = 'Parent Data Force is an independent special education and public accountability advocacy initiative. We track complaints, analyze records, document outcomes, and expose systemic patterns.';
include __DIR__ . '/../includes/head.php';
include __DIR__ . '/../includes/header.php';
?>

<section class="section" id="about">
    <div class="container">
        <div class="section-header" data-animate>
            <span class="section-tag">About Us</span>
            <h2 class="section-title">Independent Advocacy for Public Accountability</h2>
            <p class="section-subtitle">
                Parent Data Force is an independent special education and public accountability advocacy initiative. 
                We track complaints, analyze records, document outcomes, and expose systemic patterns.
            </p>
        </div>

        <div class="mission-statement" data-animate>
            <div class="mission-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
            </div>
            <blockquote class="mission-text">
                "To ensure every family navigating special education and public systems has access to 
                transparent information, documented evidence, and strategic advocacy support."
            </blockquote>
        </div>

        <div class="values-grid" data-animate>
            <div class="value-card">
                <div class="value-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                </div>
                <h3 class="value-title">Documentation</h3>
                <p class="value-description">
                    Meticulous tracking of complaints, records requests, responses, and outcomes. 
                    Every detail matters when building a case for accountability.
                </p>
            </div>
            <div class="value-card">
                <div class="value-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                    </svg>
                </div>
                <h3 class="value-title">Accountability</h3>
                <p class="value-description">
                    Holding districts and agencies accountable through documented evidence, 
                    public records requests, and formal complaints when necessary.
                </p>
            </div>
            <div class="value-card">
                <div class="value-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                    </svg>
                </div>
                <h3 class="value-title">Strategy</h3>
                <p class="value-description">
                    Evidence-based approach combining public records law, complaint procedures, 
                    and systemic analysis to achieve meaningful outcomes.
                </p>
            </div>
            <div class="value-card">
                <div class="value-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
                <h3 class="value-title">Public Interest</h3>
                <p class="value-description">
                    Information belongs to the public. We work to ensure transparency 
                    in public systems and make advocacy resources accessible to all families.
                </p>
            </div>
        </div>

        <div class="section" style="padding:3rem 0 0;" id="privacy">
            <h3 class="section-title" style="font-size:1.5rem;">Privacy</h3>
            <p class="section-subtitle" style="max-width:100%;">
                Parent Data Force does not sell, share, or monetize personal information. Any information submitted through 
                our forms is used solely for advocacy purposes. Email subscriptions are used only for site updates and can 
                be unsubscribed at any time. We do not use tracking cookies or third-party analytics.
            </p>
        </div>
    </div>
</section>

<?php
include __DIR__ . '/../includes/footer.php';

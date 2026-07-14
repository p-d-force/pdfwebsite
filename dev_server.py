#!/usr/bin/env python3
"""
Parent Data Force v2 - Python Dev Server
========================================
Standalone local development server using sqlite3 + http.server.
Runs the full site without Docker, PHP, or MySQL.

Usage:  python dev_server.py
Visit:  http://localhost:8081

Static assets (CSS, JS, images) are served from the filesystem.
All content is stored in dev.db (SQLite3).
"""

import sqlite3
import json
import os
import re
import hashlib
import binascii
import sys

USE_FIRESTORE = '--firestore' in sys.argv
if USE_FIRESTORE:
    try:
        from backend.firestore_client import init_firestore
        fs_db = init_firestore()
        print("[firestore] Connected")
    except Exception as e:
        print(f"[firestore] WARNING: {e}, falling back to SQLite")
        USE_FIRESTORE = False
import datetime
import html as html_mod
import urllib.parse
import secrets
import bcrypt
from collections import OrderedDict
from http.server import HTTPServer, SimpleHTTPRequestHandler
from http.cookies import SimpleCookie
from socketserver import ThreadingMixIn
from pathlib import Path

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

ROOT = Path(__file__).resolve().parent
PUBLIC_ROOT = ROOT / "public"
DB_PATH = ROOT / "dev.db"
HOST = "localhost"
PORT = 8081
_current_path = ''  # Set by do_GET before each handler call

# 
# Database Setup
# 

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_fs():
    """Return Firestore client if available."""
    global USE_FIRESTORE
    if USE_FIRESTORE and 'fs_db' in globals():
        return fs_db
    return None


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS districts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            location TEXT,
            description TEXT,
            dese_code TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL UNIQUE,
            district_code TEXT NOT NULL,
            type TEXT DEFAULT 'other',
            title TEXT NOT NULL,
            summary TEXT,
            status TEXT DEFAULT 'open',
            current_stage TEXT,
            priority TEXT DEFAULT 'medium',
            filed_date TEXT,
            deadline TEXT,
            requested_items TEXT,
            timeline TEXT,
            cross_references TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS case_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            document_type TEXT DEFAULT 'other',
            file_path TEXT,
            file_type TEXT,
            file_size INTEGER DEFAULT 0,
            description TEXT,
            document_date TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            excerpt TEXT,
            body TEXT,
            category TEXT DEFAULT 'other',
            status TEXT DEFAULT 'draft',
            featured INTEGER DEFAULT 0,
            featured_image TEXT,
            seo_title TEXT,
            seo_description TEXT,
            author TEXT DEFAULT 'Parent Data Force',
            read_time INTEGER DEFAULT 0,
            published_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS article_case_links (
            article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
            sort_order INTEGER DEFAULT 0,
            PRIMARY KEY (article_id, case_id)
        );

        CREATE TABLE IF NOT EXISTS article_district_links (
            article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            district_id INTEGER NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
            sort_order INTEGER DEFAULT 0,
            PRIMARY KEY (article_id, district_id)
        );

        CREATE TABLE IF NOT EXISTS speeches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            platform TEXT DEFAULT 'youtube',
            category TEXT DEFAULT 'other',
            description TEXT,
            thumbnail_url TEXT,
            related_district_code TEXT,
            related_case_id TEXT,
            published_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT,
            source TEXT DEFAULT 'manual',
            severity TEXT DEFAULT 'medium',
            related_case_id TEXT,
            related_district_code TEXT,
            document_count INTEGER DEFAULT 0,
            event_date TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_type TEXT NOT NULL,
            district TEXT,
            message TEXT NOT NULL,
            contact_email TEXT,
            contact_name TEXT,
            file_path TEXT,
            original_filename TEXT,
            status TEXT DEFAULT 'new',
            reviewed_by INTEGER,
            review_notes TEXT,
            ip_address TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            role TEXT DEFAULT 'editor',
            status TEXT DEFAULT 'active',
            last_login_at TEXT,
            login_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS system_config (
            config_key TEXT PRIMARY KEY,
            config_value TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            details TEXT,
            ip_address TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS article_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE,
            slug TEXT NOT NULL UNIQUE COLLATE NOCASE,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS article_tag_links (
            article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            tag_id INTEGER NOT NULL REFERENCES article_tags(id) ON DELETE CASCADE,
            PRIMARY KEY (article_id, tag_id)
        );

        CREATE TABLE IF NOT EXISTS admin_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS aggregate_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cat_id TEXT,
            category TEXT,
            lane TEXT,
            source_type TEXT,
            evidence_note TEXT,
            scope_seen TEXT,
            result_use TEXT,
            confidence TEXT,
            source_ref TEXT
        );

        CREATE TABLE IF NOT EXISTS prr_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request TEXT,
            matter_type TEXT,
            agency TEXT,
            stage TEXT,
            request_date TEXT,
            last_activity TEXT,
            deadline_regime TEXT,
            initial_response_due TEXT,
            initial_response_date TEXT,
            initial_response_timeliness TEXT,
            production_due TEXT,
            stated_agreed_due TEXT,
            deadline_basis TEXT,
            current_deadline_status TEXT,
            request_summary TEXT,
            timeframe_scope TEXT,
            custodian_scope TEXT,
            record_category_scope TEXT,
            search_terms TEXT,
            exclusions TEXT,
            responsive_records TEXT,
            missing_gaps TEXT,
            no_custody_claimed TEXT,
            withheld_exemptions_fee TEXT,
            scope_drift TEXT,
            appeal_determination TEXT,
            next_action TEXT,
            gmail_source TEXT,
            evidence_reviewed TEXT,
            confidence TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT,
            phone TEXT,
            email TEXT,
            category TEXT DEFAULT 'other',
            tags TEXT,
            sort_order INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS restraint_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_year TEXT,
            district_name TEXT,
            district_code TEXT,
            school_name TEXT,
            school_code TEXT,
            enrollment INTEGER,
            students_restrained INTEGER,
            students_restrained_suppressed INTEGER DEFAULT 0,
            total_restraints INTEGER,
            total_restraints_suppressed INTEGER DEFAULT 0,
            total_injuries INTEGER,
            total_injuries_suppressed INTEGER DEFAULT 0,
            restraint_rate_per_100 REAL,
            injuries_per_restraint REAL,
            is_summary_row INTEGER DEFAULT 0,
            source_workbook TEXT
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_restraint_year ON restraint_data(school_year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_restraint_district ON restraint_data(district_code)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_restraint_school ON restraint_data(school_code)")
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM districts").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    conn.executescript("""
        INSERT INTO districts (code, name, location, description, dese_code) VALUES
        ('ATTLEBORO', 'Attleboro Public Schools', 'Attleboro, MA', 'Public school district serving the city of Attleboro, Massachusetts.', '00160000'),
        ('FALLRIVER', 'Fall River Public Schools', 'Fall River, MA', 'Public school district serving the city of Fall River, Massachusetts.', '00950000'),
        ('WHITMANH', 'Whitman-Hanson Regional School District', 'Whitman, MA / Hanson, MA', 'Regional school district.', '07800000'),
        ('BRIDGEWAT', 'Bridgewater-Raynham Regional School District', 'Bridgewater, MA / Raynham, MA', 'Regional school district.', '06250000'),
        ('NORTON', 'Norton Public Schools', 'Norton, MA', 'Public school district serving the town of Norton, Massachusetts.', '02000000'),
        ('DESE', 'Massachusetts Department of Elementary and Secondary Education', 'Malden, MA', 'State-level education department.', '00000000');

        INSERT INTO admin_users (username, email, password_hash, display_name, role) VALUES
        ('admin', 'admin@parentdataforce.com', '$2b$10$eKKCt1I4.NtxNJFGp73GCe.sgb5afmD0gnGn6w4Cg8JObarglryju', 'Administrator', 'owner');

        INSERT INTO system_config (config_key, config_value) VALUES
        ('site_email', 'admin@parentdataforce.com'),
        ('site_name', 'Parent Data Force');

        INSERT INTO cases (case_id, district_code, type, title, summary, status, current_stage, priority, filed_date, deadline, requested_items, timeline) VALUES
        ('SPR26-0842', 'ATTLEBORO', 'public_records', 'Professional Development Records Request',
         'Public records request for professional development records with documented delays, fee disputes, and escalation to the Supervisor of Public Records (SPR).',
         'open', 'Response Package Review', 'high', '2026-02-18', '2026-04-02',
         '["Program title, provider, dates, format, audience, and location","Cost records including contracts, invoices, and funding source","Training content, agendas, handouts, and learning objectives","Implementation records and future PD schedules"]',
         '[{"date":"2026-02-18","title":"PRR Submitted","description":"Filed SPR26-0842 requesting professional development records.","docs":[{"label":"Initial PRR (PDF)","url":"/archive/cases/ATTLEBORO/SPR26-0842/original-request/2026-02-18_PRR_SPR26-0842_PD_Records_Request.pdf"}]},{"date":"2026-03-03","title":"Appeal Filed (C24-0260)","description":"Filed appeal contesting excessive fee estimate.","docs":[{"label":"Appeal C24-0260 (PDF)","url":"/archive/cases/ATTLEBORO/SPR26-0842/appeals/2026-03-03_Appeal_C24-0260_Excessive_Fee.pdf"}]},{"date":"2026-03-19","title":"SPR Determination Issued","description":"Supervisor of Public Records issued determination and response order.","docs":[{"label":"SPR Determination (PDF)","url":"/archive/cases/ATTLEBORO/SPR26-0842/determinations/2026-03-19_SPR_Determination_SPR26-0842.pdf"}]}]'),

        ('ATTLEBORO-PRR-002', 'ATTLEBORO', 'public_records', 'Meetings, Recordings, and Financials Archive Request',
         'Comprehensive public records request seeking all open-meeting recordings/transcripts/materials, releasable executive-session portions, and FY2022-present financial records.',
         'open', 'Awaiting District Production', 'medium', '2026-01-31', '2026-04-02',
         '["Open meeting recordings, transcripts/captions, draft/approved minutes","Agendas, notices, packets, exhibits","Executive session releasable portions","Financial records FY2022-present"]',
         '[{"date":"2026-01-31","title":"Broad PRR Submitted","description":"Filed broad records request covering all meetings and financial records.","docs":[]},{"date":"2026-03-19","title":"Responsive Audio Archive Indexed","description":"Meeting audio recordings were normalized and organized into the public archive.","docs":[]}]'),

        ('PRS-15514', 'FALLRIVER', 'determination', 'DESE Request for Local Response',
         'DESE PRS complaint progression with DESE-issued request for local response. District and complainant submissions due April 7, 2026.',
         'open', 'Request for Local Response Issued', 'high', '2026-03-19', '2026-04-07',
         '["District local response submission","Complainant supplemental materials","Any DESE-requested follow-up documentation"]',
         '[{"date":"2026-03-19","title":"Request for Local Response Issued","description":"DESE PRS notified parties and set April 7, 2026 deadlines.","docs":[]}]'),

        ('FALLRIVER-PRR-001', 'FALLRIVER', 'public_records', 'Hiring Records - Silvia Elementary',
         'Hiring-records request for School Adjustment Counselor position at Silvia Elementary, including posting, interviews, waiver records, and internal communications.',
         'open', 'Clarification in Progress', 'medium', '2026-03-05', '2026-03-20',
         '["Vacancy posting and recruitment outreach","Interview schedules and candidate lists","Licensure/waiver documentation","Internal communications on hiring decision"]',
         '[{"date":"2026-03-05","title":"PRR Submitted","description":"Initial hiring-records request sent to district.","docs":[]},{"date":"2026-03-19","title":"Clarification Submitted","description":"Requester provided amended scope and timeframe details.","docs":[]}]');

        INSERT INTO speeches (video_id, title, url, platform, category, description, related_district_code, published_at) VALUES
        ('dQw4w9WgXcQ', 'Public Comment: Special Education Priorities', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'youtube', 'public_comment',
         'Public comment delivered at Attleboro School Committee meeting regarding special education services and compliance.', 'ATTLEBORO', '2026-01-15'),
        ('V-_O7nlM6TY', 'Testimony: DESE Restraint and Seclusion Hearing', 'https://www.youtube.com/watch?v=V-_O7nlM6TY', 'youtube', 'hearing',
         'Testimony before the Massachusetts DESE regarding the use of restraint and seclusion in public schools.', NULL, '2026-02-10');

        INSERT INTO updates (title, body, source, severity, related_case_id, related_district_code, event_date) VALUES
        ('DESE Restraint Data Pipeline Activated', 'The statewide restraint and seclusion data pipeline has been activated, pulling 9 years of data from the DESE profiles website covering 8,500+ school-level records.', 'auto', 'high', NULL, 'DESE', '2026-07-10'),
        ('SPR26-0842: District Response Package Received', 'Records Access Officer sent district response letter confirming narrowed-scope response package with PD database export.', 'auto', 'medium', 'SPR26-0842', 'ATTLEBORO', '2026-03-19'),
        ('PRS-15514: DESE Issues Local Response Request', 'DESE PRS notified parties and set April 7, 2026 deadlines for local response and supplemental submissions.', 'auto', 'high', 'PRS-15514', 'FALLRIVER', '2026-03-19'),
        ('ATTLEBORO-PRR-002: Broad Records Request Filed', 'Comprehensive public records request filed covering meeting recordings, transcripts, executive session portions, and FY2022-present financial records.', 'auto', 'medium', 'ATTLEBORO-PRR-002', 'ATTLEBORO', '2026-01-31'),
        ('FALLRIVER-PRR-001: Hiring Records Request Submitted', 'Public records request for School Adjustment Counselor hiring documentation at Silvia Elementary, including posting, interviews, and waiver records.', 'auto', 'low', 'FALLRIVER-PRR-001', 'FALLRIVER', '2026-03-05');

        -- Tags
        INSERT INTO article_tags (name, slug) VALUES
        ('Public Records', 'public-records'), ('Special Education', 'special-education'),
        ('DESE', 'dese'), ('Restraint & Seclusion', 'restraint-seclusion'),
        ('Advocacy', 'advocacy'), ('Data Analysis', 'data-analysis'),
        ('Massachusetts Law', 'massachusetts-law'), ('School Committees', 'school-committees'),
        ('IEP', 'iep'), ('Compliance', 'compliance'),
        ('Fall River', 'fall-river'), ('Attleboro', 'attleboro'),
        ('Investigation', 'investigation'), ('Parent Guide', 'parent-guide');

        -- 8 Articles across all categories
        INSERT INTO articles (title, slug, excerpt, body, category, status, featured, author, read_time, published_at) VALUES
        ('How Public Records Requests Drive School District Accountability', 'how-public-records-drive-accountability',
         'A step-by-step guide to using Massachusetts public records law to obtain critical information about special education practices, professional development spending, and compliance records.',
         '<h2>The Power of Public Records Law</h2><p>Public records requests are one of the most powerful tools available to parents and advocates in Massachusetts. Under M.G.L. c. 66,  10, every person has a right to inspect and copy public records. School districts must respond within 10 business days, and failure to do so can be appealed to the Supervisor of Public Records.</p><p>This guide walks you through the entire process - from crafting a legally-sufficient request to escalating when districts fail to comply.</p><h2>Crafting an Effective Request</h2><p>The key to a successful request is specificity. A vague request for "all special education records" will be met with resistance, delays, or excessive fee estimates. Instead, specify:</p><ul><li>The exact records you seek (e.g., "all staffing assignment records for the School Adjustment Counselor position")</li><li>The date range (e.g., "August 1, 2024 to present")</li><li>The format you want (always request electronic copies)</li><li>The specific individuals or offices likely to hold the records</li></ul><blockquote><p>A well-crafted request is your best defense against administrative stonewalling.</p></blockquote><h2>When Districts Don''t Respond</h2><p>If the district fails to respond within 10 business days, or provides a fee estimate you believe is excessive, you have the right to appeal to the Supervisor of Public Records. This is not a dead end - it is a powerful escalation tool.</p><p>[case id="SPR26-0842"]</p><p>In our own advocacy, we filed a public records request for professional development records and encountered delays, a $2,400+ fee estimate, and a failure to respond. Two appeals later - C24-0260 for excessive fees and C24-0713 for failure to respond - the SPR issued a determination and the district produced responsive records.</p><h2>Building Cases From Records</h2><p>The documentation obtained through persistent records requests forms the backbone of evidence-based advocacy. Every email thread, PD database export, and internal communication becomes part of a trail that future families and advocates can rely upon.</p><p>[timeline id="SPR26-0842"]</p>',
         'guide', 'published', 1, 'Parent Data Force', 6, '2026-07-01'),

        ('Understanding Restraint and Seclusion Data in Massachusetts', 'understanding-restraint-seclusion-data',
         'An analysis of 9 years of DESE restraint and seclusion data reveals troubling trends: rising rates, suppression gaps, and what families need to know to protect their children.',
         '<h2>Nine Years of Data Tell a Story</h2><p>Since 2016, Massachusetts schools have reported over 69,000 restraint incidents. The COVID-19 pandemic created a temporary drop to 2,781 incidents in 2020-21, but rates have rebounded sharply - 2024-25 saw 8,425 incidents statewide, the second highest in the dataset.</p><p>[chart type="restraint-years"]</p><h2>The Suppression Problem</h2><p>DESE publishes school-level restraint data annually, but with critical caveats: cells are suppressed (shown as a dash) when fewer than 6 students are restrained at a school. This means thousands of restraint incidents across hundreds of schools are invisible in the published data. Schools that report zero restraints are simply not listed at all. The published data systematically underrepresents the true scope of restraint use in Massachusetts.</p><h2>Which Schools Use Restraints Most?</h2><p>The data reveals stark disparities. Some schools report rates above 10 restraints per 100 students - ten times the statewide average. These are often concentrated at specific elementary schools and specialized programs. Without public data visibility, families have no way to know what''s happening at their child''s school.</p><h2>What Families Can Do</h2><ul><li>Request your child''s school-specific restraint data - it may not be in the published dataset</li><li>Compare your district''s per-school rates to the statewide average of approximately 0.9 restraints per 100 students</li><li>Document every incident - schools may underreport</li><li>Use restraint data in IEP meetings to argue for additional behavioral supports and staff training</li><li>Check our <a href="/data/">data browser</a> to explore every school-level restraint record from 2016-2025</li></ul>',
         'data_analysis', 'published', 1, 'Parent Data Force', 5, '2026-06-15'),

        ('SPR Appeals: When and How to Escalate a Public Records Denial', 'spr-appeals-escalation-guide',
         'What happens when a school district stonewalls your records request? A practical guide to appealing to the Massachusetts Supervisor of Public Records.',
         '<h2>Know Your Appeal Rights</h2><p>Under Massachusetts public records law, you have the right to appeal to the Supervisor of Public Records (SPR) when:<ul><li>A district fails to respond within 10 business days</li><li>A district charges what you believe is an unreasonable fee</li><li>A district withholds records you believe should be public</li><li>A district''s redactions are excessive</li></ul></p><h2>The Appeal Process</h2><p>Appeals are free and can be filed electronically. The SPR will review the case and issue a determination - typically within a few weeks for failure-to-respond cases, longer for substantive disputes. The SPR''s determinations carry significant weight and often result in compliance.</p><h2>Real-World Results</h2><p>[case id="SPR26-0842"]</p><p>Our professional development records case in Attleboro involved two separate appeals: one contesting a $2,400+ fee estimate (C24-0260), and one documenting a failure to respond (C24-0713). The SPR issued a determination ordering the district to respond within 10 days. The district complied, producing a database export of all requested PD records.</p><h2>When to Appeal vs. When to Negotiate</h2><p>Not every records dispute requires an SPR appeal. Sometimes narrowing your request scope or clarifying what you''re looking for unlocks a faster response. But when a district is clearly stonewalling - missing deadlines, demanding excessive fees without justification, or refusing to search for responsive records - an SPR appeal is your most effective tool.</p>',
         'methodology', 'published', 1, 'Parent Data Force', 4, '2026-06-10'),

        ('Inside the Attleboro Public Schools PD Records Investigation', 'inside-attleboro-pd-records-investigation',
         'A detailed look at the records request, appeals, data analysis, and compliance findings from our investigation into professional development spending in Attleboro Public Schools.',
         '<h2>The Investigation</h2><p>In early 2026, Parent Data Force filed a comprehensive public records request with Attleboro Public Schools seeking all records related to professional development: program titles and providers, costs including contracts and invoices, training content and materials, implementation records, and future PD schedules.</p><p>The district''s initial response included a fee estimate exceeding $2,400 and multiple delays that extended well past the statutory 10-business-day timeline.</p><h2>Escalation</h2><p>Two SPR appeals followed:<ul><li><strong>C24-0260 (March 3, 2026):</strong> Appeal of excessive fee estimate</li><li><strong>C24-0713 (March 9, 2026):</strong> Appeal of failure to respond within statutory timeline</li></ul></p><p>[timeline id="SPR26-0842"]</p><h2>What We Found</h2><p>The district ultimately produced responsive records after the SPR determination, including a detailed database export of professional development activities. The data revealed patterns in PD spending, vendor relationships, and training priorities that were previously opaque to the public. This investigation demonstrates that persistent records requests, combined with diligent follow-up and appropriate escalation, can force transparency from districts that might otherwise operate without public accountability.</p>',
         'case_update', 'published', 1, 'Parent Data Force', 5, '2026-05-20'),

        ('Building an Evidence Locker: How to Organize Advocacy Documentation', 'building-an-evidence-locker',
         'Systematic documentation is the foundation of effective advocacy. Here''s how to organize emails, records, timelines, and correspondence into an evidence locker that wins cases.',
         '<h2>Why Documentation Matters</h2><p>In special education and public accountability advocacy, the quality of your documentation directly determines your effectiveness. A well-organized evidence locker transforms scattered emails and documents into a coherent narrative that district administrators, hearing officers, and state agencies cannot ignore.</p><h2>The Evidence Locker System</h2><p>We use a four-part organization system:<ul><li><strong>Chronological Index:</strong> Every document tagged with date, type, and source</li><li><strong>Topic Folders:</strong> IEP records, evaluations, correspondence, complaint filings</li><li><strong>Timeline Narrative:</strong> Key events in chronological order with document references</li><li><strong>Issue-Action-Outcome Log:</strong> Each concern tracked through to resolution</li></ul></p><h2>Tools and Techniques</h2><p>You don''t need expensive software. A combination of:<ul><li>Email folders with consistent naming conventions</li><li>A chronological spreadsheet tracking every interaction</li><li>Scanned or photographed physical documents</li><li>Cloud backup of everything</li></ul></p><p>is sufficient for most families. The key is consistency - document as you go, not after the fact.</p><blockquote><p>The strongest case is built on the smallest details, documented in real time.</p></blockquote>',
         'methodology', 'published', 1, 'Parent Data Force', 5, '2026-05-05'),

        ('DESE Complaint Filing: The Problem Resolution System Explained', 'dese-prs-complaint-system-explained',
         'How to file a formal complaint with the Massachusetts DESE Problem Resolution System, what to expect, and how PRS-15514 demonstrates the process.',
         '<h2>What Is PRS?</h2><p>The Problem Resolution System (PRS) is DESE''s formal mechanism for investigating complaints about school district compliance with special education law. Unlike public records appeals, PRS complaints can lead to findings, corrective action orders, and systemic changes.</p><h2>When to File</h2><p>PRS is appropriate when a district:<ul><li>Fails to follow IEP procedures</li><li>Does not provide required services</li><li>Violates special education timelines</li><li>Shows a pattern of non-compliance</li></ul></p><h2>The Process</h2><p>After filing, DESE reviews the complaint and may:<ol><li>Issue a Request for Local Response - asking the district to respond</li><li>Investigate directly</li><li>Facilitate resolution between parties</li><li>Issue findings and corrective actions</li></ol></p><p>[case id="PRS-15514"]</p><p>Our Fall River complaint (PRS-15514) demonstrates the process: after filing, DESE issued a Request for Local Response with an April 7, 2026 deadline for both the district and the complainant to submit materials. This standard procedural step initiates the formal investigation phase.</p>',
         'policy', 'published', 1, 'Parent Data Force', 4, '2026-04-22'),

        ('Fall River Silvia Elementary: A Case Study in Records and Hiring Transparency', 'fall-river-silvia-elementary-case-study',
         'Two public records requests reveal a pattern of delays, clarification loops, and staffing concerns at a Massachusetts elementary school. Here''s what we found and what it means.',
         '<h2>The Investigation</h2><p>In March 2026, Parent Data Force filed two public records requests with Fall River Public Schools targeting Silvia Elementary School. The first (FALLRIVER-PRR-001) sought hiring records for a School Adjustment Counselor position. The second (FALLRIVER-PRR-002) requested comprehensive incident reports, restraint documentation, staffing assignments, and communications tied to a February 4 incident.</p><h2>Patterns of Delay</h2><p>Both requests triggered similar responses: the statutory 10-business-day deadline passed, the district requested clarifications that extended timelines, and substantive records production remained pending. This pattern - deadline + clarification request + extended timeline - is common across Massachusetts districts and represents a gap between legal requirements and practical compliance.</p><h2>Why It Matters</h2><p>Hiring records and staffing documentation are not just administrative details. They reveal whether schools are meeting their legal obligations to provide qualified special education personnel. When a School Adjustment Counselor position''s hiring process lacks transparency, families cannot verify whether their children are receiving services from properly credentialed staff.</p><p>[case id="FALLRIVER-PRR-001"]</p><p>[case id="FALLRIVER-PRR-002"]</p>',
         'case_update', 'published', 0, 'Parent Data Force', 5, '2026-04-10'),

        ('What Every Massachusetts Parent Should Know About IEPs and Public Records', 'massachusetts-parents-iep-records-guide',
         'The intersection of IEP rights and public records access creates powerful advocacy opportunities. Here''s what parents need to know to be effective.',
         '<h2>Your Right to Information</h2><p>Massachusetts parents have two overlapping rights that together create a powerful advocacy toolkit: <strong>IEP procedural safeguards</strong> (including the right to educational records) and <strong>public records access</strong> (under M.G.L. c. 66,  10). Many families only know about the first.</p><h2>What Public Records Access Adds</h2><p>While IEP processes give you access to your child''s records, public records law opens a wider door:<ul><li>District-wide special education staffing levels and vacancies</li><li>Professional development records showing what training staff actually received</li><li>Internal communications about policies affecting your child</li><li>Incident reports and restraint documentation beyond what the school volunteers</li><li>Budget documents showing how special education funds are allocated</li></ul></p><h2>Practical Steps</h2><p>When preparing for an IEP meeting:<ol><li>File a targeted public records request 4-6 weeks before the meeting</li><li>Focus on staffing records, incident reports, and PD documentation relevant to your concerns</li><li>Bring the received records to the meeting as evidence</li><li>Reference specific data points rather than general complaints</li></ol></p><blockquote><p>Data changes the dynamic. When you walk into an IEP meeting with documented evidence of staffing vacancies or training gaps, the conversation shifts from "trust us" to "here''s what the records show."</p></blockquote>',
         'guide', 'published', 1, 'Parent Data Force', 5, '2026-03-20'),

        ('The Systemic Pattern: Cross-District Analysis of Records Compliance', 'cross-district-records-compliance-analysis',
         'When we compare records request outcomes across Attleboro, Fall River, Whitman-Hanson, Bridgewater-Raynham, and Norton, a pattern emerges: statutory deadlines are routinely missed, fee estimates are inconsistently applied, and transparency varies dramatically by district.',
         '<h2>Five Districts, One Pattern</h2><p>Parent Data Force tracks public records activity across five Massachusetts districts. Our analysis reveals consistent systemic issues:<ul><li><strong>Deadline compliance</strong> is the exception, not the rule. Most districts take longer than 10 business days to provide substantive responses.</li><li><strong>Fee estimates</strong> vary wildly for similar requests across districts, suggesting inconsistent - or nonexistent - fee policies.</li><li><strong>Clarification requests</strong> are used strategically to extend timelines.</li><li><strong>Production quality</strong> ranges from well-organized exports to piecemeal, delayed responses.</li></ul></p><h2>What the Data Shows</h2><p>Across our tracked cases, the median time to substantive response exceeds 15 business days - 50% longer than the statutory requirement. Appeals to the SPR are often necessary to compel compliance, yet many families don''t know this option exists.</p><h2>Policy Implications</h2><p>These patterns suggest that Massachusetts'' public records law, while strong on paper, lacks meaningful enforcement mechanisms. Without consequences for non-compliance, districts face little pressure to improve. The SPR process provides an important check, but only for those who know how to use it.</p><p>The solution is not just better laws - it''s informed advocacy. Every successful records request and SPR appeal builds the case for systemic reform.</p>',
         'investigation', 'published', 1, 'Parent Data Force', 4, '2026-03-01');

        -- Tag assignments
        INSERT INTO article_tag_links (article_id, tag_id) VALUES
        (1,1),(1,2),(1,5),(1,7),(1,12),     -- Public Records guide: public-records, special-ed, advocacy, mass-law, attleboro
        (2,3),(2,4),(2,6),(2,5),             -- Restraint data: dese, restraint, data-analysis, advocacy
        (3,1),(3,3),(3,5),(3,12),            -- SPR appeals: public-records, dese, advocacy, attleboro
        (4,1),(4,2),(4,12),(4,13),           -- Attleboro PD: public-records, special-ed, attleboro, investigation
        (5,5),(5,14),(5,2),                  -- Evidence locker: advocacy, parent-guide, special-ed
        (6,3),(6,2),(6,11),(6,10),           -- PRS: dese, special-ed, fall-river, compliance
        (7,1),(7,11),(7,13),                 -- Silvia: public-records, fall-river, investigation
        (8,2),(8,1),(8,5),(8,9),(8,14),      -- Parent guide: special-ed, public-records, advocacy, iep, parent-guide
        (9,1),(9,3),(9,10),(9,13);           -- Cross-district: public-records, dese, compliance, investigation

        INSERT INTO aggregate_catalog (cat_id, category, lane, source_type, evidence_note, scope_seen, result_use, confidence, source_ref) VALUES
        ('CAT-001', 'USPS mailing identifiers', 'MA public records', 'SPR determination', 'SPR26/2112 describes a five-year request for USPS Mailer ID, CRID, permit numbers, postage meter/account numbers, and linked locations/vendors.', 'Past five years; Fall River Public Schools', 'Supervisor ordered response within 10 business days after nonresponse.', 'High', 'SPR26/2112'),
        ('CAT-002', 'Hiring / licensure / start-date records', 'MA public records', 'SPR determinations', 'SPR26/1073 and SPR26/2117 show job postings, recruitment, interview records, waiver/licensure review, appointment/start-date, payroll authorization.', 'Role-specific hiring periods; Fall River Public Schools', 'Supervisor ordered response within 10 business days in both matters.', 'High', 'SPR26/1073, SPR26/2117'),
        ('CAT-003', 'Safety, restraint, staffing, and crisis records', 'MA public records with privacy overlay', 'SPR determination', 'SPR26/1074 lists incident reports, restraint reports, behavior summaries, staffing assignments, IEP-service staffing, event communications, emergency logs.', 'Aug. 1 2024-present; Silvia Elementary', 'Supervisor ordered response within 10 business days.', 'High', 'SPR26/1074'),
        ('CAT-005', 'PRS aggregate complaint/intake export', 'MA public records', 'Direct production attachment', 'The PRS aggregate PDFs show columns for number, district/agency, intake date, status, letter-of-finding date, category, subcategory, and closure code.', 'Since Jan. 1 2021; statewide and Attleboro-specific exports', 'Responsive records were produced; supports requesting database-style exports.', 'High', 'DESE PRS production');

        INSERT INTO resources (title, description, url, phone, email, category, tags, sort_order) VALUES
        ('Massachusetts DESE Problem Resolution System', 'File a formal complaint about special education non-compliance. DESE investigates and can order corrective action.', 'https://www.doe.mass.edu/prs/', '(781) 338-3700', 'compliance@doe.mass.edu', 'special-ed', 'dese, complaint, special-ed', 1),
        ('Supervisor of Public Records', 'Appeal a denied or ignored public records request. The SPR can order agencies to comply.', 'https://www.sec.state.ma.us/SPR/', '(617) 727-2832', 'pre@sec.state.ma.us', 'public-records', 'public-records, appeal, spr', 2),
        ('Massachusetts Public Records Law Guide', 'Secretary of the Commonwealth guide to M.G.L. c. 66, section 10 - your right to access public records.', 'https://www.sec.state.ma.us/ARC/arcidx.htm', NULL, NULL, 'public-records', 'public-records, massachusetts-law, guide', 3),
        ('Federation for Children with Special Needs', 'Massachusetts parent advocacy organization providing training, support, and resources.', 'https://fcsn.org/', '(617) 236-7210', 'info@fcsn.org', 'special-ed', 'special-ed, advocacy, parent-support', 4),
        ('Massachusetts Advocates for Children', 'Nonprofit advocacy organization focused on children with disabilities and vulnerable children.', 'https://www.massadvocates.org/', '(617) 357-8431', NULL, 'special-ed', 'special-ed, legal, advocacy', 5),
        ('DESE Special Education Staff Directory', 'Contact information for DESE special education leadership and program staff.', 'https://www.doe.mass.edu/sped/contact.html', NULL, NULL, 'district-contact', 'dese, special-ed, contacts', 6),
        ('US Department of Education Office for Civil Rights', 'File a federal civil rights complaint about discrimination in education, including disability discrimination.', 'https://www2.ed.gov/about/offices/list/ocr/complaintintro.html', '(800) 421-3481', 'ocr.boston@ed.gov', 'legal', 'federal, discrimination, legal', 7),
        ('Children Law Center of Massachusetts', 'Free legal services for low-income children and families in education matters.', 'https://www.clcm.org/', '(781) 581-1977', NULL, 'legal', 'legal, special-ed, low-income', 8);
    """)
    conn.commit()
    conn.close()


# 
# Helper functions
# 

def h(text):
    if text is None:
        return ''
    return html_mod.escape(str(text), quote=True)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-') or 'untitled'


def format_date(value, fmt='%b %d, %Y'):
    if not value:
        return ''
    try:
        if 'T' in str(value):
            value = str(value).split('T')[0]
        dt = datetime.datetime.strptime(str(value)[:10], '%Y-%m-%d')
        return dt.strftime(fmt)
    except (ValueError, TypeError):
        return str(value) if value else ''


def excerpt(text, length=300):
    t = re.sub(r'<[^>]+>', '', str(text or ''))
    t = t.strip()
    if len(t) <= length:
        return t
    return t[:length].rsplit(' ', 1)[0] + '...'


def read_time_est(text):
    words = len(re.sub(r'<[^>]+>', '', str(text or '')).split())
    return max(1, words // 200)


def status_badge(status):
    colors = {
        'open': 'status-open', 'closed': 'status-closed',
        'pending': 'status-pending', 'resolved': 'status-resolved',
        'overdue': 'status-overdue', 'new': 'status-pending',
        'reviewing': 'status-open', 'accepted': 'status-resolved',
        'rejected': 'status-closed', 'archived': 'status-closed',
        'active': 'status-open', 'inactive': 'status-closed',
        'draft': 'status-pending', 'published': 'status-open',
    }
    cls = colors.get(status, 'status-pending')
    label = status.replace('_', ' ').title()
    return f'<span class="status-badge {cls}">{h(label)}</span>'


def category_label(cat):
    labels = {
        'case_update': 'Case Update', 'methodology': 'Methodology',
        'data_analysis': 'Data Analysis', 'policy': 'Policy',
        'news': 'News', 'investigation': 'Investigation',
        'guide': 'Guide', 'other': 'Other',
    }
    return h(labels.get(cat, cat.replace('_', ' ').title()))


def case_type_label(typ):
    labels = {
        'public_records': 'Public Records Request', 'complaint': 'Complaint',
        'finding': 'Finding', 'determination': 'Determination',
        'appeal': 'Appeal', 'investigation': 'Investigation', 'other': 'Other',
    }
    return h(labels.get(typ, typ.replace('_', ' ').title()))


def severity_badge(sev):
    colors = {'high': 'status-closed', 'medium': 'status-pending', 'low': 'status-open'}
    cls = colors.get(sev, 'status-pending')
    return f'<span class="status-badge {cls}">{h(sev.title())}</span>'


def render_shortcodes(content):
    if not content:
        return ''

    def case_card(match):
        conn = get_db()
        row = conn.execute(
            "SELECT case_id, title, district_code, type, status, summary, current_stage, filed_date, deadline "
            "FROM cases WHERE case_id = ? AND status != 'archived'", (match.group(1),)
        ).fetchone()
        conn.close()
        if not row:
            return f'<div class="shortcode-error">Case not found: {h(match.group(1))}</div>'

        url = f'/cases/{urllib.parse.quote(row["case_id"])}'
        return f'''<div class="shortcode-case-card">
    <div class="shortcode-case-header">
        <span class="case-district">{h(row["district_code"])}, MA</span>
        {status_badge(row["status"])}
    </div>
    <h4 class="shortcode-case-title"><a href="{url}">{h(row["title"])}</a></h4>
    <p class="shortcode-case-summary">{h(row["summary"])}</p>
    <div class="shortcode-case-meta">
        <span><strong>Type:</strong> {case_type_label(row["type"])}</span>
        <span><strong>Filed:</strong> {format_date(row["filed_date"])}</span>
        <span><strong>Deadline:</strong> {format_date(row["deadline"])}</span>
        <span><strong>Stage:</strong> {h(row["current_stage"] or '')}</span>
    </div>
    <a href="{url}" class="btn btn-secondary" style="margin-top:0.5rem;font-size:0.85rem;">View Case Details</a>
</div>'''

    def case_timeline(match):
        conn = get_db()
        row = conn.execute("SELECT timeline FROM cases WHERE case_id = ?", (match.group(1),)).fetchone()
        conn.close()
        if not row or not row['timeline']:
            return f'<div class="shortcode-error">Timeline not found.</div>'
        events = json.loads(row['timeline'])
        items = ''
        for e in events:
            docs = ''
            for d in e.get('docs', []):
                if isinstance(d, str):
                    docs += f'<span class="timeline-doc">{h(d)}</span>'
                else:
                    docs += f'<a class="timeline-doc" href="{h(d.get("url","#"))}" target="_blank">{h(d.get("label","Doc"))}</a>'
            if docs:
                docs = f'<div class="timeline-docs">{docs}</div>'
            items += f'''<li class="timeline-item">
    <div class="timeline-item-head">
        <span class="timeline-item-title">{h(e.get("title",""))}</span>
        <span class="timeline-item-date">{h(e.get("date",""))}</span>
    </div>
    <p>{h(e.get("description",""))}</p>
    {docs}
</li>'''
        return f'''<div class="shortcode-timeline">
    <h4 class="shortcode-timeline-title">Case Timeline</h4>
    <ul class="timeline-list">{items}</ul>
</div>'''

    def chart_embed(match):
        return f'<div class="shortcode-chart" data-chart-type="{match.group(1)}"><canvas style="min-height:300px;"></canvas></div>'

    def youtube_embed(match):
        vid = h(match.group(1))
        title = h(match.group(2)) if match.group(2) else ''
        title_html = f'<h4 class="shortcode-embed-title">{title}</h4>' if title else ''
        return f'''<div class="shortcode-video">
    {title_html}
    <div class="shortcode-video-wrapper">
        <iframe src="https://www.youtube.com/embed/{vid}" allowfullscreen
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            loading="lazy" style="border:none;"></iframe>
    </div>
</div>'''

    content = re.sub(r'\[case\s+id="([^"]+)"\]', case_card, content)
    content = re.sub(r'\[timeline\s+id="([^"]+)"\]', case_timeline, content)
    content = re.sub(r'\[chart\s+type="([^"]+)"(?:\s+district="([^"]*)")?\]', chart_embed, content)
    content = re.sub(r'\[youtube\s+id="([^"]+)"(?:\s+title="([^"]*)")?\]', youtube_embed, content)
    return content


# 
# HTML rendering
# 
ASSETS = {
    'styles.css': (PUBLIC_ROOT / 'assets' / 'css' / 'app.css'),
    'admin.css': (PUBLIC_ROOT / 'assets' / 'css' / 'admin.css'),
    'main.js': (PUBLIC_ROOT / 'assets' / 'js' / 'app.js'),
    'charts.js': (PUBLIC_ROOT / 'assets' / 'js' / 'components' / 'charts.js'),
    'logo.png': (PUBLIC_ROOT / 'assets' / 'images' / 'logo.png'),
}

CSS_CONTENT = None
JS_MAIN_CONTENT = None
JS_CHARTS_CONTENT = None

def get_head(title='', description=''):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{h(description or 'Parent Data Force - Data-driven advocacy for families.')}">
    <meta property="og:title" content="{h(title + ' | ' if title else '')}Parent Data Force">
    <meta property="og:description" content="{h(description or 'Data-driven advocacy for families navigating special education and public systems.')}">
    <meta property="og:type" content="website">
    <meta property="og:image" content="/assets/images/logo.png">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="canonical" href="http://{HOST}:{PORT}{{canonical_path}}">
    <title>{h(title + ' | ' if title else '')}Parent Data Force</title>
    <link rel="icon" type="image/png" href="/assets/images/logo.png">
    <link rel="stylesheet" href="/assets/css/styles.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>'''


def get_header(path='/'):
    nav_items = [
        ('/articles/', 'Articles'),
        ('/cases/', 'Current Focus'),
        ('/districts/', 'Districts'),
        ('/schools/', 'Schools'),
        ('/data/', 'Data'),
        ('/speeches/', 'Speeches'),
        ('/resources/', 'Resources'),
        ('/about/', 'About'),
    ]
    nav_links = '\n'.join(
        f'<li><a href="{u}" class="nav-link{" active" if path.startswith(u) else ""}">{label}</a></li>'
        for u, label in nav_items
    )
    return f'''<body>
    <nav class="nav" id="nav">
        <div class="nav-container">
            <a href="/" class="nav-logo">
                <img src="/assets/images/logo.png" alt="Parent Data Force Logo" class="nav-logo-img">
                <span class="nav-logo-text">PARENT DATA FORCE</span>
            </a>
            <button class="nav-toggle" id="navToggle" aria-label="Toggle navigation">
                <span class="hamburger"></span>
            </button>
            <ul class="nav-menu" id="navMenu">
                {nav_links}
                <li><a href="/search/" class="nav-link">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" style="vertical-align:-3px;">
                        <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                </a></li>
                <li>
                    <a href="https://www.facebook.com/ParentDataForce" class="nav-icon" aria-label="Facebook" title="Parent Data Force on Facebook" target="_blank" rel="noopener">
                        <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                        </svg>
                    </a>
                </li>
                <li><a href="/submit/" class="nav-link nav-link-tip">Submit a Tip</a></li>
                <li><a href="/donate/" class="nav-link nav-link-donate">❤ Donate</a></li>
                <li><button class="theme-toggle" id="themeToggle" aria-label="Toggle theme" title="Switch between Dark and Paper theme">
                    <svg class="theme-icon-dark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                        <circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                    </svg>
                    <svg class="theme-icon-paper" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18" style="display:none;">
                        <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
                    </svg>
                </button></li>
            </ul>
        </div>
    </nav>
    <main>
    <div class="beta-banner" style="text-align:center;padding:0.45rem 1rem;background:rgba(255,90,31,0.08);border-bottom:1px solid rgba(255,90,31,0.15);font-size:0.78rem;color:#ff5a1f;letter-spacing:0.01em;">
        Beta Preview &mdash; data and features are under active development.
    </div>'''


def get_footer():
    return f'''</main>
    <footer class="footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-brand">
                    <div class="footer-logo">
                        <img src="/assets/images/logo.png" alt="Parent Data Force Logo" class="footer-logo-img">
                        <span class="footer-logo-text">PARENT DATA FORCE</span>
                    </div>
                    <p class="footer-tagline">MAKING DATA MAKE SENSE</p>
                    <p class="footer-description">
                        Independent special education and public accountability advocacy.
                    </p>
                </div>
                <div class="footer-nav">
                    <h4 class="footer-nav-title">Content</h4>
                    <ul class="footer-nav-list">
                        <li><a href="/articles/">Articles</a></li>
                        <li><a href="/cases/">Case Directory</a></li>
                        <li><a href="/districts/">Districts</a></li>
                        <li><a href="/data/">Data Browser</a></li>
                        <li><a href="/speeches/">Speeches</a></li>
                        <li><a href="/resources/">Resources</a></li>
                    </ul>
                </div>
                <div class="footer-nav">
                    <h4 class="footer-nav-title">Get Involved</h4>
                    <ul class="footer-nav-list">
                        <li><a href="/submit/">Submit a Tip</a></li>
                        <li><a href="/submit/">Request Help</a></li>
                        <li><a href="/about/">About Us</a></li>
                    </ul>
                </div>
                <div class="footer-contact">
                    <h4 class="footer-nav-title">Stay Updated</h4>
                    <form class="subscribe-form" action="/api/subscribe/" method="post" id="footerSubscribe">
                        <input type="email" name="email" class="form-input" placeholder="Your email address" required style="margin-bottom:0.5rem;">
                        <button type="submit" class="btn btn-primary" style="width:100%;">Subscribe</button>
                    </form>
                </div>
            </div>
            <div class="footer-disclaimer">
                <div class="disclaimer-box">
                    <p>Parent Data Force is an independent advocacy initiative. Information provided on this site is for informational purposes only and does not constitute legal advice.</p>
                </div>
            </div>
            <div class="footer-bottom">
                <p class="copyright">&copy; {datetime.date.today().year} Parent Data Force. All rights reserved.</p>
                <div class="footer-legal"><a href="/about/">Privacy Policy</a></div>
            </div>
        </div>
    </footer>
    <script src="/assets/js/main.js"></script>
    <script src="/assets/js/charts.js"></script>
    <script>
    // Column header click sorting - click any table header to sort
    document.querySelectorAll('.repo-table th').forEach(th => {{
        th.style.cursor = 'pointer';
        th.title = 'Click to sort';
        th.addEventListener('click', () => {{
            const params = new URLSearchParams(window.location.search);
            const col = th.textContent.trim().toLowerCase().replace(/[^a-z0-9]/g,'_');
            const cur = params.get('sort') || '';
            params.set('sort', cur === col+'_desc' ? col+'_asc' : col+'_desc');
            params.set('page', '1');
            window.location.search = params.toString();
        }});
    }});
    </script>
</body>
</html>'''


# 
# Page Handlers
# 

def handle_home():
    conn = get_db()
    featured = conn.execute(
        "SELECT * FROM articles WHERE status = 'published' ORDER BY featured DESC, published_at DESC LIMIT 6"
    ).fetchall()
    recent_updates = conn.execute(
        "SELECT u.*, c.case_id as case_ref FROM updates u LEFT JOIN cases c ON u.related_case_id = c.case_id ORDER BY u.created_at DESC LIMIT 6"
    ).fetchall()
    stats = {
        'articles': conn.execute("SELECT COUNT(*) FROM articles WHERE status = 'published'").fetchone()[0],
        'cases': conn.execute("SELECT COUNT(*) FROM cases WHERE status != 'archived'").fetchone()[0],
        'districts': conn.execute("SELECT COUNT(*) FROM districts WHERE status = 'active'").fetchone()[0],
        'open_cases': conn.execute("SELECT COUNT(*) FROM cases WHERE status = 'open'").fetchone()[0],
    }
    # Live data stats from DESE pipelines
    data_stats = {}
    try:
        data_stats['prs_intakes'] = conn.execute("SELECT COUNT(*) FROM prs_intakes_data").fetchone()[0]
    except:
        data_stats['prs_intakes'] = 0
    try:
        data_stats['restraint_records'] = conn.execute("SELECT COUNT(*) FROM restraint_data WHERE is_summary_row = 0").fetchone()[0]
        data_stats['restraint_year_count'] = conn.execute("SELECT COUNT(DISTINCT school_year) FROM restraint_data").fetchone()[0]
        latest_restraint = conn.execute(
            "SELECT school_year, SUM(total_restraints) as t, SUM(total_injuries) as i FROM restraint_data WHERE is_summary_row = 0 GROUP BY school_year ORDER BY school_year DESC LIMIT 1"
        ).fetchone()
        data_stats['restraint_latest_year'] = latest_restraint['school_year'] if latest_restraint else ''
        data_stats['restraint_latest_count'] = latest_restraint['t'] if latest_restraint else 0
        data_stats['restraint_latest_injuries'] = latest_restraint['i'] if latest_restraint else 0
    except:
        pass
    try:
        data_stats['discipline_districts'] = conn.execute("SELECT COUNT(DISTINCT district_code) FROM discipline_data").fetchone()[0]
        data_stats['discipline_years'] = conn.execute("SELECT COUNT(DISTINCT school_year) FROM discipline_data").fetchone()[0]
        data_stats['enrollment_districts'] = conn.execute("SELECT COUNT(DISTINCT district_code) FROM enrollment_data").fetchone()[0]
    except:
        pass
    try:
        data_stats['prr_count'] = conn.execute("SELECT COUNT(*) FROM prr_tracker").fetchone()[0]
    except:
        data_stats['prr_count'] = 0
    try:
        data_stats['resources_count'] = conn.execute("SELECT COUNT(*) FROM resources WHERE status = 'active'").fetchone()[0]
    except:
        data_stats['resources_count'] = 0
    conn.close()

    head = get_head('Home', 'Parent Data Force - Data-driven advocacy for families.')
    header = get_header('/')
    footer = get_footer()

    body = f'''{head}{header}
<section class="hero" id="hero">
    <div class="hero-bg"></div>
    <div class="hero-overlay"></div>
    <div class="hero-content">
        <div class="hero-tagline">MAKING DATA MAKE SENSE</div>
        <h1 class="hero-title">
            <span class="hero-title-line">Data-Driven Advocacy</span>
            <span class="hero-title-accent">for Families</span>
        </h1>
        <p class="hero-subtitle">Independent special education and public accountability advocacy. Tracking complaints, records, outcomes, and systemic patterns across Massachusetts districts.</p>
        <div class="hero-cta">
            <a href="/cases/" class="btn btn-primary">
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                View Cases
            </a>
            <a href="/articles/" class="btn btn-secondary">
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                Read Articles
            </a>
            <a href="/submit/" class="btn btn-tip">
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                Submit a Tip
            </a>
            <a href="/data/" class="btn btn-ghost">
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                Explore Data
            </a>
        </div>
        <div class="hero-stats">
            <div class="stat"><span class="stat-value">{stats['districts']}</span><span class="stat-label">Districts Tracked</span></div>
            <div class="stat"><span class="stat-value">{stats['open_cases']}</span><span class="stat-label">Active Cases</span></div>
            <div class="stat"><span class="stat-value">{data_stats.get('prs_intakes', 0):,}</span><span class="stat-label">PRS Complaints</span></div>
            <div class="stat"><span class="stat-value">{stats['articles']}</span><span class="stat-label">Articles Published</span></div>
            <div class="stat"><span class="stat-value">{stats['cases']}</span><span class="stat-label">Cases Tracked</span></div>
            <div class="stat"><span class="stat-value">{data_stats.get('prr_count', 0):,}</span><span class="stat-label">PRR Tracker Entries</span></div>
        </div>
    </div>
    <div class="hero-scroll-indicator">
        <span>Scroll to explore</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14l-7 7m0 0l-7-7m7 7V3"/></svg>
    </div>
</section>'''

    # Featured articles
    if featured:
        body += '<section class="section" id="featured"><div class="container"><div class="section-header"><span class="section-tag">Latest Articles</span><h2 class="section-title">Research, Analysis & Advocacy</h2><p class="section-subtitle">Data-driven reporting on special education, public records, and systemic accountability across Massachusetts.</p></div><div class="articles-grid">'
        for a in featured:
            body += f'''<article class="article-card">
    <div class="article-card-body">
        <div class="article-card-meta">
            <span class="article-category">{category_label(a["category"])}</span>
            <span class="article-date">{format_date(a["published_at"])}</span>
        </div>
        <h3 class="article-card-title"><a href="/articles/{h(a["slug"])}">{h(a["title"])}</a></h3>
        <p class="article-card-excerpt">{h(a["excerpt"] or excerpt(a["body"]))}</p>
        <div class="article-card-footer">
            <span class="article-read-time">{a["read_time"] or read_time_est(a["body"])} min read</span>
            <a href="/articles/{h(a["slug"])}" class="resource-link">Read Article</a>
        </div>
    </div>
</article>'''
        body += f'</div><div style="text-align:center;margin-top:2rem;"><a href="/articles/" class="btn btn-secondary">View All Articles</a></div></div></section>'

    # Quick links
    body += '''<section class="section section-dark" id="quick-links"><div class="container"><div class="section-header"><span class="section-tag">Explore</span><h2 class="section-title">What We Track</h2><p class="section-subtitle">Every investigation, public records request, state determination, and systemic pattern - organized and accessible.</p></div>
<div class="resources-grid">
    <article class="resource-card"><h3 class="resource-title">Case Directory</h3><p class="resource-excerpt">Active investigations, public records requests, appeals, and state determinations with full timelines and documents.</p><a href="/cases/" class="resource-link">View Cases</a></article>
    <article class="resource-card"><h3 class="resource-title">Data Browser</h3><p class="resource-excerpt">Interactive exploration of DESE restraint and seclusion data, district analytics, and statewide patterns.</p><a href="/data/" class="resource-link">Explore Data</a></article>
    <article class="resource-card"><h3 class="resource-title">District Profiles</h3><p class="resource-excerpt">Per-district pages aggregating cases, data summaries, and advocacy activity across Massachusetts.</p><a href="/districts/" class="resource-link">View Districts</a></article>
    <article class="resource-card"><h3 class="resource-title">Speeches & Media</h3><p class="resource-excerpt">Public comments, school committee testimony, press coverage, and advocacy media appearances.</p><a href="/speeches/" class="resource-link">Watch Speeches</a></article>
</div></div></section>'''

    # Data at a Glance dashboard
    if data_stats.get('prs_intakes', 0) > 0:
        body += f'''<section class="section" id="data-glance">
    <div class="container">
        <div class="section-header">
            <span class="section-tag">Live Data</span>
            <h2 class="section-title">Data at a Glance</h2>
            <p class="section-subtitle">Real-time statistics from our DESE data pipelines - updated as new data is loaded.</p>
        </div>
        <div class="hero-stats" style="flex-wrap:wrap;gap:1.5rem;">
            <div class="stat">
                <span class="stat-value">{data_stats.get('prs_intakes', 0):,}</span>
                <span class="stat-label">PRS Complaint Records</span>
                <a href="/data/prs/" style="font-size:0.75rem;color:var(--accent);display:block;margin-top:0.25rem;">View PRS Data &rarr;</a>
            </div>
            <div class="stat">
                <span class="stat-value">{data_stats.get('restraint_records', 0):,}</span>
                <span class="stat-label">Restraint Records ({data_stats.get('restraint_year_count', 0)} Years)</span>
                <a href="/data/restraints/" style="font-size:0.75rem;color:var(--accent);display:block;margin-top:0.25rem;">View Restraint Data &rarr;</a>
            </div>
            <div class="stat">
                <span class="stat-value">{data_stats.get('discipline_districts', 0):,}</span>
                <span class="stat-label">Districts w/ Discipline Data</span>
                <a href="/data/discipline/" style="font-size:0.75rem;color:var(--accent);display:block;margin-top:0.25rem;">View Discipline Data &rarr;</a>
            </div>
            <div class="stat">
                <span class="stat-value">{data_stats.get('enrollment_districts', 0):,}</span>
                <span class="stat-label">Districts w/ Enrollment Data</span>
                <a href="/data/enrollment/" style="font-size:0.75rem;color:var(--accent);display:block;margin-top:0.25rem;">View Enrollment Data &rarr;</a>
            </div>
            <div class="stat">
                <span class="stat-value">{data_stats.get('resources_count', 0):,}</span>
                <span class="stat-label">Advocacy Resources</span>
                <a href="/resources/" style="font-size:0.75rem;color:var(--accent);display:block;margin-top:0.25rem;">Browse Resources &rarr;</a>
            </div>
        </div>'''
        if data_stats.get('restraint_latest_count', 0) > 0:
            body += f'''<div style="margin-top:1rem;padding:1rem;background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.15);border-radius:8px;">
                <p style="margin:0;font-size:0.85rem;color:var(--text-muted);">
                    <strong>{data_stats['restraint_latest_year']}</strong>: 
                    <span style="color:var(--danger);">{data_stats['restraint_latest_count']:,} restraints</span> 
                    reported across Massachusetts schools, with 
                    <span style="color:var(--danger);">{data_stats['restraint_latest_injuries']:,} injuries</span>.
                </p>
            </div>'''
        body += '\n    </div>\n</section>\n'

    # Bottom CTA
    body += '<section class="section section-accent" id="cta-bottom"><div class="container"><div class="cta-banner"><h2 class="section-title">Have Information to Share?</h2><p class="section-subtitle" style="max-width:100%;">If you have tips, documents, or data about special education practices, public records concerns, or systemic issues in Massachusetts school districts, we want to hear from you.</p><div class="hero-cta" style="margin-top:1rem;"><a href="/submit/" class="btn btn-primary">Submit a Tip</a><a href="/submit/" class="btn btn-secondary">Request Help</a></div></div></div></section>'

    return body + footer


def handle_articles(path):
    conn = get_db()

    if path == '/articles/' or path == '/articles':
        page = 1
        category = ''
        search = ''
        qs = ''
        if '?' in path:
            qs = path.split('?', 1)[1]
            params = urllib.parse.parse_qs(qs)
            page = max(1, int(params.get('page', ['1'])[0]))
            category = params.get('category', [''])[0]
            search = params.get('search', [''])[0]

        per_page = 12
        offset = (page - 1) * per_page

        where = ["a.status = 'published'"]
        db_params = []
        if category and category != 'all':
            where.append('a.category = ?')
            db_params.append(category)
        if search:
            where.append('(a.title LIKE ? OR a.excerpt LIKE ?)')
            st = f'%{search}%'
            db_params.extend([st, st])

        where_clause = ' AND '.join(where)

        total = conn.execute(f"SELECT COUNT(*) FROM articles a WHERE {where_clause}", db_params).fetchone()[0]
        articles = conn.execute(
            f"SELECT * FROM articles a WHERE {where_clause} ORDER BY a.published_at DESC LIMIT ? OFFSET ?",
            db_params + [per_page, offset]
        ).fetchall()

        cats = conn.execute("SELECT category, COUNT(*) as total FROM articles WHERE status = 'published' GROUP BY category ORDER BY category").fetchall()

        head = get_head('Articles', 'Data-driven reporting on special education, public records, and systemic accountability.')
        body = f'{head}{get_header("/articles/")}<section class="section"><div class="container"><div class="section-header"><span class="section-tag">Research & Analysis</span><h2 class="section-title">Articles</h2><p class="section-subtitle">Investigative reporting, data analysis, methodology guides, and policy commentary.</p></div>'

        # Filter form
        body += '<div class="articles-controls"><form method="get"><div class="articles-search-form">'
        body += f'<div class="repo-search" style="flex:1;max-width:400px;"><svg class="repo-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg><input type="text" name="search" class="repo-search-input" placeholder="Search articles..." value="{h(search)}"></div>'
        body += '<select name="category" class="repo-select" onchange="this.form.submit()" style="max-width:200px;"><option value="all">All Categories</option>'
        for c in cats:
            body += f'<option value="{h(c["category"])}" {"selected" if category == c["category"] else ""}>{category_label(c["category"])} ({c["total"]})</option>'
        body += '</select><button type="submit" class="btn btn-ghost" style="padding:0.63rem 1rem;">Filter</button>'
        if search or category:
            body += '<a href="/articles/" class="btn btn-ghost" style="padding:0.63rem 1rem;">Clear</a>'
        body += '</div></form></div>'

        if not articles:
            body += '<div class="empty-state"><p>Articles will appear here once published.</p></div>'
        else:
            body += '<div class="articles-grid">'
            for a in articles:
                body += f'''<article class="article-card">
    <div class="article-card-body">
        <div class="article-card-meta"><span class="article-category">{category_label(a["category"])}</span><span class="article-date">{format_date(a["published_at"])}</span></div>
        <h3 class="article-card-title"><a href="/articles/{h(a["slug"])}">{h(a["title"])}</a></h3>
        <p class="article-card-excerpt">{h(a["excerpt"] or excerpt(a["body"]))}</p>
        <div class="article-card-footer"><span class="article-read-time">{a["read_time"] or read_time_est(a["body"])} min read</span><a href="/articles/{h(a["slug"])}" class="resource-link">Read Article</a></div>
    </div>
</article>'''
            body += '</div>'

            total_pages = max(1, (total + per_page - 1) // per_page)
            if total_pages > 1:
                body += '<div class="pagination">'
                if page > 1:
                    body += f'<a href="?page={page-1}{"&category=" + urllib.parse.quote(category) if category else ""}{"&search=" + urllib.parse.quote(search) if search else ""}" class="btn btn-ghost">&larr; Previous</a>'
                body += f'<span class="pagination-info">Page {page} of {total_pages} ({total} articles)</span>'
                if page < total_pages:
                    body += f'<a href="?page={page+1}{"&category=" + urllib.parse.quote(category) if category else ""}{"&search=" + urllib.parse.quote(search) if search else ""}" class="btn btn-ghost">Next &rarr;</a>'
                body += '</div>'

        conn.close()
        return body + '</div></section>' + get_footer()

    # Single article: /articles/slug
    slug = path.split('/articles/', 1)[1].split('?')[0].split('/')[0]
    if not slug:
        conn.close()
        return handle_redirect('/articles/')

    article = conn.execute(
        "SELECT * FROM articles WHERE slug = ? AND status = 'published'", (slug,)
    ).fetchone()

    if not article:
        conn.close()
        return handle_404()

    related_articles = conn.execute(
        "SELECT * FROM articles WHERE category = ? AND id != ? AND status = 'published' ORDER BY published_at DESC LIMIT 3",
        (article['category'], article['id'])
    ).fetchall()

    related_cases = conn.execute(
        "SELECT c.* FROM cases c JOIN article_case_links acl ON c.id = acl.case_id WHERE acl.article_id = ?",
        (article['id'],)
    ).fetchall()

    body_html = render_shortcodes(article['body'] or '')

    head = get_head(article['seo_title'] or article['title'], article['seo_description'] or article['excerpt'] or excerpt(article['body'], 200))
    body = f'{head}{get_header("/articles/")}<section class="section"><div class="container"><article class="article-full">'
    body += f'<header class="article-header"><div class="article-header-meta"><span class="article-category article-category-large">{category_label(article["category"])}</span><span class="article-date">{format_date(article["published_at"])}</span><span class="article-read-time">{article["read_time"] or read_time_est(article["body"])} min read</span></div><h1 class="article-title">{h(article["title"])}</h1>'
    if article['excerpt']:
        body += f'<p class="article-excerpt">{h(article["excerpt"])}</p>'
    body += '</header><div class="article-body">' + body_html + '</div>'

    # Related cases
    if related_cases:
        body += '<div class="article-related"><h3 class="article-related-title">Related Cases</h3><div class="cases-grid" style="grid-template-columns:repeat(2, minmax(0,1fr));">'
        for c in related_cases:
            body += f'''<div class="case-card">
    <div class="case-card-header"><div class="case-district">{h(c["district_code"])}, MA</div>{status_badge(c["status"])}</div>
    <div class="case-card-id">{h(c["case_id"])}</div>
    <h3 class="case-card-title">{h(c["title"])}</h3>
    <a href="/cases/{h(c["case_id"])}" class="case-card-btn">View Case Details</a>
</div>'''
        body += '</div></div>'

    # Related articles
    if related_articles:
        body += '<div class="article-related"><h3 class="article-related-title">Related Articles</h3><div class="articles-grid" style="grid-template-columns:repeat(3, minmax(0,1fr));">'
        for ra in related_articles:
            body += f'''<article class="article-card"><div class="article-card-body">
    <div class="article-card-meta"><span class="article-category">{category_label(ra["category"])}</span><span class="article-date">{format_date(ra["published_at"])}</span></div>
    <h3 class="article-card-title"><a href="/articles/{h(ra["slug"])}">{h(ra["title"])}</a></h3>
</div></article>'''
        body += '</div></div>'

    conn.close()
    return body + '</article></div></section>' + get_footer()


def handle_cases(path):
    conn = get_db()

    if path == '/cases/' or path == '/cases':
        district = ''
        typ = ''
        status = ''
        search = ''
        page = 1
        if '?' in path:
            params = urllib.parse.parse_qs(path.split('?', 1)[1])
            page = max(1, int(params.get('page', ['1'])[0]))
            district = params.get('district', [''])[0]
            typ = params.get('type', [''])[0]
            status = params.get('status', [''])[0]
            search = params.get('search', [''])[0]

        per_page = 20
        offset = (page - 1) * per_page

        where = ["c.status != 'archived'"]
        db_params = []
        if district and district != 'all':
            where.append('c.district_code = ?')
            db_params.append(district)
        if typ and typ != 'all':
            where.append('c.type = ?')
            db_params.append(typ)
        if status and status != 'all':
            where.append('c.status = ?')
            db_params.append(status)
        if search:
            where.append('(c.title LIKE ? OR c.summary LIKE ? OR c.case_id LIKE ?)')
            st = f'%{search}%'
            db_params.extend([st, st, st])

        where_clause = ' AND '.join(where)
        total = conn.execute(f"SELECT COUNT(*) FROM cases c WHERE {where_clause}", db_params).fetchone()[0]
        cases = conn.execute(
            f"SELECT c.*, COUNT(cd.id) as doc_count FROM cases c LEFT JOIN case_documents cd ON c.id = cd.case_id WHERE {where_clause} GROUP BY c.id ORDER BY c.filed_date DESC LIMIT ? OFFSET ?",
            db_params + [per_page, offset]
        ).fetchall()

        districts = conn.execute("SELECT code, name FROM districts WHERE status = 'active' ORDER BY name").fetchall()

        head = get_head('Case Directory', 'Active investigations, public records requests, appeals, and state determinations across Massachusetts districts.')
        body = f'{head}{get_header("/cases/")}<section class="section"><div class="container"><div class="section-header"><span class="section-tag">Case Portfolio</span><h2 class="section-title">Case Directory</h2><p class="section-subtitle">Active investigations, public records requests, appeals, and state determinations.</p></div>'

        body += '<div class="case-filters"><form method="get" class="articles-search-form">'
        body += f'<div class="repo-search" style="flex:1;max-width:400px;"><svg class="repo-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg><input type="text" name="search" class="repo-search-input" placeholder="Search cases..." value="{h(search)}"></div>'
        body += '<select name="district" class="repo-select" onchange="this.form.submit()" style="max-width:200px;"><option value="all">All Districts</option>'
        for d in districts:
            body += f'<option value="{h(d["code"])}" {"selected" if district == d["code"] else ""}>{h(d["name"])}</option>'
        body += '</select><select name="status" class="repo-select" onchange="this.form.submit()" style="max-width:160px;"><option value="all">All Statuses</option>'
        for s in ['open', 'pending', 'closed', 'overdue']:
            body += f'<option value="{s}" {"selected" if status == s else ""}>{s.title()}</option>'
        body += '</select><button type="submit" class="btn btn-ghost" style="padding:0.63rem 1rem;">Filter</button>'
        if search or district or status:
            body += '<a href="/cases/" class="btn btn-ghost" style="padding:0.63rem 1rem;">Clear</a>'
        body += '</form></div>'

        if not cases:
            body += '<div class="empty-state"><p>No cases found.</p></div>'
        else:
            body += '<div class="cases-grid">'
            for c in cases:
                body += f'''<div class="case-card">
    <div class="case-card-header"><div class="case-district">{h(c["district_code"])}, MA</div>{status_badge(c["status"])}</div>
    <div class="case-card-id">{h(c["case_id"])}</div>
    <h3 class="case-card-title">{h(c["title"])}</h3>
    <p class="case-card-summary">{h(c["summary"] or "")[:150]}...</p>
    <div class="case-card-meta">
        <div class="meta-item"><span class="meta-label">Type</span><span class="meta-value">{case_type_label(c["type"])}</span></div>
        <div class="meta-item"><span class="meta-label">Filed</span><span class="meta-value">{format_date(c["filed_date"])}</span></div>
        <div class="meta-item"><span class="meta-label">Deadline</span><span class="meta-value">{format_date(c["deadline"])}</span></div>
        <div class="meta-item"><span class="meta-label">Docs</span><span class="meta-value">{c["doc_count"]}</span></div>
    </div>
    <a href="/cases/{h(c["case_id"])}" class="case-card-btn">View Case Details<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14"><path d="M9 5l7 7-7 7"/></svg></a>
</div>'''
            body += '</div>'

            total_pages = max(1, (total + per_page - 1) // per_page)
            if total_pages > 1:
                body += '<div class="pagination">'
                qs = f'{"&district=" + urllib.parse.quote(district) if district else ""}{"&type=" + urllib.parse.quote(typ) if typ else ""}{"&status=" + urllib.parse.quote(status) if status else ""}{"&search=" + urllib.parse.quote(search) if search else ""}'
                if page > 1:
                    body += f'<a href="?page={page-1}{qs}" class="btn btn-ghost">&larr; Previous</a>'
                body += f'<span class="pagination-info">Page {page} of {total_pages} ({total} cases)</span>'
                if page < total_pages:
                    body += f'<a href="?page={page+1}{qs}" class="btn btn-ghost">Next &rarr;</a>'
                body += '</div>'

        conn.close()
        return body + '</div></section>' + get_footer()

    # Single case: /cases/case_id
    case_id = path.split('/cases/', 1)[1].split('?')[0].split('/')[0].strip()
    if not case_id:
        conn.close()
        return handle_redirect('/cases/')

    case = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    if not case:
        conn.close()
        return handle_404()

    docs = conn.execute("SELECT * FROM case_documents WHERE case_id = ? ORDER BY sort_order, document_date DESC", (case['id'],)).fetchall()
    related = conn.execute(
        "SELECT a.id, a.title, a.slug, a.category, a.published_at, a.read_time FROM articles a JOIN article_case_links acl ON a.id = acl.article_id WHERE acl.case_id = ? AND a.status = 'published' ORDER BY a.published_at DESC",
        (case['id'],)
    ).fetchall()

    timeline = json.loads(case['timeline'] or '[]')
    requested = json.loads(case['requested_items'] or '[]')

    head = get_head(case['title'], case['summary'])
    body = f'{head}{get_header("/cases/")}<section class="section"><div class="container"><div class="case-detail-header">'
    body += f'<div class="case-detail-meta"><a href="/districts/{case["district_code"].lower()}" class="case-district">{h(case["district_code"])}, MA</a>{status_badge(case["status"])}</div>'
    body += f'<span class="case-detail-id">{h(case["case_id"])}</span><h1 class="case-detail-title">{h(case["title"])}</h1><p class="case-detail-summary">{h(case["summary"])}</p>'
    body += f'<div class="case-detail-stats"><div class="stat"><span class="stat-label">Type</span><span class="stat-value" style="font-size:0.95rem;">{case_type_label(case["type"])}</span></div><div class="stat"><span class="stat-label">Filed</span><span class="stat-value" style="font-size:0.95rem;">{format_date(case["filed_date"], "%b %d, %Y")}</span></div><div class="stat"><span class="stat-label">Deadline</span><span class="stat-value" style="font-size:0.95rem;">{format_date(case["deadline"], "%b %d, %Y")}</span></div><div class="stat"><span class="stat-label">Stage</span><span class="stat-value" style="font-size:0.95rem;">{h(case["current_stage"] or "In Progress")}</span></div></div>'
    body += '</div>'

    if requested:
        body += '<div class="case-detail-section"><h3>Requested Records / Scope</h3><ul>'
        for item in requested:
            body += f'<li>{h(item)}</li>'
        body += '</ul></div>'

    if timeline:
        body += '<div class="case-detail-section"><h3>Case Timeline</h3><ul class="timeline-list">'
        for e in timeline:
            docs_html = ''
            if e.get('docs'):
                docs_html = '<div class="timeline-docs">'
                for d in e['docs']:
                    if isinstance(d, str):
                        docs_html += f'<span class="timeline-doc">{h(d)}</span>'
                    else:
                        docs_html += f'<a class="timeline-doc" href="{h(d.get("url","#"))}" target="_blank">{h(d.get("label","Doc"))}</a>'
                docs_html += '</div>'
            body += f'<li class="timeline-item"><div class="timeline-item-head"><span class="timeline-item-title">{h(e.get("title",""))}</span><span class="timeline-item-date">{h(e.get("date",""))}</span></div><p>{h(e.get("description",""))}</p>{docs_html}</li>'
        body += '</ul></div>'

    if docs:
        body += '<div class="case-detail-section"><h3>Documents</h3><div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>Date</th><th>Type</th><th>Title</th><th>File</th></tr></thead><tbody>'
        for d in docs:
            file_link = f'<a href="{h(d["file_path"] or "#")}" class="doc-link" target="_blank"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14"><path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>{h((d["file_type"] or "FILE").upper())}</a>' if d['file_path'] else '<span style="color:var(--text-muted);">-</span>'
            body += f'<tr><td class="repo-date">{format_date(d["document_date"])}</td><td>{h(d["document_type"].replace("_"," ").title())}</td><td>{h(d["title"])}</td><td>{file_link}</td></tr>'
        body += '</tbody></table></div></div>'

    if related:
        body += '<div class="case-detail-section"><h3>Related Articles</h3><div class="articles-grid" style="grid-template-columns:repeat(2,minmax(0,1fr));">'
        for ra in related:
            body += f'<article class="article-card"><div class="article-card-body"><div class="article-card-meta"><span class="article-category">{category_label(ra["category"])}</span><span class="article-date">{format_date(ra["published_at"])}</span></div><h3 class="article-card-title"><a href="/articles/{h(ra["slug"])}">{h(ra["title"])}</a></h3></div></article>'
        body += '</div></div>'

    conn.close()
    return body + '<div style="margin-top:2rem;"><a href="/cases/" class="btn btn-ghost">&larr; Back to Case Directory</a></div></div></section>' + get_footer()


def handle_data():
    qs = {}
    if '?' in _current_path:
        qs = dict(urllib.parse.parse_qsl(_current_path.split('?', 1)[1]))

    if qs.get('tab') == 'compare':
        return _handle_compare_tab()

    return _handle_data_portal()


def _handle_data_portal():
    conn = get_db()

    def safe_count(table):
        try:
            r = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            return r[0] if r else 0
        except:
            return None

    datasets = [
        ('Restraint & Seclusion', 'restraint_data', '/data/restraint/',
         'Statewide school-level restraint and seclusion records from DESE.'),
        ('Discipline', 'discipline_data', '/data/discipline/',
         'District-level discipline data including suspensions, expulsions, and law enforcement referrals.'),
        ('Enrollment / SPED', 'enrollment_data', '/data/enrollment/',
         'Enrollment demographics, high needs, English learners, low income, and special education percentages.'),
        ('PRS Data Dashboard', 'prs_intakes_data', '/data/prs/',
         'Problem Resolution System complaint intake and status data.'),
        ('PRR Tracker', 'prr_tracker', '/data/prr-tracker/',
         'Complete audit trail of public records requests - agencies, stages, deadlines, and outcomes.'),
        ('Public Records Timeline', 'prr_tracker', '/data/public-records/',
         'Chronological timeline of all records requests, PRS documents, and SPR appeals.'),
        ('Aggregate Request Catalog', 'aggregate_catalog', '/data/request-catalog/',
         'Pattern library mapping record categories to public records lanes and SPR outcomes.'),
        ('Resource Center', 'resources', '/resources/',
         'Links, contacts, and advocacy resources organized by issue.'),
        ('Attendance', 'attendance_data', '/data/attendance/',
         'District attendance rates, chronic absenteeism, and absence patterns.'),
        ('SPED Results', 'sped_results', '/data/sped-results/',
         'Special education graduation rates, dropout rates, LRE inclusion, and parent involvement.'),
    ]

    cards = []
    for name, table, url, desc in datasets:
        count = safe_count(table)
        if count is None or count == 0:
            if name == 'Restraint & Seclusion':
                count_text = '<span style="color:var(--text-muted);">Not loaded</span>'
            elif name == 'PRS Data Dashboard':
                count_text = '<span style="color:var(--text-muted);">Sample available</span>'
            else:
                count_text = '<span style="color:var(--text-muted);">Not loaded</span>'
        else:
            count_text = f'<span style="font-weight:700;color:var(--accent-glow);">{count:,} rows</span>'
        cards.append((name, count_text, url, desc))

    conn.close()

    head = get_head('Data Browser', 'Explore datasets covering discipline, enrollment, attendance, SPED outcomes, and public records across Massachusetts districts.')
    body = f'{head}{get_header("/data/")}<section class="section"><div class="container"><div class="section-header"><span class="section-tag">Data & Analytics</span><h2 class="section-title">Data Browser</h2><p class="section-subtitle">Explore datasets covering discipline, enrollment, attendance, SPED outcomes, and public records across Massachusetts districts.</p></div>'

    body += '<div class="data-tabs"><a href="/data/" class="data-tab active">Data Browser</a><a href="/data/?tab=compare" class="data-tab">Compare Districts</a></div>'

    body += '<div class="resources-grid">'
    for name, count_text, url, desc in cards:
        body += f'''<a href="{url}" class="resource-card">
    <h3 class="resource-title">{h(name)}</h3>
    <p style="margin:0.35rem 0;">{count_text}</p>
    <p style="font-size:0.88rem;color:var(--text-secondary);margin:0.5rem 0;">{h(desc)}</p>
    <span class="resource-link">Explore Dataset</span>
</a>'''
    body += '</div>'

    return body + '</div></section>' + get_footer()



def _handle_compare_tab():
    conn = get_db()
    school_year = '2024-25'

    restraint_rows = conn.execute("""
        SELECT district_name,
               SUM(total_restraints) as total_restraints,
               SUM(students_restrained) as students_restrained,
               SUM(total_injuries) as total_injuries,
               SUM(enrollment) as enrollment
        FROM restraint_data
        WHERE school_year = ? AND is_summary_row = 0
        GROUP BY district_name
    """, (school_year,)).fetchall()

    restraint_map = {}
    for r in restraint_rows:
        name = r['district_name']
        enroll = r['enrollment'] or 0
        total_r = r['total_restraints'] or 0
        restraint_map[name] = {
            'total_restraints': total_r,
            'students_restrained': r['students_restrained'] or 0,
            'total_injuries': r['total_injuries'] or 0,
            'enrollment': enroll,
            'restraint_rate': round((total_r / enroll * 100), 2) if enroll > 0 else 0,
        }

    enroll_rows = conn.execute("""
        SELECT district_name, sped_pct, low_income_pct, el_pct
        FROM enrollment_data
        WHERE school_year = ?
    """, (school_year,)).fetchall()

    enroll_map = {}
    for r in enroll_rows:
        enroll_map[r['district_name']] = {
            'sped_pct': r['sped_pct'],
            'low_income_pct': r['low_income_pct'],
            'el_pct': r['el_pct'],
        }

    disc_rows = conn.execute("""
        SELECT district_name, pct_out_school_susp
        FROM discipline_data
        WHERE school_year = ?
    """, (school_year,)).fetchall()

    disc_map = {r['district_name']: r['pct_out_school_susp'] for r in disc_rows}

    att_rows = conn.execute("""
        SELECT district_name, attendance_rate, chronically_absent_10_pct
        FROM attendance_data
        WHERE school_year = ?
    """, (school_year,)).fetchall()

    att_map = {}
    for r in att_rows:
        att_map[r['district_name']] = {
            'attendance_rate': r['attendance_rate'],
            'chr_absent_pct': r['chronically_absent_10_pct'],
        }

    conn.close()

    compare_data = []
    all_names = set(restraint_map.keys()) | set(enroll_map.keys()) | set(disc_map.keys()) | set(att_map.keys())
    for name in sorted(all_names):
        r = restraint_map.get(name, {})
        e = enroll_map.get(name, {})
        d_pct = disc_map.get(name)
        a = att_map.get(name, {})

        compare_data.append({
            'district_name': name,
            'total_restraints': r.get('total_restraints', 0),
            'students_restrained': r.get('students_restrained', 0),
            'total_injuries': r.get('total_injuries', 0),
            'enrollment': r.get('enrollment', 0),
            'restraint_rate': r.get('restraint_rate', 0),
            'sped_pct': e.get('sped_pct'),
            'low_income_pct': e.get('low_income_pct'),
            'el_pct': e.get('el_pct'),
            'oss_pct': d_pct,
            'attendance_rate': a.get('attendance_rate'),
            'chr_absent_pct': a.get('chr_absent_pct'),
        })

    data_json = json.dumps(compare_data)

    district_options = ''.join(
        f'<option value="{h(d["district_name"])}">{h(d["district_name"])}</option>'
        for d in compare_data if d['enrollment'] > 0
    )

    all_district_options = ''.join(
        f'<option value="{h(d["district_name"])}">{h(d["district_name"])}</option>'
        for d in compare_data
    )

    top30 = sorted([d for d in compare_data if d['total_restraints'] > 0],
                   key=lambda x: x['total_restraints'], reverse=True)[:30]

    table_rows = ''
    for d in top30:
        table_rows += f'''<tr>
    <td>{h(d['district_name'])}</td>
    <td class="num">{d['total_restraints']:,}</td>
    <td class="num">{d['total_injuries']:,}</td>
    <td class="num">{d['restraint_rate']}</td>
    <td class="num">{d['sped_pct'] if d['sped_pct'] is not None else chr(8212)}</td>
    <td class="num">{d['low_income_pct'] if d['low_income_pct'] is not None else chr(8212)}</td>
    <td class="num">{d['oss_pct'] if d['oss_pct'] is not None else chr(8212)}</td>
    <td class="num">{d['attendance_rate'] if d['attendance_rate'] is not None else chr(8212)}</td>
    <td class="num">{d['chr_absent_pct'] if d['chr_absent_pct'] is not None else chr(8212)}</td>
</tr>'''

    head = get_head('Compare Districts', 'Compare restraint, discipline, enrollment, and attendance data across Massachusetts school districts for 2024-25.')
    body = f'{head}{get_header("/data/")}<section class="section"><div class="container">'

    body += '<div class="section-header"><span class="section-tag">Data & Analytics</span><h2 class="section-title">District Comparison</h2><p class="section-subtitle">Compare restraint, discipline, enrollment, and attendance data across Massachusetts districts for 2024-25.</p></div>'

    body += '<div class="data-tabs"><a href="/data/" class="data-tab">Data Browser</a><a href="/data/?tab=compare" class="data-tab active">Compare Districts</a></div>'

    body += f'\n<script id="compare-districts-data" type="application/json">{data_json}</script>'

    body += '<div class="restraint-comparison-panel"><h3 style="margin-bottom:1rem;">Select Districts to Compare</h3><div class="compare-select-row"><div style="flex:1;min-width:200px;"><label style="font-size:0.8rem;color:var(--text-muted);display:block;margin-bottom:0.3rem;">District A</label><select id="compare-district-a" class="form-input" style="width:100%;"><option value="">-- Select a district --</option>' + district_options + '</select></div><div style="flex:1;min-width:200px;"><label style="font-size:0.8rem;color:var(--text-muted);display:block;margin-bottom:0.3rem;">District B</label><select id="compare-district-b" class="form-input" style="width:100%;"><option value="">-- Select a district --</option>' + district_options + '</select></div></div><div class="compare-chart-container"><canvas id="districtCompareChart"></canvas></div><div class="similar-districts-panel"><h4>Similar Districts</h4><p style="color:var(--text-muted);font-size:0.82rem;margin-bottom:0.75rem;">Add districts with similar demographics or restraint patterns to compare against.</p><div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;margin-bottom:0.75rem;"><select id="similar-district-select" class="form-input" style="min-width:200px;"><option value="">-- Add a district --</option>' + all_district_options + '</select><button id="similar-district-add" class="similar-district-add">+ Add to Chart</button></div><div id="similar-districts-list" style="display:flex;flex-wrap:wrap;gap:0.35rem;"></div></div></div>'

    body += '<div style="margin-top:2.5rem;"><h3 style="margin-bottom:1rem;">Top 30 Districts by Total Restraints (2024-25)</h3><div class="repo-table-wrapper"><table class="repo-table sortable"><thead><tr><th>District</th><th class="num">Total Restraints</th><th class="num">Injuries</th><th class="num">Rate / 100</th><th class="num">SPED %</th><th class="num">Low Income %</th><th class="num">OSS %</th><th class="num">Attendance %</th><th class="num">Chr. Absent %</th></tr></thead><tbody>' + table_rows + '</tbody></table></div></div>'


    body += '</div></section>' + get_footer()
    return body

def handle_search():
    query = ''
    if '?' in urllib.parse.urlparse('http://placeholder' + ('' if '?' not in ('?q=test',) else '')).geturl():
        pass

    head = get_head('Search', 'Search across Parent Data Force articles, cases, and speeches.')
    body = f'{head}{get_header("/search/")}<section class="section"><div class="container"><div class="section-header"><span class="section-tag">Search</span><h2 class="section-title">Search the Site</h2><p class="section-subtitle">Search across articles, cases, and speeches.</p></div>'
    body += '<form method="get"><div class="repo-search" style="max-width:600px;"><svg class="repo-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg><input type="text" name="q" class="repo-search-input" placeholder="Search articles, cases, and speeches..." autofocus></div><button type="submit" class="btn btn-primary" style="margin-top:0.6rem;">Search</button></form>'
    body += '</div></section>' + get_footer()
    return body


def handle_speeches():
    conn = get_db()
    speeches = conn.execute("SELECT * FROM speeches ORDER BY published_at DESC").fetchall()
    conn.close()

    head = get_head('Speeches & Media', 'Public comments, school committee testimony, press coverage, and advocacy media appearances.')
    body = f'{head}{get_header("/speeches/")}<section class="section"><div class="container"><div class="section-header"><span class="section-tag">Media & Advocacy</span><h2 class="section-title">Speeches & Media</h2><p class="section-subtitle">Public comments, school committee testimony, hearings, presentations, and media coverage.</p></div>'

    if not speeches:
        body += '<div class="empty-state"><p>Speeches and media appearances will appear here.</p></div>'
    else:
        body += '<div class="speeches-grid">'
        for s in speeches:
            if s['platform'].lower() == 'youtube':
                video = f'<div class="speech-video"><iframe src="https://www.youtube.com/embed/{h(s["video_id"])}" allowfullscreen loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" style="border:none;"></iframe></div>'
            else:
                video = f'<a href="{h(s["url"])}" target="_blank" class="btn btn-secondary" style="margin-top:0.5rem;">Watch / View</a>'
            case_link = f'<div style="margin-top:0.5rem;"><a href="/cases/{h(s["related_case_id"])}" class="related-link">Related: {h(s["related_case_id"])}</a></div>' if s['related_case_id'] else ''
            body += f'''<div class="speech-card">
    <div class="speech-card-header"><span class="speech-category">{h(s["category"].replace("_"," ").title())}</span><span class="speech-date">{format_date(s["published_at"])}</span></div>
    <h3 class="speech-title">{h(s["title"])}</h3>
    {f'<p class="speech-desc">{h(s["description"] or "")}</p>' if s["description"] else ''}
    {video}
    {case_link}
</div>'''
        body += '</div>'

    return body + '</div></section>' + get_footer()


def handle_submit():
    head = get_head('Submit Information', 'Submit a tip, request help, or upload files to Parent Data Force.')
    body = f'{head}{get_header("/submit/")}<section class="section"><div class="container"><div class="section-header"><span class="section-tag">Get Involved</span><h2 class="section-title">Submit Information</h2><p class="section-subtitle">Share tips, request advocacy help, or upload documents and data for review.</p></div>'

    body += '''<div class="submit-tabs">
        <button class="submit-tab active" data-tab="tip">Submit a Tip</button>
        <button class="submit-tab" data-tab="help">Request Help</button>
        <button class="submit-tab" data-tab="upload">Upload Data</button>
    </div>'''

    body += '''<div class="submit-content active" id="tab-tip"><div class="tip-banner" style="grid-template-columns:1fr;">
        <div class="tip-banner-copy"><h3>Report a Concern</h3><p style="color:var(--text-secondary);margin-bottom:1rem;">Report urgent district concerns, emerging incidents, documentation gaps, or recurring patterns. All submissions are reviewed.</p></div>
        <form class="submit-form" method="post">
            <div class="form-grid">
                <div class="form-group"><label class="form-label">District / Agency</label><input type="text" class="form-input" placeholder="e.g., Fall River Public Schools"></div>
                <div class="form-group"><label class="form-label">Concern Type</label><select class="form-select"><option>Select...</option><option>Public records concern</option><option>Special education concern</option><option>Compliance failure</option><option>Safety incident</option><option>Other</option></select></div>
                <div class="form-group form-group-full"><label class="form-label">Details</label><textarea class="form-textarea" rows="5" placeholder="Describe what happened, when, and what documentation might exist."></textarea></div>
                <div class="form-group"><label class="form-label">Email (Optional)</label><input type="email" class="form-input" placeholder="For follow-up"></div>
                <div class="form-group"><label class="form-label">Attach Files (Optional)</label><input type="file" class="form-input" multiple></div>
                <button type="submit" class="btn btn-primary form-group-full">Send Tip</button>
            </div>
        </form>
    </div></div>'''

    body += '''<div class="submit-content" id="tab-help"><div class="tip-banner" style="grid-template-columns:1fr;">
        <div class="tip-banner-copy"><h3>Request Advocacy Help</h3><p style="color:var(--text-secondary);margin-bottom:1rem;">Need help with a special education issue, public records request, or advocacy strategy? Describe your situation and we''ll respond.</p></div>
        <form class="submit-form" method="post">
            <div class="form-grid">
                <div class="form-group"><label class="form-label">Your Name</label><input type="text" class="form-input"></div>
                <div class="form-group"><label class="form-label">Email</label><input type="email" class="form-input" required></div>
                <div class="form-group"><label class="form-label">District / Agency</label><input type="text" class="form-input"></div>
                <div class="form-group"><label class="form-label">Help Type</label><select class="form-select"><option>IEP / 504 concerns</option><option>Restraint / seclusion</option><option>Public records help</option><option>Filing a complaint</option><option>Advocacy strategy</option><option>Other</option></select></div>
                <div class="form-group form-group-full"><label class="form-label">Describe Your Situation</label><textarea class="form-textarea" rows="5"></textarea></div>
                <button type="submit" class="btn btn-primary form-group-full">Request Help</button>
            </div>
        </form>
    </div></div>'''

    body += '''<div class="submit-content" id="tab-upload"><div class="tip-banner" style="grid-template-columns:1fr;">
        <div class="tip-banner-copy"><h3>Upload Data or Files</h3><p style="color:var(--text-secondary);margin-bottom:1rem;">Have public records, district data, or documentation? Upload files for review and potential publication.</p></div>
        <form class="submit-form" method="post" enctype="multipart/form-data">
            <div class="form-grid">
                <div class="form-group"><label class="form-label">District / Agency</label><input type="text" class="form-input"></div>
                <div class="form-group"><label class="form-label">Email (Optional)</label><input type="email" class="form-input"></div>
                <div class="form-group form-group-full"><label class="form-label">Description</label><textarea class="form-textarea" rows="3" placeholder="What does this data contain?"></textarea></div>
                <div class="form-group form-group-full"><label class="form-label">Files</label><input type="file" class="form-input" multiple></div>
                <button type="submit" class="btn btn-primary form-group-full">Upload Files</button>
            </div>
        </form>
    </div></div>'''

    body += '''<script>
document.querySelectorAll('.submit-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.submit-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.submit-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const target = document.getElementById('tab-' + tab.dataset.tab);
        if (target) target.classList.add('active');
    });
});
    </script>'''

def handle_about():
    head = get_head('About', 'Parent Data Force is an independent special education and public accountability advocacy initiative.')
    body = head + get_header("/about/") + '''<section class="section"><div class="container">
    <div class="section-header"><span class="section-tag">About Us</span><h2 class="section-title">Independent Advocacy for Public Accountability</h2><p class="section-subtitle">Parent Data Force is an independent special education and public accountability advocacy initiative. We track complaints, analyze records, document outcomes, and expose systemic patterns.</p></div>
    <div class="mission-statement"><div class="mission-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg></div><blockquote class="mission-text">"To ensure every family navigating special education and public systems has access to transparent information, documented evidence, and strategic advocacy support."</blockquote></div>
    <div class="values-grid">
        <div class="value-card"><div class="value-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></div><h3 class="value-title">Documentation</h3><p class="value-description">Meticulous tracking of complaints, records requests, responses, and outcomes. Every detail matters when building a case for accountability.</p></div>
        <div class="value-card"><div class="value-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg></div><h3 class="value-title">Accountability</h3><p class="value-description">Holding districts and agencies accountable through documented evidence, public records requests, and formal complaints when necessary.</p></div>
        <div class="value-card"><div class="value-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg></div><h3 class="value-title">Strategy</h3><p class="value-description">Evidence-based approach combining public records law, complaint procedures, and systemic analysis to achieve meaningful outcomes.</p></div>
        <div class="value-card"><div class="value-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg></div><h3 class="value-title">Public Interest</h3><p class="value-description">Information belongs to the public. We work to ensure transparency in public systems and make advocacy resources accessible to all families.</p></div>
    </div>
    <div style="padding:3rem 0 0;"><h3 class="section-title" style="font-size:1.5rem;">Privacy</h3><p class="section-subtitle" style="max-width:100%;">Parent Data Force does not sell, share, or monetize personal information. Any information submitted through our forms is used solely for advocacy purposes. We do not use tracking cookies or third-party analytics.</p></div>
    </div></section>'''
    return body + get_footer()


def handle_districts(path=''):
    conn = get_db()
    code = None
    if path and path not in ('/districts/', '/districts'):
        code = path.split('/districts/', 1)[1].split('?')[0].split('/')[0].strip().upper()

    if not code:
        # District list with real data stats
        districts = conn.execute("""
            SELECT d.*, 
                COUNT(DISTINCT c.id) as case_count,
                SUM(CASE WHEN c.status = 'open' THEN 1 ELSE 0 END) as open_cases,
                (SELECT COUNT(*) FROM discipline_data WHERE district_code = d.dese_code) as disc_count,
                (SELECT COUNT(*) FROM enrollment_data WHERE district_code = d.dese_code) as enroll_count,
                (SELECT COUNT(*) FROM restraint_data WHERE district_code = d.dese_code AND is_summary_row = 0) as restraint_count
            FROM districts d 
            LEFT JOIN cases c ON d.code = c.district_code AND c.status != 'archived'
            WHERE d.status = 'active'
            GROUP BY d.id 
            ORDER BY case_count DESC, d.name ASC
        """).fetchall()
        conn.close()

        head = get_head('District Profiles', 'School district profiles with DESE data, cases, and advocacy activity.')
        body = f'{head}{get_header("/districts/")}<section class="section"><div class="container">'
        body += '<div class="section-header"><span class="section-tag">Massachusetts Districts</span><h2 class="section-title">District Profiles</h2><p class="section-subtitle">Per-district pages aggregating DESE data, cases, and advocacy activity across Massachusetts districts.</p></div>'

        if not districts:
            body += '<div class="empty-state"><p>District profiles will appear here as investigations expand.</p></div>'
        else:
            body += '<div class="districts-grid">'
            for d in districts:
                badge = f'<span class="status-badge status-open">{d["open_cases"]} Active</span>' if d['open_cases'] > 0 else ''
                data_badges = ''
                if d['disc_count']:
                    data_badges += f'<span style="font-size:0.7rem;background:var(--bg-card);padding:0.15rem 0.4rem;border-radius:4px;">{d["disc_count"]} disc</span> '
                if d['restraint_count']:
                    data_badges += f'<span style="font-size:0.7rem;background:var(--bg-card);padding:0.15rem 0.4rem;border-radius:4px;">{d["restraint_count"]} restr</span>'
                body += f'''<a href="/districts/{d["code"].lower()}" class="district-card">
    <div class="district-card-header"><h3 class="district-card-name">{h(d["name"])}</h3>{badge}</div>
    <p class="district-card-location">{h(d["location"])}</p>
    <div class="district-card-stats">
        <span>{d["case_count"]} case{"s" if d["case_count"] != 1 else ""}</span>
        {data_badges}
    </div>
    <span class="district-card-link">View Full Profile &rarr;</span>
</a>'''
            body += '</div>'
        return body + '</div></section>' + get_footer()

    # === SINGLE DISTRICT WITH TABS ===
    district = conn.execute("SELECT * FROM districts WHERE code = ?", (code,)).fetchone()
    if not district:
        conn.close()
        return handle_404()

    dese_code = district['dese_code'] or code
    # Also try 4-digit code variant (some DESE datasets use truncated codes)
    dese_code_short = dese_code[:4] if dese_code and len(dese_code) >= 4 else dese_code
    dese_codes = [dese_code, dese_code_short] if dese_code_short != dese_code else [dese_code]
    
    cases = conn.execute(
        "SELECT c.* FROM cases c WHERE c.district_code = ? AND c.status != 'archived' ORDER BY c.filed_date DESC",
        (code,)
    ).fetchall()

    # Query all data types for this district (try both code variants)
    restraint_rows = []
    discipline_rows = []
    enrollment_rows = []
    attendance_rows = []
    sped_rows = []
    prs_rows = []
    
    for dc in dese_codes:
        if not restraint_rows:
            try:
                restraint_rows = conn.execute(
                    "SELECT * FROM restraint_data WHERE district_code = ? AND is_summary_row = 0 ORDER BY school_year DESC",
                    (dc,)
                ).fetchall()
            except: pass
        if not discipline_rows:
            try:
                discipline_rows = conn.execute(
                    "SELECT * FROM discipline_data WHERE district_code = ? ORDER BY school_year DESC",
                    (dc,)
                ).fetchall()
            except: pass
        if not enrollment_rows:
            try:
                enrollment_rows = conn.execute(
                    "SELECT * FROM enrollment_data WHERE district_code = ? ORDER BY school_year DESC",
                    (dc,)
                ).fetchall()
            except: pass
        if not attendance_rows:
            try:
                attendance_rows = conn.execute(
                    "SELECT * FROM attendance_data WHERE district_code = ? ORDER BY school_year DESC",
                    (dc,)
                ).fetchall()
            except: pass
        if not sped_rows:
            try:
                sped_rows = conn.execute(
                    "SELECT * FROM sped_data WHERE district_code = ? ORDER BY school_year DESC",
                    (dc,)
                ).fetchall()
            except: pass
    try:
        # Try full name, then short name variants for PRS matching
        prs_rows = conn.execute(
            "SELECT * FROM prs_intakes_data WHERE district LIKE ? OR district LIKE ? ORDER BY intake_date DESC LIMIT 50",
            (f"%{district['name']}%", f"%{district['name'].split()[0]}%")
        ).fetchall()
    except: pass

    has_data = bool(restraint_rows or discipline_rows or enrollment_rows or attendance_rows or sped_rows or prs_rows)
    conn.close()

    head = get_head(district['name'], district['description'] or f'DESE data, cases, and advocacy for {district["name"]}')
    body = f'''{head}{get_header("/districts/")}
<section class="section"><div class="container">
<div class="district-detail-header">
    <span class="section-tag">District Profile</span>
    <h1 class="section-title">{h(district["name"])}</h1>
    <p class="section-subtitle">{h(district["location"])} &middot; DESE Code: {h(dese_code)}</p>
</div>
<div class="hero-stats" style="margin-bottom:1.5rem;">
    <div class="stat"><span class="stat-value">{len(cases)}</span><span class="stat-label">Cases</span></div>
    <div class="stat"><span class="stat-value">{len(restraint_rows)}</span><span class="stat-label">Restraint Records</span></div>
    <div class="stat"><span class="stat-value">{len(discipline_rows)}</span><span class="stat-label">Discipline Records</span></div>
    <div class="stat"><span class="stat-value">{len(prs_rows)}</span><span class="stat-label">PRS Intakes</span></div>
</div>'''

    # Tab navigation
    tabs = [('overview', 'Overview', True)]
    if cases: tabs.append(('cases', 'Cases', False))
    if prs_rows: tabs.append(('prs', 'PRS Complaints', False))
    if restraint_rows: tabs.append(('restraint', 'Restraint & Seclusion', False))
    if discipline_rows: tabs.append(('discipline', 'Discipline', False))
    if enrollment_rows: tabs.append(('enrollment', 'Enrollment', False))
    if attendance_rows: tabs.append(('attendance', 'Attendance', False))
    if sped_rows: tabs.append(('sped', 'SPED Results', False))

    if len(tabs) > 1:
        body += '<div class="data-tabs" style="display:flex;gap:0;border-bottom:2px solid var(--border);margin-bottom:1.5rem;flex-wrap:wrap;">'
        for tab_id, tab_label, active in tabs:
            active_class = 'active' if active else ''
            body += f'<button class="data-tab {active_class}" data-tab="{tab_id}" style="padding:0.75rem 1.25rem;border:none;background:none;color:var(--text-muted);cursor:pointer;font-size:0.85rem;font-weight:500;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all 0.2s;">{tab_label}</button>'
        body += '</div>'

    # === TAB: Overview ===
    body += f'<div class="data-tab-content active" id="tab-overview">'
    
    if cases:
        body += '<div class="district-section"><h3 style="font-size:1.2rem;margin-bottom:0.75rem;">Active Cases</h3><div class="cases-grid">'
        for c in cases:
            body += f'''<div class="case-card">
    <div class="case-card-header"><div class="case-district">{h(c["district_code"])}, MA</div>{status_badge(c["status"])}</div>
    <div class="case-card-id">{h(c["case_id"])}</div>
    <h3 class="case-card-title">{h(c["title"])}</h3>
    <p style="font-size:0.85rem;color:var(--text-muted);">{h((c["summary"] or "")[:150])}</p>
    <a href="/cases/{h(c["case_id"])}" class="case-card-btn">View Details</a>
</div>'''
        body += '</div></div>'

    # Data summary cards
    if has_data:
        body += '<div class="resources-grid" style="margin-top:1rem;">'
        if restraint_rows:
            latest_r = restraint_rows[0]
            body += f'''<article class="resource-card">
    <h3 class="resource-title">Restraint & Seclusion</h3>
    <p class="resource-excerpt">{latest_r["school_year"]}: {latest_r["total_restraints"] or 0} restraints, {latest_r["total_injuries"] or 0} injuries across {len(restraint_rows)} school-level records.</p>
    <span class="resource-link" onclick="document.querySelector('[data-tab=restraint]').click()" style="cursor:pointer;">View Restraint Data &rarr;</span>
</article>'''
        if discipline_rows:
            latest_d = discipline_rows[0]
            body += f'''<article class="resource-card">
    <h3 class="resource-title">Discipline</h3>
    <p class="resource-excerpt">{latest_d["school_year"]}: {latest_d["students_disciplined"] or 0} students disciplined ({len(discipline_rows)} year{"" if len(discipline_rows)==1 else "s"} of data).</p>
    <span class="resource-link" onclick="document.querySelector('[data-tab=discipline]').click()" style="cursor:pointer;">View Discipline Data &rarr;</span>
</article>'''
        if enrollment_rows:
            latest_e = enrollment_rows[0]
            body += f'''<article class="resource-card">
    <h3 class="resource-title">Enrollment & Demographics</h3>
    <p class="resource-excerpt">{latest_e["school_year"]}: SPED {latest_e["sped_pct"] if "sped_pct" in latest_e.keys() else "-"}%, Low Income {latest_e["low_income_pct"] if "low_income_pct" in latest_e.keys() else "-"}%, EL {latest_e["el_pct"] if "el_pct" in latest_e.keys() else "-"}%</p>
    <span class="resource-link" onclick="document.querySelector('[data-tab=enrollment]').click()" style="cursor:pointer;">View Enrollment Data &rarr;</span>
</article>'''
        if attendance_rows:
            latest_a = attendance_rows[0]
            body += f'''<article class="resource-card">
    <h3 class="resource-title">Attendance</h3>
    <p class="resource-excerpt">{latest_a["school_year"]}: {latest_a["attendance_rate"] if "attendance_rate" in latest_a.keys() else "-"}% attendance, {latest_a["chronically_absent_10_pct"] if "chronically_absent_10_pct" in latest_a.keys() else "-"}% chronically absent.</p>
    <span class="resource-link" onclick="document.querySelector('[data-tab=attendance]').click()" style="cursor:pointer;">View Attendance Data &rarr;</span>
</article>'''
        body += '</div>'

    if not cases and not has_data:
        body += '<div class="empty-state"><p>No DESE data or cases loaded for this district yet. Data pipelines are being built - check back soon.</p></div>'
    body += '</div>'

    # === TAB: Cases ===
    if cases:
        body += f'<div class="data-tab-content" id="tab-cases" style="display:none;">'
        body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>Case ID</th><th>Type</th><th>Title</th><th>Status</th><th>Filed</th><th>Deadline</th></tr></thead><tbody>'
        for c in cases:
            body += f'<tr><td><a href="/cases/{h(c["case_id"])}" style="color:var(--accent);font-weight:600;">{h(c["case_id"])}</a></td><td>{case_type_label(c["type"])}</td><td>{h(c["title"])}</td><td>{status_badge(c["status"])}</td><td>{format_date(c["filed_date"])}</td><td>{format_date(c["deadline"])}</td></tr>'
        body += '</tbody></table></div></div>'

    # === TAB: PRS Complaints ===
    if prs_rows:
        body += f'<div class="data-tab-content" id="tab-prs" style="display:none;">'
        body += f'<p style="color:var(--text-muted);margin-bottom:0.75rem;">{len(prs_rows)} PRS complaint records matching this district (from DESE Problem Resolution System).</p>'
        body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>PRS #</th><th>District</th><th>Intake Date</th><th>Status</th><th>Category</th><th>Subcategory</th></tr></thead><tbody>'
        for r in prs_rows:
            vals = [r[k] for k in r.keys() if k != 'id']
            body += f'<tr><td><strong>{h(str(vals[0]) if len(vals)>0 else "")}</strong></td><td>{h(str(vals[1]) if len(vals)>1 else "")}</td><td>{format_date(vals[2] if len(vals)>2 else "")}</td><td>{status_badge(str(vals[3]).lower() if len(vals)>3 and vals[3] else "unknown")}</td><td>{h(str(vals[4]) if len(vals)>4 else "")}</td><td>{h(str(vals[5]) if len(vals)>5 else "")}</td></tr>'
        body += '</tbody></table></div></div>'

    # === TAB: Restraint & Seclusion ===
    if restraint_rows:
        body += f'<div class="data-tab-content" id="tab-restraint" style="display:none;">'
        body += f'<p style="color:var(--text-muted);margin-bottom:0.75rem;">{len(restraint_rows)} school-level records - DESE suppresses cells when fewer than 6 students were restrained.</p>'
        body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>Year</th><th>School</th><th>Enrollment</th><th>Students Restrained</th><th>Total Restraints</th><th>Injuries</th><th>Rate/100</th></tr></thead><tbody>'
        for r in restraint_rows:
            body += f'<tr><td>{h(r["school_year"])}</td><td><strong>{h(r["school_name"] or "-")}</strong></td><td>{r["enrollment"] or 0:,}</td><td>{h(str(r["students_restrained"] or "&lt;6"))}</td><td>{h(str(r["total_restraints"] or "-"))}</td><td>{h(str(r["total_injuries"] or "-"))}</td><td>{h(str(r["restraint_rate_per_100"] or "-"))}</td></tr>'
        body += '</tbody></table></div></div>'

    # === TAB: Discipline ===
    if discipline_rows:
        body += f'<div class="data-tab-content" id="tab-discipline" style="display:none;">'
        body += f'<p style="color:var(--text-muted);margin-bottom:0.75rem;">{len(discipline_rows)} year{"" if len(discipline_rows)==1 else "s"} of discipline data.</p>'
        body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>Year</th><th>Students</th><th>Disciplined</th><th>% In-School Susp</th><th>% Out-School Susp</th><th>% Expulsion</th><th>% Arrest</th></tr></thead><tbody>'
        for r in discipline_rows:
            body += f'<tr><td><strong>{h(r["school_year"])}</strong></td><td>{r["students"] or 0:,}</td><td>{r["students_disciplined"] or 0:,}</td><td>{h(str(r["pct_in_school_susp"] or "-"))}%</td><td>{h(str(r["pct_out_school_susp"] or "-"))}%</td><td>{h(str(r["pct_expulsion"] or "-"))}%</td><td>{h(str(r["pct_arrest"] if "pct_arrest" in r.keys() else "-"))}%</td></tr>'
        body += '</tbody></table></div></div>'

    # === TAB: Enrollment ===
    if enrollment_rows:
        body += f'<div class="data-tab-content" id="tab-enrollment" style="display:none;">'
        body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>Year</th><th>High Needs %</th><th>EL %</th><th>Low Income %</th><th>SPED %</th><th>FLNE %</th></tr></thead><tbody>'
        for r in enrollment_rows:
            body += f'<tr><td><strong>{h(r["school_year"])}</strong></td><td>{h(str(r["high_needs_pct"] if "high_needs_pct" in r.keys() else "-"))}%</td><td>{h(str(r["el_pct"] if "el_pct" in r.keys() else "-"))}%</td><td>{h(str(r["low_income_pct"] if "low_income_pct" in r.keys() else "-"))}%</td><td>{h(str(r["sped_pct"] if "sped_pct" in r.keys() else "-"))}%</td><td>{h(str(r["flne_pct"] if "flne_pct" in r.keys() else "-"))}%</td></tr>'
        body += '</tbody></table></div></div>'

    # === TAB: Attendance ===
    if attendance_rows:
        body += f'<div class="data-tab-content" id="tab-attendance" style="display:none;">'
        body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>Year</th><th>Attendance Rate</th><th>Avg Absences</th><th>% Absent 10+</th><th>% Chronically Absent</th></tr></thead><tbody>'
        for r in attendance_rows:
            body += f'<tr><td><strong>{h(r["school_year"])}</strong></td><td>{h(str(r["attendance_rate"] if "attendance_rate" in r.keys() else "-"))}%</td><td>{h(str(r["avg_absences"] if "avg_absences" in r.keys() else "-"))}</td><td>{h(str(r["absent_10_plus_pct"] if "absent_10_plus_pct" in r.keys() else "-"))}%</td><td>{h(str(r["chronically_absent_10_pct"] if "chronically_absent_10_pct" in r.keys() else "-"))}%</td></tr>'
        body += '</tbody></table></div></div>'

    # === TAB: SPED Results ===
    if sped_rows:
        body += f'<div class="data-tab-content" id="tab-sped" style="display:none;">'
        body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>Year</th><th>SPED Grad Rate</th><th>SPED Dropout Rate</th><th>Full Inclusion %</th><th>Parent Involvement %</th></tr></thead><tbody>'
        for r in sped_rows:
            body += f'<tr><td><strong>{h(r["school_year"])}</strong></td><td>{h(str(r["sped_grad_rate"] if "sped_grad_rate" in r.keys() else "-"))}%</td><td>{h(str(r["sped_dropout_rate"] if "sped_dropout_rate" in r.keys() else "-"))}%</td><td>{h(str(r["lre_full_incl_pct"] if "lre_full_incl_pct" in r.keys() else "-"))}%</td><td>{h(str(r["parent_involve_pct"] if "parent_involve_pct" in r.keys() else "-"))}%</td></tr>'
        body += '</tbody></table></div></div>'

    # Tab JS
    if len(tabs) > 1:
        body += '''<script>
document.querySelectorAll('.data-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.data-tab').forEach(t => {
            t.classList.remove('active');
            t.style.color = 'var(--text-muted)';
            t.style.borderBottomColor = 'transparent';
        });
        document.querySelectorAll('.data-tab-content').forEach(c => c.style.display = 'none');
        tab.classList.add('active');
        tab.style.color = 'var(--accent)';
        tab.style.borderBottomColor = 'var(--accent)';
        const target = document.getElementById('tab-' + tab.dataset.tab);
        if (target) target.style.display = 'block';
    });
});
// Style active tab on load
const activeTab = document.querySelector('.data-tab.active');
if (activeTab) {
    activeTab.style.color = 'var(--accent)';
    activeTab.style.borderBottomColor = 'var(--accent)';
}
</script>'''

    return body + '<div style="margin-top:2rem;"><a href="/districts/" class="btn btn-ghost">&larr; All Districts</a></div></div></section>' + get_footer()



def handle_schools(path=''):
    conn = get_db()
    code = None
    if path and path not in ('/schools/', '/schools'):
        code = path.split('/schools/', 1)[1].split('?')[0].split('/')[0].strip()

    if not code:
        # School listing — latest year per school
        schools = conn.execute("""
            SELECT r.school_name, r.school_code, r.district_name, r.district_code,
                   r.school_year, r.enrollment, r.total_restraints,
                   r.students_restrained, r.restraint_rate_per_100
            FROM restraint_data r
            INNER JOIN (
                SELECT school_code, MAX(school_year) as max_year
                FROM restraint_data
                WHERE is_summary_row = 0 AND school_name IS NOT NULL AND school_name != ''
                GROUP BY school_code
            ) latest ON r.school_code = latest.school_code AND r.school_year = latest.max_year
            WHERE r.is_summary_row = 0
            ORDER BY r.district_name ASC, r.school_name ASC
        """).fetchall()
        conn.close()

        head = get_head('School Profiles', 'Individual school restraint data from DESE, with links to district-level data.')
        body = f'{head}{get_header("/schools/")}<section class="section"><div class="container">'
        body += '<div class="section-header"><span class="section-tag">Massachusetts Schools</span><h2 class="section-title">School Profiles</h2><p class="section-subtitle">Per-school restraint and seclusion data reported to DESE. District-level enrollment, discipline, attendance, and SPED data are available on the district profile.</p></div>'

        if not schools:
            body += '<div class="empty-state"><p>School profiles will appear here as restraint data is loaded.</p></div>'
        else:
            body += '<div class="districts-grid">'
            for s in schools:
                rate_str = f'{s["restraint_rate_per_100"]:.1f}/100' if s['restraint_rate_per_100'] else '-'
                body += f'''<a href="/schools/{s["school_code"]}" class="district-card">
    <div class="district-card-header"><h3 class="district-card-name">{h(s["school_name"])}</h3></div>
    <p class="district-card-location">{h(s["district_name"])} &middot; {h(s["school_year"])}</p>
    <div class="district-card-stats">
        <span>{s["total_restraints"] or 0:,} restraints</span>
        <span>{s["students_restrained"] or 0:,} students</span>
        <span>{rate_str} rate</span>
    </div>
    <span class="district-card-link">View School Profile &rarr;</span>
</a>'''
            body += '</div>'
        return body + '</div></section>' + get_footer()

    # === SINGLE SCHOOL ===
    school_info = conn.execute(
        "SELECT school_name, district_name, district_code FROM restraint_data WHERE school_code = ? AND is_summary_row = 0 AND school_name IS NOT NULL LIMIT 1",
        (code,)
    ).fetchone()

    if not school_info:
        conn.close()
        return handle_404()

    restraint_rows = conn.execute(
        "SELECT school_year, enrollment, students_restrained, students_restrained_suppressed, total_restraints, total_restraints_suppressed, total_injuries, total_injuries_suppressed, restraint_rate_per_100, injuries_per_restraint FROM restraint_data WHERE school_code = ? AND is_summary_row = 0 ORDER BY school_year DESC",
        (code,)
    ).fetchall()
    conn.close()

    total_all = sum(r['total_restraints'] or 0 for r in restraint_rows)
    peak_rate = max((r['restraint_rate_per_100'] or 0 for r in restraint_rows), default=0)
    latest = restraint_rows[0] if restraint_rows else None

    head = get_head(school_info['school_name'], f'Restraint data for {school_info["school_name"]} ({school_info["district_name"]}), from Massachusetts DESE.')
    body = f'''{head}{get_header("/schools/")}
<section class="section"><div class="container">
<div class="district-detail-header">
    <span class="section-tag">School Profile</span>
    <h1 class="section-title">{h(school_info["school_name"])}</h1>
    <p class="section-subtitle"><a href="/districts/{school_info["district_code"].lower()}" style="color:var(--accent-glow);">{h(school_info["district_name"])}</a></p>
</div>
<div class="hero-stats" style="margin-bottom:1.5rem;">
    <div class="stat"><span class="stat-value">{latest["total_restraints"] or 0 if latest else 0:,}</span><span class="stat-label">Restraints ({latest["school_year"] if latest else "N/A"})</span></div>
    <div class="stat"><span class="stat-value">{total_all:,}</span><span class="stat-label">All-Time Restraints</span></div>
    <div class="stat"><span class="stat-value">{len(restraint_rows)}</span><span class="stat-label">Years of Data</span></div>
    <div class="stat"><span class="stat-value">{peak_rate:.1f}/100</span><span class="stat-label">Peak Rate</span></div>
</div>'''

    if restraint_rows:
        body += '''<div class="district-section">
    <h2 class="section-title" style="font-size:1.5rem;margin-bottom:1rem;">Restraint &amp; Seclusion History</h2>
    <p style="color:var(--text-muted);margin-bottom:0.75rem;font-size:0.85rem;">Data sourced from the Massachusetts DESE. DESE suppresses restraint counts when fewer than 6 students are restrained — suppressed cells show as 0 or &lt;6.</p>
    <div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>Year</th><th>Enrollment</th><th>Students Restrained</th><th>Total Restraints</th><th>Injuries</th><th>Rate/100</th></tr></thead><tbody>'''
        for r in restraint_rows:
            students = '&lt;6' if (r['students_restrained_suppressed'] or 0) else str(r['students_restrained'] or 0)
            restraints = '&lt;6' if (r['total_restraints_suppressed'] or 0) else f'{r["total_restraints"] or 0:,}'
            injuries = '&lt;6' if (r['total_injuries_suppressed'] or 0) else f'{r["total_injuries"] or 0:,}'
            rate = f'{r["restraint_rate_per_100"]:.1f}' if r['restraint_rate_per_100'] is not None else '-'
            body += f'<tr><td><strong>{h(r["school_year"])}</strong></td><td>{r["enrollment"] or 0:,}</td><td>{students}</td><td>{restraints}</td><td>{injuries}</td><td>{rate}</td></tr>'
        body += '</tbody></table></div></div>'

    body += f'''<div style="margin-top:2rem;display:flex;gap:1rem;flex-wrap:wrap;">
        <a href="/schools/" class="btn btn-ghost">&larr; All Schools</a>
        <a href="/districts/{school_info["district_code"].lower()}" class="btn btn-ghost">{h(school_info["district_name"])} District Profile &rarr;</a>
    </div>
</div></section>''' + get_footer()
    return body

def handle_updates():
    conn = get_db()
    updates = conn.execute(
        "SELECT u.*, c.case_id as case_ref FROM updates u LEFT JOIN cases c ON u.related_case_id = c.case_id ORDER BY u.created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()

    head = get_head('Updates', 'Chronological activity feed tracking case filings, document releases, determinations, and advocacy milestones.')
    body = f'{head}{get_header("/updates/")}<section class="section"><div class="container"><div class="section-header"><span class="section-tag">Activity Feed</span><h2 class="section-title">Updates</h2><p class="section-subtitle">Chronological feed of case activity, document releases, determinations, and advocacy milestones.</p></div>'

    if not updates:
        body += '<div class="empty-state"><p>Updates will appear here as cases progress.</p></div>'
    else:
        body += '<div class="updates-list">'
        for u in updates:
            case_link = f'<a href="/cases/{h(u["case_ref"] or u["related_case_id"])}" class="update-case-link">{h(u["case_ref"] or u["related_case_id"])}</a>' if u['case_ref'] or u['related_case_id'] else ''
            district_link = f'<div style="margin-top:0.35rem;"><a href="/districts/{h(u["related_district_code"].lower())}" class="related-link">District: {h(u["related_district_code"])}</a></div>' if u['related_district_code'] else ''
            body += f'''<div class="update-item">
    <div class="update-item-head"><span class="update-date">{format_date(u["event_date"] or u["created_at"])}</span>{severity_badge(u["severity"])}<span class="update-source">{"Auto-generated" if u["source"] == "auto" else "Manual"}</span>{case_link}</div>
    <h4 class="update-title">{h(u["title"])}</h4>
    {f'<p class="update-body">{h(u["body"] or "")}</p>' if u["body"] else ''}
    {district_link}
</div>'''
        body += '</div>'

    return body + '</div></section>' + get_footer()


def handle_404():
    return f'''{get_head("Page Not Found")}<body>
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
</body></html>'''


def handle_redirect(location):
    return f'<meta http-equiv="refresh" content="0;url={location}"><script>location.href="{location}"</script>'


# Admin session helpers
def get_admin_session(handler):
    cookie_str = handler.headers.get('Cookie', '')
    if not cookie_str:
        return None
    # Extract pdf_admin_session from the cookie string
    for part in cookie_str.split(';'):
        part = part.strip()
        if part.startswith('pdf_admin_session='):
            token = part.split('=', 1)[1].strip()
            conn = get_db()
            row = conn.execute(
                "SELECT u.id, u.username, u.role FROM admin_users u "
                "JOIN admin_sessions s ON u.id = s.user_id "
                "WHERE s.session_token = ? AND s.expires_at > datetime('now') AND u.status = 'active'",
                (token,)
            ).fetchone()
            conn.close()
            return row if row else None
    return None

def set_admin_cookie(handler, user_id):
    """Create a session token and return Set-Cookie header value."""
    token = secrets.token_hex(32)
    expires = (datetime.datetime.utcnow() + datetime.timedelta(hours=24)).isoformat()
    conn = get_db()
    conn.execute("INSERT INTO admin_sessions (session_token, user_id, expires_at) VALUES (?, ?, ?)",
                 (token, user_id, expires))
    conn.execute("UPDATE admin_users SET last_login_at = datetime('now'), login_count = login_count + 1 WHERE id = ?",
                 (user_id,))
    conn.commit()
    conn.close()
    return f'pdf_admin_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400'

def clear_admin_cookie():
    return 'pdf_admin_session=; Path=/; Max-Age=0'


def handle_admin_login(handler):
    """Handle GET/POST for admin login page."""
    error = ''
    if handler.command == 'POST':
        content_length = int(handler.headers.get('Content-Length', 0))
        body = urllib.parse.parse_qs(handler.rfile.read(content_length).decode('utf-8'))
        username = body.get('username', [''])[0]
        password = body.get('password', [''])[0]
        if username and password:
            conn = get_db()
            user = conn.execute("SELECT id, password_hash, status FROM admin_users WHERE username = ?", (username,)).fetchone()
            conn.close()
            if user and user['status'] == 'active':
                try:
                    if bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
                        cookie = set_admin_cookie(handler, user['id'])
                        handler.send_response(302)
                        handler.send_header('Location', '/admin/articles/')
                        handler.send_header('Set-Cookie', cookie)
                        handler.end_headers()
                        return
                except Exception:
                    pass
            error = 'Invalid username or password.'

    body = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">\n<title>Admin Login - Parent Data Force</title>\n<link rel="icon" href="/assets/images/logo.png"><link rel="stylesheet" href="/assets/css/styles.css"><link rel="stylesheet" href="/assets/css/admin.css">\n<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300..800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">\n<style>body{display:grid;place-items:center;min-height:100vh} .login-box{width:min(400px,90vw);border:1px solid var(--border);border-radius:var(--radius-lg);padding:2.5rem;background:var(--bg-elevated)}\n.login-box h1{font-size:1.3rem;margin-bottom:.3rem} .form-group{margin-bottom:1rem}\n.form-label{display:block;font-size:.85rem;color:var(--text-secondary);margin-bottom:.35rem}\n.form-input{width:100%;padding:.75rem;border:1px solid var(--border);border-radius:var(--radius-sm);background:rgba(255,255,255,.03);color:var(--text-primary)}\n.form-input:focus{outline:0;border-color:var(--accent-ember);box-shadow:0 0 0 3px rgba(255,90,31,.1)}\n.error{color:var(--danger);font-size:.85rem;margin-bottom:.8rem;padding:.5rem;background:var(--danger-bg);border-radius:var(--radius-xs);border:1px solid rgba(239,68,68,.2)}\n</style></head><body><div class="login-box"><h1>Parent Data Force</h1><p style="color:var(--accent-glow);font-size:.78rem;letter-spacing:.1em;margin-bottom:1.5rem">ADMIN PANEL</p>'
    if error:
        body += f'<div class="error">{h(error)}</div>'
    body += '<form method="post"><div class="form-group"><label class="form-label">Username</label><input type="text" name="username" class="form-input" required autofocus autocomplete="off"></div><div class="form-group"><label class="form-label">Password</label><input type="password" name="password" class="form-input" required></div><button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;">Sign In</button></form><div style="text-align:center;margin-top:1rem;"><a href="/" style="color:var(--text-muted);font-size:.82rem;">&larr; Back to site</a></div></div></body></html>'
    handler.send_response(200)
    handler.send_header('Content-Type', 'text/html; charset=utf-8')
    handler.end_headers()
    handler.wfile.write(body.encode('utf-8'))


def handle_admin_dashboard(admin_user):
    conn = get_db()
    articles_count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    published_count = conn.execute("SELECT COUNT(*) FROM articles WHERE status = 'published'").fetchone()[0]
    draft_count = conn.execute("SELECT COUNT(*) FROM articles WHERE status = 'draft'").fetchone()[0]
    cases_count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    submissions_new = conn.execute("SELECT COUNT(*) FROM submissions WHERE status = 'new'").fetchone()[0]
    conn.close()

    return f'''{admin_head('Dashboard')}<body class="admin-body">{admin_nav('/admin/', admin_user)}
<div class="admin-content"><div class="admin-header"><h1>Dashboard</h1><p class="admin-subtitle">Welcome, {h(admin_user['username'])}.</p></div>
<div class="admin-stats">
    <div class="admin-stat-card"><span class="admin-stat-value">{articles_count}</span><span class="admin-stat-label">Total Articles</span><span class="admin-stat-sub">{published_count} published, {draft_count} drafts</span></div>
    <div class="admin-stat-card"><span class="admin-stat-value">{cases_count}</span><span class="admin-stat-label">Total Cases</span></div>
    <div class="admin-stat-card"><span class="admin-stat-value">{submissions_new}</span><span class="admin-stat-label">New Submissions</span></div>
    <div class="admin-stat-card"><span class="admin-stat-value">{published_count}</span><span class="admin-stat-label">Published Articles</span></div>
</div>
<div class="admin-quick-links">
    <a href="/admin/articles/" class="btn btn-primary">Manage Articles</a>
    <a href="/admin/articles/new" class="btn btn-secondary">New Article</a>
    <a href="/" class="btn btn-ghost">View Site</a>
</div></div></body></html>'''


def admin_head(title=''):
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{h(title + ' - ' if title else '')}Admin - Parent Data Force</title>
<link rel="icon" href="/assets/images/logo.png"><link rel="stylesheet" href="/assets/css/styles.css"><link rel="stylesheet" href="/assets/css/admin.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300..800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"></head>'''


def admin_nav(active_path, admin_user):
    links = [
        ('/admin/', 'Dashboard'),
        ('/admin/articles/', 'Articles'),
    ]
    html = f'''<nav class="admin-nav"><div class="admin-nav-container">
<a href="/admin/" class="admin-logo"><span class="admin-logo-text">PDF Admin</span></a>
<ul class="admin-nav-menu">'''
    for href, label in links:
        cls = ' active' if active_path.startswith(href) else ''
        html += f'<li><a href="{href}" class="admin-nav-link{cls}">{label}</a></li>'
    html += f'<li><a href="/" class="admin-nav-link" target="_blank">View Site</a></li>'
    html += f'<li><a href="/admin/logout" class="admin-nav-link admin-nav-logout">Logout</a></li>'
    html += '</ul></div></nav>'
    return html


def handle_admin_articles(handler, admin_user, action='list', article_id=None):
    """Handle admin article management routes."""
    conn = get_db()

    # POST: save or delete
    if handler.command == 'POST' and article_id is None:
        content_length = int(handler.headers.get('Content-Length', 0))
        body = urllib.parse.parse_qs(handler.rfile.read(content_length).decode('utf-8'))
        act = body.get('action', ['save'])[0]

        if act == 'delete' and body.get('article_id'):
            aid = int(body['article_id'][0])
            conn.execute("DELETE FROM articles WHERE id = ?", (aid,))
            conn.execute("DELETE FROM article_tag_links WHERE article_id = ?", (aid,))
            conn.commit()
            conn.close()
            handler.send_response(302)
            handler.send_header('Location', '/admin/articles/')
            handler.end_headers()
            return

        if act == 'save':
            title = body.get('title', [''])[0].strip()
            slug = body.get('slug', [''])[0].strip() or slugify(title)
            excerpt = body.get('excerpt', [''])[0].strip()
            html_body = body.get('body', [''])[0]
            category = body.get('category', ['other'])[0]
            status = body.get('status', ['draft'])[0]
            featured = 1 if body.get('featured') else 0
            aid = body.get('article_id', [''])[0]
            tags_raw = body.get('tags', [''])[0].strip()

            if not title or not html_body:
                conn.close()
                handler.send_response(302)
                handler.send_header('Location', f'/admin/articles/new?error=Title+and+body+are+required')
                handler.end_headers()
                return

            # Ensure unique slug
            exist = conn.execute("SELECT id FROM articles WHERE slug = ?" + (f" AND id != ?" if aid else ""),
                                 (slug, int(aid)) if aid else (slug,)).fetchone()
            if exist:
                slug = slug + '-' + str(exist['id'] + 1)

            now = datetime.datetime.utcnow().isoformat()
            published_at = now if status == 'published' else None
            rt = read_time_est(html_body)

            if aid:
                conn.execute(
                    "UPDATE articles SET title=?, slug=?, excerpt=?, body=?, category=?, status=?, featured=?, read_time=?, published_at=COALESCE(?, published_at), updated_at=? WHERE id=?",
                    (title, slug, excerpt, html_body, category, status, featured, rt, published_at, now, int(aid)))
            else:
                conn.execute(
                    "INSERT INTO articles (title, slug, excerpt, body, category, status, featured, read_time, published_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (title, slug, excerpt, html_body, category, status, featured, rt, published_at, now, now))
                aid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            # Update tags
            conn.execute("DELETE FROM article_tag_links WHERE article_id = ?", (aid,))
            if tags_raw:
                for tag_name in tags_raw.split(','):
                    tag_name = tag_name.strip()
                    if tag_name:
                        tag_slug = slugify(tag_name)
                        conn.execute("INSERT OR IGNORE INTO article_tags (name, slug) VALUES (?, ?)", (tag_name, tag_slug))
                        tag_row = conn.execute("SELECT id FROM article_tags WHERE slug = ?", (tag_slug,)).fetchone()
                        if tag_row:
                            conn.execute("INSERT OR IGNORE INTO article_tag_links (article_id, tag_id) VALUES (?, ?)",
                                         (aid, tag_row['id']))

            conn.commit()
            conn.close()
            handler.send_response(302)
            handler.send_header('Location', '/admin/articles/')
            handler.end_headers()
            return

    # GET routes
    if action == 'new':
        return admin_article_editor(None, conn, admin_user)

    if action == 'edit' and article_id:
        article = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        if article:
            return admin_article_editor(article, conn, admin_user)
        conn.close()
        return handle_404()

    # List
    articles = conn.execute("SELECT * FROM articles ORDER BY updated_at DESC").fetchall()
    tags = conn.execute("SELECT * FROM article_tags ORDER BY name").fetchall()
    conn.close()

    stats = {'total': len(articles), 'published': sum(1 for a in articles if a['status'] == 'published'), 'draft': sum(1 for a in articles if a['status'] == 'draft')}

    body = f'''{admin_head('Articles')}<body class="admin-body">{admin_nav('/admin/articles/', admin_user)}
<div class="admin-content"><div class="admin-header">
    <h1>Articles ({stats["total"]})</h1>
    <div style="display:flex;gap:.5rem;">
        <span style="font-size:.85rem;color:var(--text-secondary);align-self:center;">{stats["published"]} published - {stats["draft"]} drafts</span>
        <a href="/admin/articles/new" class="btn btn-primary">New Article</a>
    </div>
</div>'''

    if not articles:
        body += '<div class="empty-state"><p>No articles yet. <a href="/admin/articles/new">Write your first article.</a></p></div>'
    else:
        body += '<table class="admin-table"><thead><tr><th>Title</th><th>Category</th><th>Status</th><th>Published</th><th>Tags</th><th>Actions</th></tr></thead><tbody>'
        for a in articles:
            a_tags = conn.execute(
                "SELECT t.name FROM article_tags t JOIN article_tag_links atl ON t.id = atl.tag_id WHERE atl.article_id = ?",
                (a['id'],)
            ).fetchall() if False else []
            # Re-fetch tags
            conn2 = get_db()
            a_tags = conn2.execute(
                "SELECT t.name FROM article_tags t JOIN article_tag_links atl ON t.id = atl.tag_id WHERE atl.article_id = ?",
                (a['id'],)
            ).fetchall()
            conn2.close()
            tag_html = ', '.join(h(t['name']) for t in a_tags) if a_tags else '-'

            body += f'''<tr>
    <td><a href="/admin/articles/edit/{a["id"]}" style="font-weight:600;">{h(a["title"][:80])}{"" if len(a["title"] or "")>80 else ""}</a></td>
    <td>{category_label(a["category"])}</td>
    <td>{status_badge(a["status"])}</td>
    <td>{format_date(a["published_at"])}</td>
    <td style="font-size:.78rem;color:var(--text-muted);">{tag_html}</td>
    <td>
        <a href="/admin/articles/edit/{a["id"]}" class="btn btn-ghost" style="padding:.25rem .5rem;font-size:.75rem;">Edit</a>
        <a href="/articles/{h(a["slug"])}" class="btn btn-ghost" style="padding:.25rem .5rem;font-size:.75rem;" target="_blank">View</a>
        <form method="post" style="display:inline;" onsubmit="return confirm('Delete?')">
            <input type="hidden" name="action" value="delete">
            <input type="hidden" name="article_id" value="{a["id"]}">
            <button type="submit" style="color:var(--danger);font-size:.75rem;background:0;border:0;cursor:pointer;">Del</button>
        </form>
    </td></tr>'''
        body += '</tbody></table>'

    body += '</div></body></html>'
    return body


def admin_article_editor(article, conn, admin_user):
    """Rich HTML article editor with live preview."""
    is_new = article is None
    all_tags = conn.execute("SELECT * FROM article_tags ORDER BY name").fetchall()

    # Get current article tags
    current_tags = []
    if not is_new:
        current_tags = conn.execute(
            "SELECT t.name FROM article_tags t JOIN article_tag_links atl ON t.id = atl.tag_id WHERE atl.article_id = ?",
            (article['id'],)
        ).fetchall()
    conn.close()

    title_esc = h(article['title']) if not is_new else ''
    slug_esc = h(article['slug']) if not is_new else ''
    excerpt_esc = h(article['excerpt'] or '') if not is_new else ''
    body_esc = html_mod.escape(article['body'] or '') if not is_new else ''
    category_val = article['category'] if not is_new else 'other'
    status_val = article['status'] if not is_new else 'draft'
    featured_checked = 'checked' if (not is_new and article['featured']) else ''
    current_tag_names = [t['name'] for t in current_tags]
    tags_val = h(', '.join(current_tag_names))
    article_id_field = f'<input type="hidden" name="article_id" value="{article["id"]}">' if not is_new else ''

    body = f'''{admin_head('Editor')}<body class="admin-body">{admin_nav('/admin/articles/', admin_user)}
<div class="admin-content">
<div class="admin-header"><h1>{"New Article" if is_new else "Edit Article"}</h1><a href="/admin/articles/" class="btn btn-ghost">Back to List</a></div>

<form method="post" class="admin-form" id="articleForm">
<input type="hidden" name="action" value="save">
{article_id_field}
<div class="admin-form-grid">
<div class="admin-form-main">
    <div class="form-group"><label class="form-label">Title *</label>
        <input type="text" name="title" class="form-input" value="{title_esc}" required id="titleInput" oninput="autoSlug()"></div>
    <div class="form-group"><label class="form-label">Slug</label>
        <input type="text" name="slug" class="form-input" value="{slug_esc}" id="slugInput"></div>
    <div class="form-group"><label class="form-label">Excerpt</label>
        <textarea name="excerpt" class="form-textarea" rows="2">{excerpt_esc}</textarea></div>
    <div class="form-group" style="margin-bottom:.5rem;">
        <label class="form-label">Body * (Full HTML5)</label>
        <div style="display:flex;gap:.5rem;margin-bottom:.4rem;flex-wrap:wrap;">
            <button type="button" class="btn btn-ghost" onclick="insertTag('h2')" style="font-size:.75rem;padding:.3rem .5rem;">H2</button>
            <button type="button" class="btn btn-ghost" onclick="insertTag('h3')" style="font-size:.75rem;padding:.3rem .5rem;">H3</button>
            <button type="button" class="btn btn-ghost" onclick="insertTag('p')" style="font-size:.75rem;padding:.3rem .5rem;">P</button>
            <button type="button" class="btn btn-ghost" onclick="insertTag('ul')" style="font-size:.75rem;padding:.3rem .5rem;">UL</button>
            <button type="button" class="btn btn-ghost" onclick="insertTag('blockquote')" style="font-size:.75rem;padding:.3rem .5rem;">Quote</button>
            <button type="button" class="btn btn-ghost" onclick="insertShortcode('[case id=\"\"]')" style="font-size:.75rem;padding:.3rem .5rem;">Case Card</button>
            <button type="button" class="btn btn-ghost" onclick="insertShortcode('[timeline id=\"\"]')" style="font-size:.75rem;padding:.3rem .5rem;">Timeline</button>
            <button type="button" class="btn btn-ghost" onclick="insertShortcode('[chart type=\"restraint-years\"]')" style="font-size:.75rem;padding:.3rem .5rem;">Chart</button>
            <button type="button" class="btn btn-ghost" onclick="insertShortcode('[youtube id=\"\" title=\"\"]')" style="font-size:.75rem;padding:.3rem .5rem;">YouTube</button>
            <button type="button" class="btn btn-ghost" onclick="insertLink()" style="font-size:.75rem;padding:.3rem .5rem;">Link</button>
        </div>
        <textarea name="body" class="form-textarea" rows="18" id="bodyEditor" required
            style="font-family:'JetBrains Mono',monospace;font-size:.85rem;tab-size:2;"
            oninput="updatePreview()">{body_esc}</textarea>
    </div>
</div>
<div class="admin-form-sidebar">
    <div class="admin-sidebar-box">
        <h3>Publishing</h3>
        <div class="form-group"><label class="form-label">Status</label>
            <select name="status" class="form-select">
                <option value="draft" {"selected" if status_val == "draft" else ""}>Draft</option>
                <option value="published" {"selected" if status_val == "published" else ""}>Published</option>
                <option value="archived" {"selected" if status_val == "archived" else ""}>Archived</option>
            </select></div>
        <div class="form-group"><label class="form-label">Category</label>
            <select name="category" class="form-select">
''' + ''.join(f'<option value="{c}" {"selected" if category_val == c else ""}>{category_label(c)}</option>'
             for c in ['case_update', 'methodology', 'data_analysis', 'policy', 'news', 'investigation', 'guide', 'other']) + '''
            </select></div>
        <div class="form-group"><label class="checkbox-label"><input type="checkbox" name="featured" value="1" ''' + featured_checked + '''> Featured Article</label></div>
    </div>
    <div class="admin-sidebar-box">
        <h3>Tags</h3>
        <div class="form-group"><label class="form-label">Tags (comma-separated)</label>
            <input type="text" name="tags" class="form-input" value="''' + tags_val + '''" placeholder="e.g. Public Records, DESE, Advocacy"></div>
        <p style="font-size:.75rem;color:var(--text-muted);margin-top:-.3rem;">Existing tags: ''' + ', '.join(h(t['name']) for t in all_tags[:12]) + '''</p>
    </div>
    <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;margin-bottom:1rem;">Save Article</button>
</div>
</div>
</form>

<!-- Live Preview -->
<div style="margin-top:2rem;border-top:1px solid var(--border);padding-top:1.5rem;">
    <h3 style="font-size:1.1rem;margin-bottom:.75rem;color:var(--text-secondary);">Live Preview</h3>
    <div id="articlePreview" style="border:1px solid var(--border);border-radius:var(--radius-md);padding:2rem;background:var(--bg-card);min-height:300px;" class="article-body">
        <p style="color:var(--text-muted);">Start writing to see preview...</p>
    </div>
</div>

</div>

<script>
function autoSlug(){{var t=document.getElementById('titleInput').value;document.getElementById('slugInput').value=t.toLowerCase().replace(/[^\\w\\s-]/g,'').replace(/[\\s_]+/g,'-').replace(/-+/g,'-').replace(/^-+|-+$/g,'')}}
function insertTag(tag){{var e=document.getElementById('bodyEditor');var s=e.selectionStart,v=e.value,p=0;var open='<'+tag+'>',close='</'+tag+'>';e.value=v.substring(0,s)+open+v.substring(s,v.length)+close;e.focus();e.selectionStart=e.selectionEnd=s+open.length;updatePreview()}}
function insertShortcode(text){{var e=document.getElementById('bodyEditor');var s=e.selectionStart,v=e.value;e.value=v.substring(0,s)+"\\n"+text+"\\n"+v.substring(s,v.length);e.focus();e.selectionStart=e.selectionEnd=s+text.length+2;updatePreview()}}
function insertLink(){{var url=prompt('URL:','https://');if(url){{var t=prompt('Link text:','');if(t){{var e=document.getElementById('bodyEditor');var s=e.selectionStart,v=e.value;var a='<a href="'+url+'">'+t+'</a>';e.value=v.substring(0,s)+a+v.substring(s,v.length);e.focus();updatePreview()}}}}}
function updatePreview(){{var body=document.getElementById('bodyEditor').value;if(!body.trim()){{document.getElementById('articlePreview').innerHTML='<p style="color:var(--text-muted);">Start writing to see preview...</p>';return}}
var div=document.createElement('div');div.innerHTML=body;var preview=document.getElementById('articlePreview');preview.innerHTML=div.innerHTML;
var charts=preview.querySelectorAll('[data-chart-type]');for(var i=0;i<charts.length;i++){{var c=charts[i];c.innerHTML='<canvas style="min-height:200px;border:1px dashed var(--border);border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--text-muted);"><div style="text-align:center;padding:2rem;">Chart: '+c.getAttribute('data-chart-type')+'</div></canvas>'}}}}
updatePreview();</script>
</body></html>'''
    return body


def handle_prr_tracker():
    conn = get_db()
    agency = ''
    stage = ''
    status = ''
    if '?' in '':
        pass
    # Read from actual request path
    tracker = conn.execute("SELECT * FROM prr_tracker ORDER BY request_date DESC").fetchall()
    
    # Agency + stage counts for filters
    agencies = conn.execute("SELECT DISTINCT agency FROM prr_tracker WHERE agency != '' AND agency IS NOT NULL ORDER BY agency").fetchall()
    stages = conn.execute("SELECT DISTINCT stage FROM prr_tracker WHERE stage != '' AND stage IS NOT NULL ORDER BY stage").fetchall()
    deadlines = conn.execute("SELECT DISTINCT current_deadline_status FROM prr_tracker WHERE current_deadline_status != '' AND current_deadline_status IS NOT NULL ORDER BY current_deadline_status").fetchall()
    conn.close()

    head = get_head('PRR Tracker', 'Complete audit trail of every public records request filed - agencies, stages, deadlines, and outcomes.')
    body = f'''{head}{get_header("/data/")}<section class="section"><div class="container">
<div class="section-header"><span class="section-tag">Data Tool</span><h2 class="section-title">Public Records Request Tracker</h2><p class="section-subtitle">Complete audit trail of every records request filed - agencies, stages, deadlines, responses, appeals, and outcomes. Sourced from Gmail audit records.</p></div>
<div class="data-browser-intro" style="margin-bottom:1rem;"><p><strong>{len(tracker)} active requests</strong> across {len(agencies)} agencies. Stages: '''
    for s in stages:
        body += f'<span style="display:inline-block;margin:0.2rem 0.4rem;font-size:0.8rem;color:var(--text-secondary);"> {h(s[0])}</span> '
    body += '</p></div>'

    if not tracker:
        body += '<div class="empty-state"><p>Load tracker data to populate this page.</p></div>'
    else:
        body += '<div data-table-controls data-target-table="prr-body"><div class="data-control-row"><input type="text" class="form-input" data-table-search placeholder="Filter by agency, stage, or summary..." style="max-width:400px;"><span class="datatable-count" data-table-count></span></div></div>'
        body += '<div class="repo-table-wrapper"><table class="repo-table" id="prr-body"><thead><tr><th>Request</th><th>Agency</th><th>Stage</th><th>Filed</th><th>Deadline Status</th><th>Summary</th><th>Next Action</th></tr></thead><tbody>'
        for t in tracker:
            body += f'''<tr data-search="{h(str(t['agency'] or '') + ' ' + str(t['stage'] or '') + ' ' + str(t['request_summary'] or '')).lower()}" data-agency="{h(t['agency'] or '')}" data-stage="{h(t['stage'] or '')}" data-deadline="{h(t['current_deadline_status'] or '')}">
                <td style="font-family:JetBrains Mono,monospace;font-size:0.78rem;">{h(t['request'] or '-')}</td>
                <td><strong>{h(t['agency'] or '-')}</strong></td>
                <td>{status_badge(t['stage'] or 'pending')}</td>
                <td>{format_date(t['request_date'])}</td>
                <td>{h(t['current_deadline_status'] or '-')}</td>
                <td style="max-width:300px;">{h((t['request_summary'] or '')[:150])}{'' if t['request_summary'] and len(t['request_summary']) > 150 else ''}</td>
                <td style="font-size:0.82rem;color:var(--text-secondary);">{h(str(t['next_action'] or '')[:80])}</td>
            </tr>'''
        body += '</tbody></table></div>'

    body += '</div></section>' + get_footer()
    return body


def handle_public_records():
    """Horizontal Gantt-style timeline of public records requests with deadline tracking."""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    from datetime import datetime, timedelta
    
    tracker = conn.execute("SELECT * FROM prr_tracker ORDER BY request_date DESC NULLS LAST").fetchall()
    
    # Build document registry
    docs_by_prs = {}
    for r in conn.execute("SELECT prs_number, filename, filepath, file_size, doc_type FROM prs_documents ORDER BY prs_number").fetchall():
        pnum = r['prs_number']
        if pnum not in docs_by_prs: docs_by_prs[pnum] = []
        docs_by_prs[pnum].append({'filename': r['filename'], 'size_kb': r['file_size'] // 1024, 'type': r['doc_type']})
    
    entries = []
    today = datetime.now()
    
    for t in tracker:
        deadline_status = (t['current_deadline_status'] or '').lower()
        missed = any(w in deadline_status for w in ('missed', 'overdue', 'late', 'past due'))
        
        filed_date = None
        if t['request_date']:
            try: filed_date = datetime.strptime(str(t['request_date'])[:10], '%Y-%m-%d')
            except: pass
        
        resp_date = None
        if t['initial_response_date'] and t['initial_response_date'] != 'None':
            try: resp_date = datetime.strptime(str(t['initial_response_date'])[:10], '%Y-%m-%d')
            except: pass
        
        due_date = None
        if t['initial_response_due'] and t['initial_response_due'] != 'None':
            try: due_date = datetime.strptime(str(t['initial_response_due'])[:10], '%Y-%m-%d')
            except: pass
        
        appeal_date = None
        prod_date = None
        if t['production_due'] and t['production_due'] != 'None':
            try: prod_date = datetime.strptime(str(t['production_due'])[:10], '%Y-%m-%d')
            except: pass
        
        # Calculate key metrics
        elapsed = (today - filed_date).days if filed_date else 0
        response_days = (resp_date - filed_date).days if filed_date and resp_date else None
        deadline_passed = due_date and due_date < today
        is_overdue = missed or (deadline_passed and not resp_date)
        
        # Find related documents
        related_docs = []
        request_text = (t['request'] or '') + ' ' + (t['request_summary'] or '')
        for pnum, docs in docs_by_prs.items():
            if pnum.lower() in request_text.lower() or pnum.replace('-','').lower() in request_text.lower():
                related_docs.extend(docs)
        
        entries.append({
            'filed_date': filed_date, 'resp_date': resp_date, 'due_date': due_date,
            'elapsed': elapsed, 'response_days': response_days, 'is_overdue': is_overdue,
            'title': t['request'] or 'Records Request',
            'agency': t['agency'] or '', 'stage': t['stage'] or '',
            'summary': t['request_summary'] or '',
            'responsive': t['responsive_records'] or '',
            'missing_gaps': t['missing_gaps'] or '',
            'scope': t['record_category_scope'] or '',
            'appeal': t['appeal_determination'] or '',
            'next_action': t['next_action'] or '',
            'deadline_basis': t['deadline_basis'] or '',
            'timeliness': t['initial_response_timeliness'] or '',
            'withheld': t['withheld_exemptions_fee'] or '',
            'documents': related_docs,
            'request_id': t['request'] or '',
        })
    
    entries.sort(key=lambda x: x['filed_date'] or datetime(2000,1,1), reverse=True)
    missed_count = sum(1 for e in entries if e['is_overdue'])
    conn.close()
    
    # Find max elapsed for proportional scaling
    max_elapsed = max((e['elapsed'] for e in entries if e['elapsed'] > 0), default=365)
    
    # Compute aggregate stats for display
    responded = sum(1 for e in entries if e['resp_date'])
    appealed = sum(1 for e in entries if e.get('appeal'))
    with_docs = sum(1 for e in entries if e['documents'])
    avg_elapsed = sum(e['elapsed'] for e in entries) // max(len(entries), 1)
    worst = max((e for e in entries if e['is_overdue']), key=lambda e: e['elapsed'], default=None)
    
    head_body = f'''{get_head("Records Timeline", "Public records requests with Gantt-style deadline tracking.")}{get_header("/data/")}
<style>
.pr-gantt-row {{ display:flex; align-items:stretch; gap:0; margin-bottom:0.6rem; border-radius:8px; overflow:hidden; border:1px solid var(--border); background:var(--bg-card); cursor:pointer; transition:border-color 0.15s; }}
.pr-gantt-row:hover {{ border-color:var(--accent); }}
.pr-gantt-row.overdue {{ border-left:3px solid #ef4444; }}
.pr-gantt-left {{ flex:0 0 280px; padding:0.8rem 1rem; display:flex; flex-direction:column; justify-content:center; border-right:1px solid var(--border); min-width:0; }}
.pr-gantt-left h4 {{ font-size:0.85rem; margin:0 0 0.2rem; line-height:1.3; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.pr-gantt-left .agency {{ font-size:0.7rem; color:var(--text-muted); }}
.pr-gantt-left .date {{ font-size:0.68rem; color:var(--accent); margin-top:0.15rem; }}
.pr-gantt-bar-wrap {{ flex:1; padding:0.8rem 0.5rem; display:flex; align-items:center; position:relative; min-width:0; }}
.pr-gantt-track {{ position:relative; width:100%; height:20px; background:rgba(255,255,255,0.03); border-radius:10px; overflow:visible; }}
.pr-gantt-segment {{ position:absolute; top:0; height:100%; border-radius:10px; transition:opacity 0.2s; }}
.pr-gantt-segment.wait {{ background:rgba(255,255,255,0.04); left:0; }}
.pr-gantt-segment.resp-ontime {{ background:linear-gradient(90deg,rgba(34,197,94,0.25),rgba(34,197,94,0.1)); }}
.pr-gantt-segment.resp-late {{ background:linear-gradient(90deg,rgba(239,68,68,0.2),rgba(239,68,68,0.08)); }}
.pr-gantt-segment.resp-none {{ background:linear-gradient(90deg,rgba(239,68,68,0.35),rgba(239,68,68,0.15)); }}
.pr-gantt-segment.prod {{ background:linear-gradient(90deg,rgba(34,197,94,0.18),rgba(34,197,94,0.06)); }}
.pr-gantt-segment.pending {{ background:linear-gradient(90deg,rgba(249,115,22,0.18),rgba(249,115,22,0.06)); }}
.pr-gantt-row:hover .pr-gantt-segment {{ filter:brightness(1.3); }}
.pr-gantt-deadline {{ position:absolute; top:-6px; width:2px; height:32px; background:#ef4444; z-index:3; opacity:0.8; }}
.pr-gantt-deadline::before {{ content:'10-DAY DEADLINE'; position:absolute; top:-18px; left:50%; transform:translateX(-50%); font-size:0.52rem; color:#ef4444; font-weight:700; white-space:nowrap; background:var(--bg-card); padding:0 4px; }}
.pr-gantt-right {{ flex:0 0 110px; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:0.5rem; border-left:1px solid var(--border); gap:0.15rem; }}
.pr-gantt-days {{ font-size:1.3rem; font-weight:800; line-height:1; }}
.pr-gantt-days.over {{ color:#ef4444; }}
.pr-gantt-days.ok {{ color:#22c55e; }}
.pr-gantt-days.neutral {{ color:var(--text-muted); }}
.pr-gantt-label {{ font-size:0.58rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; text-align:center; }}
/* Status badges in left panel */
.pr-badges {{ display:flex; gap:0.25rem; flex-wrap:wrap; margin-top:0.3rem; }}
.pr-badge {{ font-size:0.6rem; padding:0.1rem 0.4rem; border-radius:3px; font-weight:600; letter-spacing:0.03em; }}
.pr-badge.overdue {{ background:rgba(239,68,68,0.15); color:#ef4444; }}
.pr-badge.responded {{ background:rgba(34,197,94,0.12); color:#22c55e; }}
.pr-badge.appealed {{ background:rgba(139,92,246,0.12); color:#a78bfa; }}
.pr-badge.produced {{ background:rgba(59,130,246,0.12); color:#60a5fa; }}
.pr-badge.pending {{ background:rgba(249,115,22,0.12); color:#f97316; }}
/* Legend */
.pr-legend {{ display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1rem; font-size:0.7rem; color:var(--text-muted); align-items:center; }}
.pr-legend-item {{ display:flex; align-items:center; gap:0.3rem; }}
.pr-legend-swatch {{ width:14px; height:8px; border-radius:4px; flex-shrink:0; }}
/* Expand panel */
.pr-expand {{ display:none; padding:1rem 1.5rem; border-top:1px solid var(--border); background:rgba(0,0,0,0.08); }}
.pr-expand.open {{ display:block; }}
.pr-expand-grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:0.8rem; }}
.pr-expand-section {{ }}
.pr-expand-section h5 {{ font-size:0.72rem; color:var(--text-muted); margin:0 0 0.25rem; text-transform:uppercase; letter-spacing:0.06em; display:flex; align-items:center; gap:0.3rem; }}
.pr-expand-section h5 .ico {{ font-size:0.85rem; }}
.pr-expand-section p {{ font-size:0.78rem; color:var(--text-secondary); margin:0; line-height:1.45; }}
.pr-expand-section.full {{ grid-column:1/-1; }}
@media(max-width:768px){{ .pr-expand-grid{{grid-template-columns:1fr;}} }}
.pr-doc-inline {{ display:inline-flex; align-items:center; gap:0.3rem; font-size:0.68rem; padding:0.1rem 0.5rem; border-radius:3px; background:rgba(139,92,246,0.1); color:#a78bfa; margin:0.15rem; cursor:pointer; }}
.pr-doc-inline:hover {{ background:rgba(139,92,246,0.2); }}
/* Summary row */
.pr-summary-row {{ display:flex; gap:1rem; flex-wrap:wrap; padding:0.75rem 1rem; margin-bottom:1rem; background:rgba(249,115,22,0.05); border:1px solid rgba(249,115,22,0.12); border-radius:8px; font-size:0.75rem; color:var(--text-secondary); }}
.pr-summary-row strong {{ color:var(--accent); }}
@media(max-width:768px){{ .pr-gantt-row{{flex-direction:column;}} .pr-gantt-left{{flex:0 0 auto;border-right:none;border-bottom:1px solid var(--border);}} .pr-gantt-right{{flex:0 0 auto;border-left:none;border-top:1px solid var(--border);flex-direction:row;gap:0.5rem;}} }}
</style>
<section class="section"><div class="container">
<div class="section-header"><span class="section-tag">Records & Appeals</span><h2 class="section-title">Public Records Requests</h2><p class="section-subtitle">Timeline bars show the journey from filing to today. Red vertical line = 10-business-day legal deadline. Hover for dates. Click to expand details.</p></div>
<div class="hero-stats" style="margin-bottom:1rem;">
    <div class="stat"><span class="stat-value">{len(entries)}</span><span class="stat-label">Requests Filed</span></div>
    <div class="stat"><span class="stat-value">{responded}</span><span class="stat-label">Responded</span></div>
    <div class="stat"><span class="stat-value">{appealed}</span><span class="stat-label">Appealed</span></div>
    <div class="stat"><span class="stat-value" style="color:#ef4444;">{missed_count}</span><span class="stat-label">Overdue</span></div>
    <div class="stat"><span class="stat-value">{avg_elapsed}d</span><span class="stat-label">Avg Age</span></div>
</div>
<div class="pr-legend">
    <span style="font-weight:600;">Bar colors:</span>
    <div class="pr-legend-item"><div class="pr-legend-swatch" style="background:linear-gradient(90deg,rgba(34,197,94,0.6),rgba(34,197,94,0.2));"></div> On-time</div>
    <div class="pr-legend-item"><div class="pr-legend-swatch" style="background:linear-gradient(90deg,rgba(239,68,68,0.5),rgba(239,68,68,0.2));"></div> Late</div>
    <div class="pr-legend-item"><div class="pr-legend-swatch" style="background:linear-gradient(90deg,rgba(239,68,68,0.7),rgba(239,68,68,0.3));"></div> Overdue</div>
    <div class="pr-legend-item"><div class="pr-legend-swatch" style="background:linear-gradient(90deg,rgba(249,115,22,0.4),rgba(249,115,22,0.1));"></div> Pending</div>
    <div class="pr-legend-item" style="margin-left:0.5rem;"><span style="color:#ef4444;font-weight:700;">&#9474;</span> 10-day deadline</div>
</div>
'''
    head_body += (f'<div class="pr-summary-row"><strong>Worst offender:</strong> {h(worst["title"][:60])} - {worst["elapsed"]}d, {h(worst["agency"])} | <strong>{missed_count} of {len(entries)}</strong> overdue | <strong>{with_docs} requests</strong> have documents</div>' if worst else '')

    if not entries:
        head_body += '<div class="empty-state"><p>No records data loaded yet.</p></div>'
    else:
        for entry in entries:
            overdue_class = 'overdue' if entry['is_overdue'] else ''
            days_color = 'over' if entry['is_overdue'] else ('ok' if entry['resp_date'] else '')
            days_label = f"{entry['elapsed']}d"
            
            # Build Gantt bar segments
            fd = entry['filed_date']
            if not fd:
                bar_html = '<div class="pr-gantt-segment wait" style="left:0;width:100%;"></div>'
            else:
                total_days = max(entry['elapsed'], 1)
                
                # Calculate positions as percentages
                resp_start_pct = 0
                resp_end_pct = 0
                if entry['resp_date']:
                    resp_start_pct = 0
                    resp_end_pct = min(100, (entry['response_days'] or 0) / total_days * 100)
                elif entry['is_overdue']:
                    resp_end_pct = 100  # Still waiting, entire bar shows overdue
                else:
                    resp_end_pct = min(100, entry['elapsed'] / total_days * 100)
                
                bar_html = ''
                
                # Response phase bar
                if entry['resp_date']:
                    timeliness = entry.get('timeliness','').lower()
                    resp_class = 'resp-ontime' if 'on time' in timeliness else 'resp-late'
                    bar_html += f'<div class="pr-gantt-segment {resp_class}" style="left:{resp_start_pct}%;width:{resp_end_pct}%;" title="Response: {fd.strftime("%m/%d/%Y") if fd else ""} to {entry["resp_date"].strftime("%m/%d/%Y") if entry["resp_date"] else "pending"} ({entry.get("timeliness","")})"></div>'
                elif entry['is_overdue']:
                    bar_html += f'<div class="pr-gantt-segment resp-none" style="left:0%;width:{resp_end_pct}%;" title="No response — overdue since {entry["due_date"].strftime("%m/%d/%Y") if entry["due_date"] else "?"}"></div>'
                else:
                    bar_html += f'<div class="pr-gantt-segment wait" style="left:0%;width:{resp_end_pct}%;" title="Awaiting response — due {entry["due_date"].strftime("%m/%d/%Y") if entry["due_date"] else "?"}"></div>'
                
                # Production phase (after response)
                if entry['resp_date'] and entry['responsive']:
                    prod_start = resp_end_pct
                    prod_end = min(100, prod_start + max(5, 30 / total_days * 100))
                    bar_html += f'<div class="pr-gantt-segment prod" style="left:{prod_start}%;width:{prod_end - prod_start}%;" title="Production phase"></div>'
                
                # Pending remainder
                if resp_end_pct < 100:
                    bar_html += f'<div class="pr-gantt-segment pending" style="left:{resp_end_pct}%;width:{100 - resp_end_pct}%;" title="Pending"></div>'
                
                # Deadline marker
                if entry['due_date']:
                    dl = entry['due_date']
                    dl_days = (dl - fd).days if fd else 10
                    dl_pct = min(98, dl_days / total_days * 100) if total_days > 0 else 5
                    bar_html += f'<div class="pr-gantt-deadline" style="left:{dl_pct}%;" title="10-day legal deadline: {dl.strftime("%m/%d/%Y")}"></div>'
            
            # Documents mini-indicator
            doc_badges = ''
            if entry['documents']:
                stage_docs = {'request':0,'response':0,'appeal':0,'outcome':0}
                for d in entry['documents']:
                    m = {'prs_document':'request','intake':'request','local_response':'response','letter_of_finding':'response','spr_appeal':'appeal','closure':'outcome'}
                    s = m.get(d['type'],'outcome')
                    stage_docs[s] = stage_docs.get(s,0) + 1
                for s, c in stage_docs.items():
                    if c: doc_badges += f'<span class="pr-doc-inline">{c} {s}</span>'
            
            # Status badges for left panel
            badges_html = '<div class="pr-badges">'
            if entry['is_overdue']:
                badges_html += '<span class="pr-badge overdue">OVERDUE</span>'
            if entry['resp_date']:
                timeliness = entry.get('timeliness','').lower()
                cls = 'responded' if 'on time' in timeliness else 'overdue'
                label = 'On Time' if 'on time' in timeliness else 'Late Response'
                badges_html += f'<span class="pr-badge {cls}">{label}</span>'
            if entry['appeal']:
                badges_html += '<span class="pr-badge appealed">Appealed</span>'
            if entry['responsive']:
                badges_html += '<span class="pr-badge produced">Produced</span>'
            if not entry['resp_date'] and not entry['is_overdue']:
                badges_html += '<span class="pr-badge pending">Awaiting</span>'
            badges_html += '</div>'
            
            # Appealed?
            appeal_badge = ''
            if entry['appeal']:
                spr = entry['appeal'][:15]
                appeal_badge = f' <span style="font-size:0.65rem;background:rgba(139,92,246,0.2);color:#a78bfa;padding:0.1rem 0.3rem;border-radius:3px;">{h(spr)}</span>'
            
            head_body += f'''<div class="pr-gantt-row {overdue_class}" onclick="var e=this.nextElementSibling;e.classList.toggle('open');">
    <div class="pr-gantt-left">
        <h4 title="{h(entry['title'])}">{h(entry['title'][:60])}</h4>
        <span class="agency">{h(entry['agency'])}</span>
        <span class="date">{entry['filed_date'].strftime('%b %d, %Y') if entry['filed_date'] else ''}{appeal_badge}</span>
        {badges_html}
    </div>
    <div class="pr-gantt-bar-wrap">
        <div class="pr-gantt-track">{bar_html}</div>
    </div>
    <div class="pr-gantt-right">
        <span class="pr-gantt-days {days_color}">{days_label}</span>
        <span class="pr-gantt-label">{'OVERDUE' if entry['is_overdue'] else ('RESPONDED' if entry['resp_date'] else 'PENDING')}</span>
    </div>
</div>
<div class="pr-expand">
    <div class="pr-expand-grid">
        {f'<div class="pr-expand-section"><h5><span class="ico">&#128196;</span> Summary</h5><p>{h(entry["summary"][:300])}</p></div>' if entry['summary'] else ''}
        {f'<div class="pr-expand-section"><h5><span class="ico">&#128269;</span> Scope</h5><p>{h(entry["scope"][:250])}</p></div>' if entry['scope'] else ''}
        {f'<div class="pr-expand-section"><h5><span class="ico">&#128230;</span> Responsive Records</h5><p style="color:#22c55e;">{h(entry["responsive"][:300])}</p></div>' if entry['responsive'] else ''}
        {f'<div class="pr-expand-section"><h5><span class="ico">&#9888;</span> Missing / Gaps</h5><p style="color:#ef4444;">{h(entry["missing_gaps"][:250])}</p></div>' if entry['missing_gaps'] else ''}
        {f'<div class="pr-expand-section"><h5><span class="ico">&#128274;</span> Withheld</h5><p style="color:#f59e0b;">{h(entry["withheld"][:200])}</p></div>' if entry.get('withheld') else ''}
        {f'<div class="pr-expand-section full"><h5><span class="ico">&#8505;</span> Deadline Basis</h5><p>{h(entry.get("deadline_basis","")[:250])}</p></div>' if entry.get('deadline_basis') else ''}
        {f'<div class="pr-expand-section"><h5><span class="ico">&#10132;</span> Next Action</h5><p style="color:var(--accent);">{h(entry["next_action"])}</p></div>' if entry['next_action'] else ''}
    </div>
    {f'<div style="margin-top:0.6rem;display:flex;flex-wrap:wrap;gap:0.3rem;">{doc_badges}</div>' if doc_badges else ''}
</div>'''
    
    return head_body + '<div style="margin-top:1.5rem;"><a href="/data/" class="btn btn-ghost">&larr; Data Hub</a></div></div></section>' + get_footer()


def handle_request_catalog():
    conn = get_db()
    catalog = conn.execute("SELECT * FROM aggregate_catalog ORDER BY id").fetchall()
    conn.close()

    head = get_head('Request Catalog', 'Pattern library of public records request types - categories, lanes, evidence, and SPR outcomes.')
    body = f'''{head}{get_header("/data/")}<section class="section"><div class="container">
<div class="section-header"><span class="section-tag">Data Tool</span><h2 class="section-title">Aggregate Request Catalog</h2><p class="section-subtitle">Pattern library mapping record categories to public records lanes, SPR determinations, and evidence notes. Use this to identify what records are obtainable and how.</p></div>'''

    if not catalog:
        body += '<div class="empty-state"><p>Load catalog data to populate this page.</p></div>'
    else:
        body += '<div class="data-browser-intro"><p><strong>{len(catalog)} record categories</strong> cataloged - each entry maps a category of records to the legal lane, source type, and SPR outcome.</p></div>'
        for c in catalog:
            confidence_color = 'status-open' if c['confidence'] == 'High' else 'status-pending'
            body += f'''<div class="catalog-card" style="border:1px solid var(--border);border-radius:var(--radius-md);padding:1.2rem;margin-bottom:1rem;background:var(--bg-card);">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.5rem;">
        <h3 style="font-size:1.1rem;">{h(c['cat_id'] or '')}: {h(c['category'] or '')}</h3>
        <span class="status-badge {confidence_color}">{h(c['confidence'] or '')}</span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.5rem;margin-bottom:0.8rem;font-size:0.85rem;color:var(--text-secondary);">
        <div><strong>Lane:</strong> {h(c['lane'] or '')}</div>
        <div><strong>Source Type:</strong> {h(c['source_type'] or '')}</div>
        <div><strong>Source:</strong> <code style="font-size:0.8rem;">{h(c['source_ref'] or '')}</code></div>
    </div>
    <p style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:0.4rem;"><strong>Evidence:</strong> {h(str(c['evidence_note'] or '')[:300])}</p>
    <p style="font-size:0.85rem;color:var(--text-muted);"><strong>Scope:</strong> {h(str(c['scope_seen'] or '')[:200])}</p>
    <p style="font-size:0.85rem;color:var(--accent-glow);margin-top:0.4rem;"><strong>Result:</strong> {h(str(c['result_use'] or '')[:250])}</p>
</div>'''

    body += '</div></section>' + get_footer()
    return body


# 
# Shared filter/sort/pagination for data pages
# 

def data_filter_bar(page_url, search_placeholder='Search...', extra_filters='', show_per_page=True, show_search=True):
    """Returns HTML for a reusable filter bar with search, sort, and per-page."""
    import urllib.parse as up
    qs = {}
    if '?' in _current_path:
        qs = dict(up.parse_qsl(_current_path.split('?',1)[1]))
    
    search = qs.get('search', '').strip()
    sort_by = qs.get('sort', '')
    per_page = qs.get('per_page', '50')
    
    bar = f'<form method="get" action="{page_url}" style="margin-bottom:1rem;"><div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:flex-end;">'
    
    if show_search:
        bar += f'''<div style="flex:2;min-width:180px;">
    <label style="font-size:0.75rem;color:var(--text-muted);display:block;">Search</label>
    <input type="text" name="search" value="{h(search)}" placeholder="{search_placeholder}" 
        style="width:100%;padding:0.5rem 0.75rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.85rem;">
</div>'''
    
    bar += extra_filters
    
    # Sort
    bar += f'''<div style="flex:1;min-width:100px;">
    <label style="font-size:0.75rem;color:var(--text-muted);display:block;">Sort By</label>
    <select name="sort" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;">
        <option value="">Default</option>'''
    bar += f'</select></div>'
    
    if show_per_page:
        bar += f'''<div style="flex:1;min-width:80px;">
    <label style="font-size:0.75rem;color:var(--text-muted);display:block;">Per Page</label>
    <select name="per_page" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;">'''
        for pp in [25, 50, 100, 200]:
            sel = 'selected' if per_page == str(pp) else ''
            bar += f'<option value="{pp}" {sel}>{pp}</option>'
        bar += '</select></div>'
    
    bar += '<div style="flex:0;min-width:70px;display:flex;align-items:flex-end;"><button type="submit" class="btn btn-primary" style="padding:0.5rem 1rem;font-size:0.85rem;">Apply</button></div>'
    bar += '</div></form>'
    return bar


def pagination_links(page_url, page, total_pages, qs_dict, per_page_val=50):
    """Returns HTML pagination bar."""
    import urllib.parse as up
    if total_pages <= 1:
        return ''
    
    def plink(p):
        params = dict(qs_dict)
        params['page'] = str(p)
        params['per_page'] = str(params.get('per_page', per_page_val))
        return page_url + '?' + up.urlencode(params)
    
    html = '<div style="display:flex;gap:0.5rem;justify-content:center;margin-top:1.5rem;flex-wrap:wrap;">'
    if page > 1:
        html += f'<a href="{plink(1)}" class="btn btn-ghost" style="padding:0.4rem 0.8rem;font-size:0.8rem;">&laquo; First</a>'
    for p in range(max(1, page-2), min(total_pages+1, page+3)):
        cls = 'btn-primary' if p == page else 'btn-ghost'
        html += f'<a href="{plink(p)}" class="btn {cls}" style="padding:0.4rem 0.8rem;font-size:0.8rem;">{p}</a>'
    if page < total_pages:
        html += f'<a href="{plink(total_pages)}" class="btn btn-ghost" style="padding:0.4rem 0.8rem;font-size:0.8rem;">Last &raquo;</a>'
    html += '</div>'
    return html


def handle_discipline():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    
    try:
        years = [r[0] for r in conn.execute("SELECT DISTINCT school_year FROM discipline_data ORDER BY school_year DESC").fetchall()]
        districts = conn.execute("SELECT DISTINCT district_name, district_code FROM discipline_data ORDER BY district_name").fetchall()
    except:
        conn.close()
        return f'{get_head("Discipline Data")}{get_header("/data/")}<section class="section"><div class="container"><h2>Discipline Data</h2><p style="color:var(--text-muted);">Not loaded.</p></div></section>{get_footer()}'
    
    import urllib.parse as up
    qs = {}
    if '?' in _current_path:
        qs = dict(up.parse_qsl(_current_path.split('?',1)[1]))
    
    search = qs.get('search', '').strip()
    sort_by = qs.get('sort', 'school_year_desc')
    page = max(1, int(qs.get('page', '1')))
    per_page = min(200, max(10, int(qs.get('per_page', '50'))))
    year_filter = qs.get('year', '').strip()
    district_filter = qs.get('district', '').strip()
    
    # Build WHERE
    where = []
    params = []
    if search:
        where.append("(district_name LIKE ? OR district_code LIKE ?)")
        params.extend([f'%{search}%', f'%{search}%'])
    if year_filter:
        where.append("school_year = ?")
        params.append(year_filter)
    if district_filter:
        where.append("district_code = ?")
        params.append(district_filter)
    
    where_clause = ' WHERE ' + ' AND '.join(where) if where else ''
    total = conn.execute(f'SELECT COUNT(*) FROM discipline_data{where_clause}', params).fetchone()[0]
    
    sort_map = {
        'school_year_desc': 'school_year DESC', 'school_year_asc': 'school_year ASC',
        'district_asc': 'district_name ASC', 'district_desc': 'district_name DESC',
        'students_desc': 'students DESC', 'students_asc': 'students ASC',
        'disciplined_desc': 'students_disciplined DESC', 'disciplined_asc': 'students_disciplined ASC',
        'inschool_desc': 'pct_in_school_susp DESC', 'outschool_desc': 'pct_out_school_susp DESC',
        'expulsion_desc': 'pct_expulsion DESC', 'arrest_desc': 'pct_arrest DESC',
    }
    order = sort_map.get(sort_by, 'school_year DESC, district_name')
    
    offset = (page - 1) * per_page
    total_pages = max(1, (total + per_page - 1) // per_page)
    
    rows = conn.execute(f'SELECT * FROM discipline_data{where_clause} ORDER BY {order} LIMIT ? OFFSET ?', params + [per_page, offset]).fetchall()
    conn.close()
    
    # Build page
    extra_filters = f'''<div style="flex:1;min-width:120px;">
    <label style="font-size:0.75rem;color:var(--text-muted);display:block;">Year</label>
    <select name="year" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;">
        <option value="">All Years</option>'''
    for y in years:
        sel = 'selected' if y == year_filter else ''
        extra_filters += f'<option value="{h(y)}" {sel}>{h(y)}</option>'
    extra_filters += '</select></div>'
    
    extra_filters += '''<div style="flex:1;min-width:160px;">
    <label style="font-size:0.75rem;color:var(--text-muted);display:block;">District</label>
    <select name="district" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;">
        <option value="">All Districts</option>'''
    for d in districts:
        sel = 'selected' if d[1] == district_filter else ''
        extra_filters += f'<option value="{h(d[1])}" {sel}>{h(d[0])} ({h(d[1])})</option>'
    extra_filters += '</select></div>'
    
    # Sort options
    sort_opts_html = '''<option value="school_year_desc">Year (Newest)</option><option value="school_year_asc">Year (Oldest)</option>
        <option value="district_asc">District (A-Z)</option><option value="district_desc">District (Z-A)</option>
        <option value="students_desc">Students (High)</option><option value="disciplined_desc">Disciplined (High)</option>
        <option value="inschool_desc">In-School Susp % (High)</option><option value="outschool_desc">Out-School Susp % (High)</option>
        <option value="expulsion_desc">Expulsion % (High)</option><option value="arrest_desc">Arrest % (High)</option>'''
    
    filter_bar = data_filter_bar('/data/discipline/', 'District name or code...', extra_filters).replace('<option value="">Default</option>', f'<option value="">Default</option>{sort_opts_html}')
    
    # Set selected sort
    filter_bar = filter_bar.replace(f'value="{sort_by}"', f'value="{sort_by}" selected')
    
    head_body = f'{get_head("Discipline Data", "District-level discipline: suspensions, expulsions, arrests, law enforcement referrals.")}{get_header("/data/")}<section class="section"><div class="container">'
    head_body += f'<div class="hero-stats" style="margin-bottom:1rem;"><div class="stat"><span class="stat-value">{total:,}</span><span class="stat-label">Records</span></div><div class="stat"><span class="stat-value">{len(years)}</span><span class="stat-label">Years</span></div><div class="stat"><span class="stat-value">{len(districts)}</span><span class="stat-label">Districts</span></div><div class="stat"><span class="stat-value">{total_pages}</span><span class="stat-label">Pages</span></div></div>'
    head_body += '<h2 style="font-size:1.5rem;margin-bottom:0.75rem;">Discipline Data Explorer</h2>'
    head_body += '<p style="color:var(--text-muted);margin-bottom:1rem;">Every metric sortable - click sort dropdown. Sourced from DESE.</p>'
    head_body += filter_bar
    
    if not rows:
        head_body += '<div class="empty-state"><p>No records match.</p></div>'
    else:
        head_body += f'<p style="color:var(--text-muted);font-size:0.8rem;">{offset+1}-{min(offset+per_page,total)} of {total:,}</p>'
        head_body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>District</th><th>Year</th><th>Students</th><th>Disciplined</th><th>% In-School</th><th>% Out-School</th><th>% Expulsion</th><th>% Arrest</th><th>% Emerg</th><th>% Alt</th></tr></thead><tbody>'
        for r in rows:
            head_body += f'<tr><td><strong>{h(r["district_name"])}</strong></td><td>{h(r["school_year"])}</td><td>{r["students"] or 0:,}</td><td>{r["students_disciplined"] or 0:,}</td><td>{h(str(r["pct_in_school_susp"] or "-"))}%</td><td>{h(str(r["pct_out_school_susp"] or "-"))}%</td><td>{h(str(r["pct_expulsion"] or "-"))}%</td><td>{h(str(r["pct_arrest"] if "pct_arrest" in r.keys() else "-"))}%</td><td>{h(str(r["pct_emergency_removal"] if "pct_emergency_removal" in r.keys() else "-"))}%</td><td>{h(str(r["pct_alt_setting"] if "pct_alt_setting" in r.keys() else "-"))}%</td></tr>'
        head_body += '</tbody></table></div>'
        head_body += pagination_links('/data/discipline/', page, total_pages, qs)
    
    return head_body + '<div style="margin-top:1rem;"><a href="/data/" class="btn btn-ghost">&larr; Data Hub</a></div></div></section>' + get_footer()


def handle_enrollment():
    conn = get_db(); conn.row_factory = sqlite3.Row
    try:
        years = [r[0] for r in conn.execute("SELECT DISTINCT school_year FROM enrollment_data ORDER BY school_year DESC").fetchall()]
        districts = conn.execute("SELECT DISTINCT district_name, district_code FROM enrollment_data ORDER BY district_name").fetchall()
    except:
        conn.close()
        return f'{get_head("Enrollment Data")}{get_header("/data/")}<section class="section"><div class="container"><h2>Enrollment Data</h2><p style="color:var(--text-muted);">Not loaded.</p></div></section>{get_footer()}'
    
    import urllib.parse as up
    qs = {}; 
    if '?' in _current_path: qs = dict(up.parse_qsl(_current_path.split('?',1)[1]))
    search = qs.get('search','').strip(); sort_by = qs.get('sort','school_year_desc')
    page = max(1,int(qs.get('page','1'))); per_page = min(200,max(10,int(qs.get('per_page','50'))))
    year_filter = qs.get('year','').strip(); district_filter = qs.get('district','').strip()
    
    where = []; params = []
    if search: where.append("(district_name LIKE ? OR district_code LIKE ?)"); params.extend([f'%{search}%',f'%{search}%'])
    if year_filter: where.append("school_year = ?"); params.append(year_filter)
    if district_filter: where.append("district_code = ?"); params.append(district_filter)
    where_clause = ' WHERE ' + ' AND '.join(where) if where else ''
    total = conn.execute(f'SELECT COUNT(*) FROM enrollment_data{where_clause}', params).fetchone()[0]
    
    sort_map = {'school_year_desc':'school_year DESC','school_year_asc':'school_year ASC','district_asc':'district_name ASC',
        'sped_desc':'sped_pct DESC','lowincome_desc':'low_income_pct DESC','el_desc':'el_pct DESC',
        'highneeds_desc':'high_needs_pct DESC','flne_desc':'flne_pct DESC'}
    order = sort_map.get(sort_by, 'school_year DESC, district_name')
    offset = (page-1)*per_page; total_pages = max(1,(total+per_page-1)//per_page)
    rows = conn.execute(f'SELECT * FROM enrollment_data{where_clause} ORDER BY {order} LIMIT ? OFFSET ?', params+[per_page,offset]).fetchall()
    conn.close()
    
    extra = f'''<div style="flex:1;min-width:110px;"><label style="font-size:0.75rem;color:var(--text-muted);display:block;">Year</label><select name="year" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;"><option value="">All</option>'''
    for y in years: extra += f'<option value="{h(y)}" {"selected" if y==year_filter else ""}>{h(y)}</option>'
    extra += '</select></div><div style="flex:1;min-width:150px;"><label style="font-size:0.75rem;color:var(--text-muted);display:block;">District</label><select name="district" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;"><option value="">All</option>'
    for d in districts: extra += f'<option value="{h(d[1])}" {"selected" if d[1]==district_filter else ""}>{h(d[0])}</option>'
    extra += '</select></div>'
    
    sort_opts = '<option value="school_year_desc">Year (Newest)</option><option value="school_year_asc">Year (Oldest)</option><option value="district_asc">District (A-Z)</option><option value="sped_desc">SPED % (High)</option><option value="lowincome_desc">Low Income % (High)</option><option value="el_desc">EL % (High)</option><option value="highneeds_desc">High Needs % (High)</option><option value="flne_desc">FLNE % (High)</option>'
    filter_bar = data_filter_bar('/data/enrollment/','District name...',extra).replace('<option value="">Default</option>', f'<option value="">Default</option>{sort_opts}').replace(f'value="{sort_by}"', f'value="{sort_by}" selected')
    
    body = f'{get_head("Enrollment Demographics","District enrollment: SPED, low income, EL, high needs, FLNE.")}{get_header("/data/")}<section class="section"><div class="container">'
    body += f'<div class="hero-stats" style="margin-bottom:1rem;"><div class="stat"><span class="stat-value">{total:,}</span><span class="stat-label">Records</span></div><div class="stat"><span class="stat-value">{len(years)}</span><span class="stat-label">Years</span></div><div class="stat"><span class="stat-value">{len(districts)}</span><span class="stat-label">Districts</span></div><div class="stat"><span class="stat-value">{total_pages}</span><span class="stat-label">Pages</span></div></div>'
    body += '<h2 style="font-size:1.5rem;margin-bottom:0.75rem;">Enrollment & Demographics Explorer</h2><p style="color:var(--text-muted);margin-bottom:1rem;">Every metric sortable. Sourced from DESE.</p>'+filter_bar
    if not rows: body += '<div class="empty-state"><p>No records match.</p></div>'
    else:
        body += f'<p style="color:var(--text-muted);font-size:0.8rem;">{offset+1}-{min(offset+per_page,total)} of {total:,}</p>'
        body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>District</th><th>Year</th><th>% SPED</th><th>% Low Income</th><th>% EL</th><th>% High Needs</th><th>% FLNE</th></tr></thead><tbody>'
        for r in rows:
            body += f'<tr><td><strong>{h(r["district_name"])}</strong></td><td>{h(r["school_year"])}</td><td>{h(str(r["sped_pct"] if "sped_pct" in r.keys() else "-"))}%</td><td>{h(str(r["low_income_pct"] if "low_income_pct" in r.keys() else "-"))}%</td><td>{h(str(r["el_pct"] if "el_pct" in r.keys() else "-"))}%</td><td>{h(str(r["high_needs_pct"] if "high_needs_pct" in r.keys() else "-"))}%</td><td>{h(str(r["flne_pct"] if "flne_pct" in r.keys() else "-"))}%</td></tr>'
        body += '</tbody></table></div>'+pagination_links('/data/enrollment/',page,total_pages,qs)
    return body + '<div style="margin-top:1rem;"><a href="/data/" class="btn btn-ghost">&larr; Data Hub</a></div></div></section>'+get_footer()


def handle_restraint_data_firestore(fs_db):
    """Restraint data handler using Firestore."""
    from collections import defaultdict
    import urllib.parse as up
    
    try:
        # Load all restraint docs from Firestore
        all_docs = list(fs_db.collection('restraint_data').stream())
        if not all_docs:
            return f'{get_head("Restraint Data")}{get_header("/data/")}<section class="section"><div class="container"><h2>Restraint Data</h2><p style="color:var(--text-muted);">No data in Firestore. Run migration first.</p></div></section>{get_footer()}'
        
        rows = [d.to_dict() for d in all_docs]
        # Filter summary rows
        rows = [r for r in rows if not r.get('is_summary_row', 0)]
        
        # Get distinct values
        years = sorted(set(r.get('school_year','') for r in rows), reverse=True)
        districts_list = sorted(set((r.get('district_name',''), r.get('district_code','')) 
                                     for r in rows if r.get('district_name')), key=lambda x: x[0])
        
    except Exception as e:
        return f'{get_head("Restraint Data")}{get_header("/data/")}<section class="section"><div class="container"><h2>Restraint Data</h2><p style="color:var(--text-muted);">Firestore error: {h(str(e)[:200])}</p></div></section>{get_footer()}'
    
    qs = {}
    if '?' in _current_path: qs = dict(up.parse_qsl(_current_path.split('?',1)[1]))
    search = qs.get('search','').strip().lower()
    sort_by = qs.get('sort','rate_desc')
    page = max(1,int(qs.get('page','1')))
    per_page = min(200,max(10,int(qs.get('per_page','50'))))
    year_filter = qs.get('year','').strip()
    district_filter = qs.get('district','').strip()
    
    # Filter in Python
    filtered = [r for r in rows]
    if search:
        filtered = [r for r in filtered if search in r.get('district_name','').lower() 
                     or search in r.get('school_name','').lower()
                     or search in r.get('district_code','').lower()]
    if year_filter:
        filtered = [r for r in filtered if r.get('school_year') == year_filter]
    if district_filter:
        filtered = [r for r in filtered if r.get('district_code') == district_filter]
    
    # Sort in Python
    sort_map = {'rate_desc':('restraint_rate_per_100', True), 'rate_asc':('restraint_rate_per_100', False),
        'restraints_desc':('total_restraints', True), 'injuries_desc':('total_injuries', True),
        'year_desc':('school_year', True), 'year_asc':('school_year', False),
        'district_asc':('district_name', False), 'school_asc':('school_name', False),
        'enrollment_desc':('enrollment', True)}
    sort_field, sort_desc = sort_map.get(sort_by, ('restraint_rate_per_100', True))
    filtered.sort(key=lambda r: r.get(sort_field, 0) or 0, reverse=sort_desc)
    
    total = len(filtered)
    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page
    paged = filtered[offset:offset + per_page]
    
    # YOY aggregation
    yoy = defaultdict(lambda: {'sc': 0, 'sr': 0, 'ss': 0, 'si': 0, 'se': 0})
    for r in rows:
        sy = r.get('school_year','')
        if sy:
            yoy[sy]['sc'] += 1
            yoy[sy]['sr'] += r.get('total_restraints', 0) or 0
            yoy[sy]['ss'] += r.get('students_restrained', 0) or 0
            yoy[sy]['si'] += r.get('total_injuries', 0) or 0
            yoy[sy]['se'] += r.get('enrollment', 0) or 0
    yoy_data = [{'school_year': k, **v} for k, v in sorted(yoy.items())]
    
    # Statewide avg
    total_restraints = sum(r.get('total_restraints', 0) or 0 for r in rows)
    total_enrollment = sum(r.get('enrollment', 0) or 0 for r in rows)
    sw_rate = round(total_restraints * 100.0 / total_enrollment, 2) if total_enrollment > 0 else 0
    
    # Top districts (min enrollment to filter tiny SPED schools)
    district_agg = defaultdict(lambda: {'tr': 0, 'enr': 0})
    for r in rows:
        dn = r.get('district_name','')
        enr = r.get('enrollment', 0) or 0
        if dn and enr > 0:
            district_agg[dn]['tr'] += r.get('total_restraints', 0) or 0
            district_agg[dn]['enr'] += enr
    top_districts = [{'district_name': k, 'rate': round(v['tr']*100.0/v['enr'], 2) if v['enr'] > 0 else 0} 
                     for k, v in sorted(district_agg.items(), key=lambda x: x[1]['tr']*100.0/max(x[1]['enr'],1), reverse=True)
                     if v['enr'] >= 100][:15]
    
    # Rate distribution buckets for histogram
    rate_buckets = {'0': 0, '0-1': 0, '1-2': 0, '2-5': 0, '5-10': 0, '10-20': 0, '20+': 0}
    for r in rows:
        rate = r.get('restraint_rate_per_100')
        if rate is not None and rate >= 0 and r.get('enrollment', 0):
            if rate == 0: rate_buckets['0'] += 1
            elif rate < 1: rate_buckets['0-1'] += 1
            elif rate < 2: rate_buckets['1-2'] += 1
            elif rate < 5: rate_buckets['2-5'] += 1
            elif rate < 10: rate_buckets['5-10'] += 1
            elif rate < 20: rate_buckets['10-20'] += 1
            else: rate_buckets['20+'] += 1
    
    # Annual averages
    annual_avg = defaultdict(list)
    for r in rows:
        if r.get('restraint_rate_per_100'):
            annual_avg[r.get('school_year','')].append(r['restraint_rate_per_100'])
    annual_avg = {k: sum(v)/len(v) for k, v in annual_avg.items()}
    
    # Filter bar HTML
    extra = f'<div style="flex:1;min-width:110px;"><label style="font-size:0.75rem;color:var(--text-muted);display:block;">Year</label><select name="year" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;"><option value="">All</option>'
    for y in years: extra += f'<option value="{h(y)}" {"selected" if y==year_filter else ""}>{h(y)}</option>'
    extra += '</select></div><div style="flex:1;min-width:150px;"><label style="font-size:0.75rem;color:var(--text-muted);display:block;">District</label><select name="district" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;"><option value="">All</option>'
    for d in districts_list: extra += f'<option value="{h(d[1])}" {"selected" if d[1]==district_filter else ""}>{h(d[0])}</option>'
    extra += '</select></div>'
    
    sort_opts = '<option value="rate_desc">Rate/100 (High)</option><option value="rate_asc">Rate/100 (Low)</option><option value="restraints_desc">Restraints (High)</option><option value="injuries_desc">Injuries (High)</option><option value="year_desc">Year (Newest)</option><option value="year_asc">Year (Oldest)</option><option value="district_asc">District (A-Z)</option><option value="school_asc">School (A-Z)</option><option value="enrollment_desc">Enrollment (High)</option>'
    filter_bar = data_filter_bar('/data/restraint/','District, school, or code...',extra).replace('<option value="">Default</option>', f'<option value="">Default</option>{sort_opts}').replace(f'value="{sort_by}"', f'value="{sort_by}" selected')
    
    # Chart configs
    yoy_cfg = json.dumps({
        'type': 'line', 'data': {
            'labels': [r['school_year'] for r in yoy_data],
            'datasets': [
                {'label': 'Total Restraints', 'data': [r['sr'] or 0 for r in yoy_data], 'borderColor': '#ff3b1f', 'backgroundColor': 'rgba(255,59,31,0.08)', 'fill': True, 'tension': 0.3, 'pointRadius': 4, 'pointHoverRadius': 7},
                {'label': 'Students Restrained', 'data': [r['ss'] or 0 for r in yoy_data], 'borderColor': '#ffa366', 'backgroundColor': 'rgba(255,163,102,0.08)', 'fill': True, 'tension': 0.3, 'pointRadius': 4, 'pointHoverRadius': 7},
                {'label': 'Injuries', 'data': [r['si'] or 0 for r in yoy_data], 'borderColor': '#f59e0b', 'backgroundColor': 'rgba(245,158,11,0.08)', 'fill': True, 'tension': 0.3, 'pointRadius': 4, 'pointHoverRadius': 7}
            ]
        },
        'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'labels': {'color': '#a0a0a0'}}}, 'scales': {'x': {'ticks': {'color': '#a0a0a0'}, 'grid': {'color': 'rgba(255,255,255,0.06)'}}, 'y': {'ticks': {'color': '#a0a0a0'}, 'grid': {'color': 'rgba(255,255,255,0.06)'}}}}
    })
    dist_cfg = json.dumps({
        'type': 'bar', 'data': {
            'labels': [r['district_name'] for r in top_districts],
            'datasets': [{'label': 'Rate per 100', 'data': [r['rate'] for r in top_districts], 'backgroundColor': '#ff5a1f', 'borderRadius': 4}]
        },
        'options': {'indexAxis': 'y', 'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'display': False}, 'tooltip': {'callbacks': {}}}, 'scales': {'x': {'ticks': {'color': '#a0a0a0'}, 'grid': {'color': 'rgba(255,255,255,0.06)'}}, 'y': {'ticks': {'color': '#f5f5f5', 'font': {'size': 11}}, 'grid': {'color': 'rgba(255,255,255,0.06)'}}}}
    })
    hist_labels = json.dumps(list(rate_buckets.keys()))
    hist_data = json.dumps(list(rate_buckets.values()))
    hist_cfg = json.dumps({
        'type': 'bar', 'data': {
            'labels': list(rate_buckets.keys()),
            'datasets': [{'label': 'Schools', 'data': list(rate_buckets.values()), 'backgroundColor': '#ffa366', 'borderRadius': 4}]
        },
        'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'display': False}}, 'scales': {'x': {'title': {'display': True, 'text': 'Restraint Rate per 100', 'color': '#a0a0a0'}, 'ticks': {'color': '#a0a0a0'}, 'grid': {'color': 'rgba(255,255,255,0.06)'}}, 'y': {'title': {'display': True, 'text': 'Number of Schools', 'color': '#a0a0a0'}, 'ticks': {'color': '#a0a0a0'}, 'grid': {'color': 'rgba(255,255,255,0.06)'}}}}
    })
    
    body = f'{get_head("Restraint & Seclusion","School-level restraint data from DESE, 2016-2025.")}{get_header("/data/")}'
    body += '<section class="section"><div class="container">'
    body += f'<div class="hero-stats" style="margin-bottom:1.5rem;"><div class="stat"><span class="stat-value">{total:,}</span><span class="stat-label">Records</span></div><div class="stat"><span class="stat-value">{len(years)}</span><span class="stat-label">Years</span></div><div class="stat"><span class="stat-value">{len(districts_list)}</span><span class="stat-label">Districts</span></div><div class="stat"><span class="stat-value">{sw_rate}</span><span class="stat-label">Statewide Rate/100</span></div></div>'
    
    body += '''<div class="restraint-info-box"><strong>About This Data</strong><br>Data sourced from the <a href="https://educationtocareer.data.mass.gov/" target="_blank" rel="noopener">Massachusetts E2C Data Hub</a> (Socrata API) and the <a href="https://profiles.doe.mass.edu/statereport/restraints.aspx" target="_blank" rel="noopener">DESE Profiles website</a>. DESE publishes school-year restraint data in <strong>late February</strong> of the following year. Dataset spans 2016-2025.<br><br><strong>Note:</strong> Counts below 6 are suppressed. True statewide totals are higher than published figures. School demographics (SPED%, income) joined from enrollment dataset.</div>'''
    
    # Row 1: Full-width YOY chart
    body += f'<div class="restraint-chart-card full-width" style="margin-bottom:1.5rem;"><h3 class="restraint-chart-title">Statewide Restraint Trends (2016-2025)</h3><div style="position:relative;height:350px;"><canvas id="restraintYOYChart"></canvas></div></div>'
    
    # Row 2: Three charts
    body += f'''<div class="restraint-charts">
        <div class="restraint-chart-card"><h3 class="restraint-chart-title">Top 15 Districts by Rate</h3><div style="position:relative;height:350px;"><canvas id="restraintDistrictChart"></canvas></div></div>
        <div class="restraint-chart-card"><h3 class="restraint-chart-title">Rate Distribution</h3><div style="position:relative;height:350px;"><canvas id="restraintHistChart"></canvas></div></div>
        <div class="restraint-chart-card"><h3 class="restraint-chart-title">Injury Rate by Year</h3><div style="position:relative;height:350px;"><canvas id="restraintInjuryChart"></canvas></div></div>
    </div>'''
    
    # YOY table
    if yoy_data:
        body += '<div style="margin-bottom:1.5rem;"><h3 style="margin-bottom:0.25rem;font-size:1.1rem;">Year-over-Year Statewide Totals</h3><p style="color:var(--accent-glow);font-size:0.78rem;margin-bottom:0.75rem;"><strong>Click column headers to sort.</strong></p><div class="repo-table-wrapper"><table class="repo-table sortable"><thead><tr><th data-sort="text">Year</th><th data-sort="number">Schools</th><th data-sort="number">Students</th><th data-sort="number">Restraints</th><th data-sort="number">Injuries</th><th data-sort="number">Rate/100</th></tr></thead><tbody>'
        for t in yoy_data:
            rate = f'{t["sr"]/t["se"]*100:.2f}' if t["se"] and t["se"] > 0 and t["sr"] else '-'
            body += f'<tr><td><strong>{h(t["school_year"])}</strong></td><td>{t["sc"]:,}</td><td>{t["ss"]:,}</td><td>{t["sr"]:,}</td><td>{t["si"]:,}</td><td>{rate}</td></tr>'
        body += '</tbody></table></div></div>'
    
    # School-level table with tooltips
    body += '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.5rem;"><h3 style="font-size:1.1rem;">School-Level Records</h3>'
    export_params = dict(qs); export_params.pop('page', None)
    export_url = '/data/restraint/export?' + up.urlencode(export_params)
    body += f'<a href="{export_url}" class="restraint-export-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Export CSV</a></div>'
    body += filter_bar
    
    if not paged:
        body += '<div class="empty-state"><p>No records match your filters.</p></div>'
    else:
        body += f'<p style="color:var(--text-muted);font-size:0.8rem;">{offset+1}-{min(offset+per_page,total)} of {total:,}</p>'
        # Column tooltips
        tips = {'Rate/100': '(Restraints / Enrollment) &times; 100', 'Inj Rate': 'Injuries per 100 students', 'SPED%': '% Students with Disabilities', 'Students': 'Unique students restrained (&lt;6 suppressed)', 'Restr.': 'Total restraint incidents', 'Inj.': 'Injuries during restraints'}
        th = lambda label: f'<th data-sort="number"><span class="col-has-tip">{label}<span class="col-tip">{tips.get(label,"")}</span></span></th>' if label in tips else f'<th data-sort="number">{label}</th>'
        body += '<div class="repo-table-wrapper"><table class="repo-table sortable"><thead><tr>'
        body += '<th data-sort="text">Year</th><th data-sort="text">District</th><th data-sort="text">School</th>'
        body += '<th data-sort="number">Enroll</th>' + th('Students') + th('Restr.') + th('Inj.')
        body += th('Rate/100') + th('Inj Rate') + th('SPED%') + '<th data-sort="number">LI%</th>'
        body += '</tr></thead><tbody>'
        
        for r in paged:
            suppressed = r.get('total_restraints_suppressed', 0)
            students = r.get('students_restrained') if not suppressed else '<6'
            restraints = r.get('total_restraints') if not suppressed else '<6'
            injuries = r.get('total_injuries') if not suppressed else '<6'
            rate_val = r.get('restraint_rate_per_100')
            rate = f'{rate_val:.2f}' if rate_val is not None else '-'
            inj_rate = r.get('injury_rate_per_100')
            inj_rate_str = f'{inj_rate:.2f}' if inj_rate is not None else '-'
            sped = r.get('swd_pct')
            sped_str = f'{sped:.1f}%' if sped is not None else '-'
            li = r.get('li_pct')
            li_str = f'{li:.1f}%' if li is not None else '-'
            yr_avg = annual_avg.get(r.get('school_year',''), 0)
            delta_html = ''
            if yr_avg and rate_val and rate_val > 0:
                pct_diff = ((rate_val - yr_avg) / yr_avg * 100) if yr_avg > 0 else 0
                if abs(pct_diff) > 5:
                    color = 'var(--danger)' if pct_diff > 0 else 'var(--success)'
                    arrow = '&#9650;' if pct_diff > 0 else '&#9660;'
                    delta_html = f' <span style="color:{color};font-size:0.7rem;">{arrow}{abs(pct_diff):.0f}%</span>'
            body += f'<tr><td style="white-space:nowrap;">{h(str(r.get("school_year","")))}</td><td>{h(str(r.get("district_name","")))}</td><td><strong>{h(str(r.get("school_name","-")))})</strong></td><td>{r.get("enrollment", 0) or 0:,}</td><td>{students}</td><td>{restraints}</td><td>{injuries}</td><td style="white-space:nowrap;">{rate}{delta_html}</td><td>{inj_rate_str}</td><td>{sped_str}</td><td>{li_str}</td></tr>'
        body += '</tbody></table></div>' + pagination_links('/data/restraint/', page, total_pages, qs)
    
    # Injury chart data
    inj_chart_labels = json.dumps([r['school_year'] for r in yoy_data])
    inj_chart_data = json.dumps([round(r['si']*100.0/r['sr'], 2) if r['sr'] > 0 else 0 for r in yoy_data])
    inj_rate_data = json.dumps([round(r['si']*100.0/r['se'], 2) if r['se'] > 0 else 0 for r in yoy_data])
    
    # Chart JS - initialize all 4 charts
    body += f'''<style>
.col-has-tip {{ position:relative; cursor:help; border-bottom:1px dotted var(--text-muted); }}
.col-has-tip .col-tip {{ display:none; position:absolute; bottom:120%; left:0; background:var(--bg-elevated); border:1px solid var(--accent-glow); border-radius:6px; padding:0.4rem 0.6rem; font-size:0.72rem; white-space:nowrap; z-index:100; color:var(--text-secondary); font-weight:400; }}
.col-has-tip:hover .col-tip {{ display:block; }}
</style>
<script>
document.addEventListener("DOMContentLoaded",function(){{
try{{
var c1=document.getElementById("restraintYOYChart");
if(c1&&typeof Chart!=="undefined"){{new Chart(c1,{yoy_cfg})}}
var c2=document.getElementById("restraintDistrictChart");
if(c2&&typeof Chart!=="undefined"){{new Chart(c2,{dist_cfg})}}
var c3=document.getElementById("restraintHistChart");
if(c3&&typeof Chart!=="undefined"){{new Chart(c3,{hist_cfg})}}
var c4=document.getElementById("restraintInjuryChart");
if(c4&&typeof Chart!=="undefined"){{new Chart(c4,{{type:"bar",data:{{labels:{inj_chart_labels},datasets:[{{label:"Injuries per Restraint (%)",data:{inj_chart_data},backgroundColor:"#ef4444",borderRadius:4}}]}},options:{{responsive:!0,maintainAspectRatio:!1,plugins:{{legend:{{display:!1}}}},scales:{{x:{{ticks:{{color:"#a0a0a0"}},grid:{{color:"rgba(255,255,255,0.06)"}}}},y:{{ticks:{{color:"#a0a0a0"}},grid:{{color:"rgba(255,255,255,0.06)"}}}}}}}}}})}}
}}catch(e){{console.error(e)}}
document.querySelectorAll("table.sortable th").forEach(function(th,col){{
th.style.cursor="pointer";th.style.userSelect="none";th.title="Click to sort";
th.onclick=function(){{
var tbody=this.closest("table").tBodies[0];
var rows=Array.from(tbody.rows);
var asc=this.classList.toggle("sort-asc");
this.closest("tr").querySelectorAll("th").forEach(function(h){{h.classList.remove("sort-asc","sort-desc")}});
this.classList.add(asc?"sort-asc":"sort-desc");
var type=this.dataset.sort||"text";
rows.sort(function(a,b){{
var va=a.cells[col].textContent.replace(/[,%<>\u25b2\u25bc]/g,"").trim();
var vb=b.cells[col].textContent.replace(/[,%<>\u25b2\u25bc]/g,"").trim();
if(type==="number"){{va=parseFloat(va)||0;vb=parseFloat(vb)||0;}}
else{{va=va.toLowerCase();vb=vb.toLowerCase();}}
if(va<vb)return asc?-1:1;if(va>vb)return asc?1:-1;return 0;
}});
rows.forEach(function(r){{tbody.appendChild(r)}});
}};}});
}});</script>'''
    body += '<div style="margin-top:1rem;"><a href="/data/" class="btn btn-ghost">&larr; Data Hub</a></div></div></section>' + get_footer()
    return body


def handle_restraint_data():
    fs = get_fs()
    if fs:
        return handle_restraint_data_firestore(fs)
    
    conn = get_db(); conn.row_factory = sqlite3.Row
    try:
        years = [r[0] for r in conn.execute("SELECT DISTINCT school_year FROM restraint_data WHERE is_summary_row=0 ORDER BY school_year DESC").fetchall()]
        districts = conn.execute("SELECT DISTINCT district_name, district_code FROM restraint_data WHERE is_summary_row=0 ORDER BY district_name").fetchall()
    except:
        conn.close()
        return f'{get_head("Restraint Data")}{get_header("/data/")}<section class="section"><div class="container"><h2>Restraint Data</h2><p style="color:var(--text-muted);">Data not loaded. Run the ingest pipeline first.</p></div></section>{get_footer()}'
    
    import urllib.parse as up
    qs = {}; 
    if '?' in _current_path: qs = dict(up.parse_qsl(_current_path.split('?',1)[1]))
    search = qs.get('search','').strip(); sort_by = qs.get('sort','rate_desc')
    page = max(1,int(qs.get('page','1'))); per_page = min(200,max(10,int(qs.get('per_page','50'))))
    year_filter = qs.get('year','').strip(); district_filter = qs.get('district','').strip()
    
    
    where = ["is_summary_row=0"]; params = []
    if search: where.append("(district_name LIKE ? OR school_name LIKE ? OR district_code LIKE ?)"); params.extend([f'%{search}%',f'%{search}%',f'%{search}%'])
    if year_filter: where.append("school_year = ?"); params.append(year_filter)
    if district_filter: where.append("district_code = ?"); params.append(district_filter)
    where_clause = ' WHERE ' + ' AND '.join(where)
    total = conn.execute(f'SELECT COUNT(*) FROM restraint_data{where_clause}', params).fetchone()[0]
    
    sort_map = {'rate_desc':'restraint_rate_per_100 DESC','rate_asc':'restraint_rate_per_100 ASC',
        'restraints_desc':'total_restraints DESC','injuries_desc':'total_injuries DESC',
        'year_desc':'school_year DESC','year_asc':'school_year ASC',
        'district_asc':'district_name ASC','school_asc':'school_name ASC',
        'enrollment_desc':'enrollment DESC'}
    order = sort_map.get(sort_by, 'restraint_rate_per_100 DESC')
    offset = (page-1)*per_page; total_pages = max(1,(total+per_page-1)//per_page)
    
    # YOY trends for chart
    yoy_data = conn.execute("SELECT school_year, COUNT(*) as sc, SUM(total_restraints) as sr, SUM(students_restrained) as ss, SUM(total_injuries) as si, SUM(enrollment) as se FROM restraint_data WHERE is_summary_row=0 GROUP BY school_year ORDER BY school_year").fetchall()
    
    # Statewide avg for hero stat
    sw_rate = conn.execute("SELECT ROUND(SUM(total_restraints)*100.0/SUM(enrollment),2) FROM restraint_data WHERE is_summary_row=0").fetchone()[0] or 0
    
    # District chart data (top 15 by rate)
    top_districts = conn.execute("SELECT district_name, SUM(total_restraints) as tr, ROUND(SUM(total_restraints)*100.0/SUM(enrollment),2) as rate FROM restraint_data WHERE is_summary_row=0 AND enrollment>0 GROUP BY district_name HAVING SUM(total_restraints)>0 ORDER BY rate DESC LIMIT 15").fetchall()
    
    # Annual stats for percentiles
    annual_stats_rows = conn.execute("SELECT school_year, AVG(restraint_rate_per_100) as avg_rate FROM restraint_data WHERE is_summary_row=0 AND restraint_rate_per_100>0 GROUP BY school_year").fetchall()
    annual_avg = {r['school_year']: r['avg_rate'] for r in annual_stats_rows}
    
    rows = conn.execute(f'SELECT * FROM restraint_data{where_clause} ORDER BY {order} LIMIT ? OFFSET ?', params+[per_page,offset]).fetchall()
    conn.close()
    
    # Filter bar
    extra = f'''<div style="flex:1;min-width:110px;"><label style="font-size:0.75rem;color:var(--text-muted);display:block;">Year</label><select name="year" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;"><option value="">All</option>'''
    for y in years: extra += f'<option value="{h(y)}" {"selected" if y==year_filter else ""}>{h(y)}</option>'
    extra += '</select></div><div style="flex:1;min-width:150px;"><label style="font-size:0.75rem;color:var(--text-muted);display:block;">District</label><select name="district" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;"><option value="">All</option>'
    for d in districts: extra += f'<option value="{h(d[1])}" {"selected" if d[1]==district_filter else ""}>{h(d[0])}</option>'
    extra += '</select></div>'
    
    sort_opts = '<option value="rate_desc">Rate/100 (High)</option><option value="rate_asc">Rate/100 (Low)</option><option value="restraints_desc">Restraints (High)</option><option value="injuries_desc">Injuries (High)</option><option value="year_desc">Year (Newest)</option><option value="year_asc">Year (Oldest)</option><option value="district_asc">District (A-Z)</option><option value="school_asc">School (A-Z)</option><option value="enrollment_desc">Enrollment (High)</option>'
    filter_bar = data_filter_bar('/data/restraint/','District, school, or code...',extra).replace('<option value="">Default</option>', f'<option value="">Default</option>{sort_opts}').replace(f'value="{sort_by}"', f'value="{sort_by}" selected')
    
    # Build page
    body = f'{get_head("Restraint & Seclusion","School-level restraint data from DESE, 2016-2025.")}{get_header("/data/")}'
    body += '<section class="section"><div class="container">'
    
    # Hero stats
    body += f'''<div class="hero-stats" style="margin-bottom:1.5rem;">
        <div class="stat"><span class="stat-value">{total:,}</span><span class="stat-label">Records</span></div>
        <div class="stat"><span class="stat-value">{len(years)}</span><span class="stat-label">Years</span></div>
        <div class="stat"><span class="stat-value">{len(districts)}</span><span class="stat-label">Districts</span></div>
        <div class="stat"><span class="stat-value">{sw_rate}</span><span class="stat-label">Statewide Rate/100</span></div>
    </div>'''
    
    # DESE info box
    body += '''<div class="restraint-info-box">
        <strong>About This Data</strong><br>
        Data sourced from the <a href="https://profiles.doe.mass.edu/statereport/restraints.aspx" target="_blank" rel="noopener">Massachusetts DESE Profiles website</a>. 
        DESE typically publishes school-year restraint data in <strong>late February</strong> of the following year 
        (e.g., 2024-25 data expected in February 2026). This dataset spans school years 2016-17 through 2024-25, 
        covering all Massachusetts public school districts.<br><br>
        <strong>Note:</strong> DESE suppresses restraint counts when fewer than 6 students are restrained at a school. 
        Suppressed cells show 0 in the raw data. The true number of restraint incidents statewide is higher than 
        reflected in published figures.
    </div>'''
    
    # Charts section
    body += f'''<div class="restraint-charts">
        <div class="restraint-chart-card full-width">
            <h3 class="restraint-chart-title">Statewide Restraint Trends (2016-2025)</h3>
            <div style="position:relative;height:350px;"><canvas id="restraintYOYChart"></canvas></div>
        </div>
        <div class="restraint-chart-card">
            <h3 class="restraint-chart-title">Top 15 Districts by Restraint Rate</h3>
            <div style="position:relative;height:400px;"><canvas id="restraintDistrictChart"></canvas></div>
        </div>
    </div>'''
    
    # YOY summary table
    if yoy_data:
        body += '<div style="margin-bottom:1.5rem;"><h3 style="margin-bottom:0.25rem;font-size:1.1rem;">Year-over-Year Statewide Totals</h3><p style="color:var(--accent-glow);font-size:0.78rem;margin-bottom:0.75rem;"><strong>Click column headers to sort.</strong> Note: Seed data may show identical totals across years — full per-year data regeneration pending.</p><div class="repo-table-wrapper"><table class="repo-table sortable"><thead><tr><th data-sort="text">Year</th><th data-sort="number">Schools</th><th data-sort="number">Students</th><th data-sort="number">Restraints</th><th data-sort="number">Injuries</th><th data-sort="number">Rate/100</th></tr></thead><tbody>'
        for t in yoy_data:
            rate = f'{t["sr"]/t["se"]*100:.2f}' if t["se"] and t["se"]>0 and t["sr"] else '-'
            body += f'<tr><td><strong>{h(t["school_year"])}</strong></td><td>{t["sc"]:,}</td><td>{t["ss"]:,}</td><td>{t["sr"]:,}</td><td>{t["si"]:,}</td><td>{rate}</td></tr>'
        body += '</tbody></table></div></div>'
    
    # School-level records
    body += '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.5rem;"><h3 style="font-size:1.1rem;">School-Level Records</h3>'
    
    # CSV export link
    export_params = dict(qs); export_params.pop('page',None)
    export_url = '/data/restraint/export?' + up.urlencode(export_params)
    body += f'<a href="{export_url}" class="restraint-export-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Export CSV</a>'
    body += '</div>'
    
    body += filter_bar
    
    if not rows:
        body += '<div class="empty-state"><p>No records match your filters.</p></div>'
    else:
        body += f'<p style="color:var(--text-muted);font-size:0.8rem;">{offset+1}-{min(offset+per_page,total)} of {total:,}</p>'
        body += '<div class="repo-table-wrapper"><table class="repo-table sortable"><thead><tr><th data-sort="text">Year</th><th data-sort="text">District</th><th data-sort="text">School</th><th data-sort="number">Enroll</th><th data-sort="number">Students</th><th data-sort="number">Restr.</th><th data-sort="number">Inj.</th><th data-sort="number">Rate/100</th></tr></thead><tbody>'
        for r in rows:
            students = r['students_restrained'] if r['students_restrained_suppressed'] == 0 else f'&lt;6'
            restraints = r['total_restraints'] if r['total_restraints_suppressed'] == 0 else f'&lt;6'
            injuries = r['total_injuries'] if r['total_injuries_suppressed'] == 0 else f'&lt;6'
            rate = f'{r["restraint_rate_per_100"]:.2f}' if r['restraint_rate_per_100'] is not None else '-'
            yr_avg = annual_avg.get(r['school_year'], 0)
            delta_html = ''
            if yr_avg and r['restraint_rate_per_100'] and r['restraint_rate_per_100'] > 0:
                pct_diff = ((r['restraint_rate_per_100'] - yr_avg) / yr_avg * 100) if yr_avg > 0 else 0
                if abs(pct_diff) > 5:
                    color = 'var(--danger)' if pct_diff > 0 else 'var(--success)'
                    arrow = '&#9650;' if pct_diff > 0 else '&#9660;'
                    delta_html = f' <span style="color:{color};font-size:0.7rem;">{arrow}{abs(pct_diff):.0f}%</span>'
            body += f'<tr><td style="white-space:nowrap;">{h(r["school_year"])}</td><td>{h(r["district_name"])}</td><td><strong>{h(r["school_name"] or "-")}</strong></td><td>{r["enrollment"] or 0:,}</td><td>{students}</td><td>{restraints}</td><td>{injuries}</td><td style="white-space:nowrap;">{rate}{delta_html}</td></tr>'
        body += '</tbody></table></div>'+pagination_links('/data/restraint/',page,total_pages,qs)
    
    # Chart configs as Python dicts → JSON for inline JS
    yoy_cfg = json.dumps({
        'type': 'line',
        'data': {
            'labels': [r['school_year'] for r in yoy_data],
            'datasets': [
                {'label': 'Total Restraints', 'data': [r['sr'] or 0 for r in yoy_data], 'borderColor': '#ff3b1f', 'backgroundColor': 'rgba(255,59,31,0.08)', 'fill': True, 'tension': 0.3, 'pointRadius': 4, 'pointHoverRadius': 7},
                {'label': 'Students Restrained', 'data': [r['ss'] or 0 for r in yoy_data], 'borderColor': '#ffa366', 'backgroundColor': 'rgba(255,163,102,0.08)', 'fill': True, 'tension': 0.3, 'pointRadius': 4, 'pointHoverRadius': 7},
                {'label': 'Injuries', 'data': [r['si'] or 0 for r in yoy_data], 'borderColor': '#f59e0b', 'backgroundColor': 'rgba(245,158,11,0.08)', 'fill': True, 'tension': 0.3, 'pointRadius': 4, 'pointHoverRadius': 7}
            ]
        },
        'options': {
            'responsive': True, 'maintainAspectRatio': False,
            'plugins': {'legend': {'labels': {'color': '#a0a0a0'}}},
            'scales': {
                'x': {'ticks': {'color': '#a0a0a0'}, 'grid': {'color': 'rgba(255,255,255,0.06)'}},
                'y': {'ticks': {'color': '#a0a0a0'}, 'grid': {'color': 'rgba(255,255,255,0.06)'}}
            }
        }
    })
    dist_cfg = json.dumps({
        'type': 'bar',
        'data': {
            'labels': [r['district_name'] for r in top_districts],
            'datasets': [{'label': 'Rate per 100', 'data': [r['rate'] for r in top_districts], 'backgroundColor': '#ff5a1f', 'borderRadius': 4}]
        },
        'options': {
            'indexAxis': 'y', 'responsive': True, 'maintainAspectRatio': False,
            'plugins': {'legend': {'display': False}},
            'scales': {
                'x': {'ticks': {'color': '#a0a0a0'}, 'grid': {'color': 'rgba(255,255,255,0.06)'}},
                'y': {'ticks': {'color': '#f5f5f5', 'font': {'size': 11}}, 'grid': {'color': 'rgba(255,255,255,0.06)'}}
            }
        }
    })
    body += f'''<script>
document.addEventListener("DOMContentLoaded",function(){{try{{
    var c1=document.getElementById("restraintYOYChart");
    if(c1&&typeof Chart!=="undefined"){{new Chart(c1,{yoy_cfg})}}
    var c2=document.getElementById("restraintDistrictChart");
    if(c2&&typeof Chart!=="undefined"){{new Chart(c2,{dist_cfg})}}
}}catch(e){{console.error(e)}};

/* Sortable tables */
document.querySelectorAll("table.sortable th").forEach(function(th,col){{
  th.style.cursor="pointer";th.style.userSelect="none";
  th.title="Click to sort";
  th.onclick=function(){{
    var tbody=this.closest("table").tBodies[0];
    var rows=Array.from(tbody.rows);
    var asc=this.classList.toggle("sort-asc");
    this.closest("tr").querySelectorAll("th").forEach(function(h){{h.classList.remove("sort-asc","sort-desc")}});
    this.classList.add(asc?"sort-asc":"sort-desc");
    var type=this.dataset.sort||"text";
    rows.sort(function(a,b){{
      var va=a.cells[col].textContent.replace(/[,%&lt;>\\u25b2\\u25bc]/g,"").trim();
      var vb=b.cells[col].textContent.replace(/[,%&lt;>\\u25b2\\u25bc]/g,"").trim();
      if(type==="number"){{va=parseFloat(va)||0;vb=parseFloat(vb)||0;}}
      else{{va=va.toLowerCase();vb=vb.toLowerCase();}}
      if(va<vb)return asc?-1:1;
      if(va>vb)return asc?1:-1;
      return 0;
    }});
    rows.forEach(function(r){{tbody.appendChild(r)}});
  }}
}});
}});</script>'''
    
    body += '<div style="margin-top:1rem;"><a href="/data/" class="btn btn-ghost">&larr; Data Hub</a></div></div></section>'+get_footer()
    return body


def handle_restraint_export(handler):
    conn = get_db(); conn.row_factory = sqlite3.Row
    import urllib.parse as up, csv, io
    qs = {}
    if '?' in _current_path: qs = dict(up.parse_qsl(_current_path.split('?',1)[1]))
    search = qs.get('search','').strip(); sort_by = qs.get('sort','rate_desc')
    year_filter = qs.get('year','').strip(); district_filter = qs.get('district','').strip()
    
    where = ["is_summary_row=0"]; params = []
    if search: where.append("(district_name LIKE ? OR school_name LIKE ? OR district_code LIKE ?)"); params.extend([f'%{search}%',f'%{search}%',f'%{search}%'])
    if year_filter: where.append("school_year = ?"); params.append(year_filter)
    if district_filter: where.append("district_code = ?"); params.append(district_filter)
    where_clause = ' WHERE ' + ' AND '.join(where)
    
    sort_map = {'rate_desc':'restraint_rate_per_100 DESC','rate_asc':'restraint_rate_per_100 ASC',
        'restraints_desc':'total_restraints DESC','injuries_desc':'total_injuries DESC',
        'year_desc':'school_year DESC','year_asc':'school_year ASC',
        'district_asc':'district_name ASC','school_asc':'school_name ASC',
        'enrollment_desc':'enrollment DESC'}
    order = sort_map.get(sort_by, 'restraint_rate_per_100 DESC')
    
    rows = conn.execute(f'SELECT * FROM restraint_data{where_clause} ORDER BY {order}', params).fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['school_year','district_name','district_code','school_name','school_code','enrollment','students_restrained','total_restraints','total_injuries','restraint_rate_per_100','injuries_per_restraint'])
    for r in rows:
        writer.writerow([r['school_year'],r['district_name'],r['district_code'],r['school_name'],r['school_code'],
            r['enrollment'],r['students_restrained'],r['total_restraints'],r['total_injuries'],
            f'{r["restraint_rate_per_100"]:.2f}' if r['restraint_rate_per_100'] is not None else '',
            f'{r["injuries_per_restraint"]:.3f}' if r['injuries_per_restraint'] is not None else ''])
    
    csv_content = output.getvalue()
    handler.send_response(200)
    handler.send_header('Content-Type', 'text/csv; charset=utf-8')
    handler.send_header('Content-Disposition', 'attachment; filename="restraint_data.csv"')
    handler.send_header('Content-Length', str(len(csv_content.encode('utf-8'))))
    handler.end_headers()
    handler.wfile.write(csv_content.encode('utf-8'))


def handle_prs_data():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    
    # Get filter values from URL (set by do_GET before calling handler)
    qs = {}
    import urllib.parse as up
    if '?' in _current_path:
        qs = dict(up.parse_qsl(_current_path.split('?',1)[1]))
    
    search = qs.get('search', '').strip()
    status_filter = qs.get('status', '').strip()
    cat_filter = qs.get('category', '').strip()
    closure_filter = qs.get('closure', '').strip()
    sort_by = qs.get('sort', 'intake_date_desc')
    page = max(1, int(qs.get('page', '1')))
    per_page = min(200, max(10, int(qs.get('per_page', '50'))))
    district_filter = qs.get('district', '').strip()
    date_from = qs.get('date_from', '').strip()
    date_to = qs.get('date_to', '').strip()
    
    try:
        # Get unique filter values
        statuses = [r[0] for r in conn.execute("SELECT DISTINCT status FROM prs_intakes_data WHERE status IS NOT NULL AND status != '' ORDER BY status").fetchall()]
        categories = [r[0] for r in conn.execute("SELECT DISTINCT category FROM prs_intakes_data WHERE category IS NOT NULL AND category != '' ORDER BY category").fetchall()]
        closures = [r[0] for r in conn.execute("SELECT DISTINCT closure_code FROM prs_intakes_data WHERE closure_code IS NOT NULL AND closure_code != '' ORDER BY closure_code").fetchall()]
        
        # Build WHERE clause
        where = []
        params = []
        if search:
            where.append("(prs_number LIKE ? OR district LIKE ? OR category LIKE ? OR subcategory LIKE ?)")
            p = f'%{search}%'
            params.extend([p, p, p, p])
        if status_filter:
            selected = status_filter.split(',')
            placeholders = ','.join(['?' for _ in selected])
            where.append(f'status IN ({placeholders})')
            params.extend(selected)
        if cat_filter:
            selected = cat_filter.split(',')
            placeholders = ','.join(['?' for _ in selected])
            where.append(f'category IN ({placeholders})')
            params.extend(selected)
        if closure_filter:
            selected = closure_filter.split(',')
            placeholders = ','.join(['?' for _ in selected])
            where.append(f'closure_code IN ({placeholders})')
            params.extend(selected)
        if district_filter:
            where.append('district LIKE ?')
            params.append(f'%{district_filter}%')
        if date_from:
            where.append('intake_date >= ?')
            params.append(date_from)
        if date_to:
            where.append('intake_date <= ?')
            params.append(date_to)
        
        where_clause = ' WHERE ' + ' AND '.join(where) if where else ''
        
        # Count total
        total = conn.execute(f'SELECT COUNT(*) FROM prs_intakes_data{where_clause}', params).fetchone()[0]
        total_all = conn.execute("SELECT COUNT(*) FROM prs_intakes_data").fetchone()[0]
        
        # Sort
        sort_map = {
            'intake_date_desc': 'intake_date DESC',
            'intake_date_asc': 'intake_date ASC',
            'prs_number_asc': 'prs_number ASC',
            'prs_number_desc': 'prs_number DESC',
            'district_asc': 'district ASC',
            'district_desc': 'district DESC',
            'status_asc': 'status ASC',
        }
        order = sort_map.get(sort_by, 'intake_date DESC')
        
        # Paginate
        offset = (page - 1) * per_page
        total_pages = max(1, (total + per_page - 1) // per_page)
        
        rows = conn.execute(
            f'SELECT * FROM prs_intakes_data{where_clause} ORDER BY {order} LIMIT ? OFFSET ?',
            params + [per_page, offset]
        ).fetchall()
        
        # Quick stats for filtered set
        stats = {}
        if where:
            stats['closed'] = conn.execute(f'SELECT COUNT(*) FROM prs_intakes_data{where_clause} AND status="Closed"', params).fetchone()[0]
            stats['open'] = conn.execute(f'SELECT COUNT(*) FROM prs_intakes_data{where_clause} AND status NOT IN ("Closed","Case Inactive: Pending BSEA")', params).fetchone()[0]
        else:
            stats['closed'] = conn.execute("SELECT COUNT(*) FROM prs_intakes_data WHERE status='Closed'").fetchone()[0]
            stats['open'] = total - stats['closed']
        
    except Exception as e:
        conn.close()
        return f'{get_head("PRS Data Dashboard")}{get_header("/data/")}<section class="section"><div class="container"><h2>PRS Data Dashboard</h2><p style="color:var(--text-muted);">PRS data table not found. Run the data pipeline to load it.</p><div style="margin-top:1.5rem;"><a href="/data/" class="btn btn-ghost">&larr; Data Hub</a></div></div></section>{get_footer()}'
    
    conn.close()
    
    # Build page
    head_body = f'{get_head("PRS Data Dashboard", "DESE Problem Resolution System - complaint intake, findings, and closure data.")}{get_header("/data/")}<section class="section"><div class="container">'
    
    # Stats row
    head_body += f'''<div class="hero-stats" style="margin-bottom:1rem;">
    <div class="stat"><span class="stat-value">{total:,}</span><span class="stat-label">Filtered Records</span></div>
    <div class="stat"><span class="stat-value">{total_all:,}</span><span class="stat-label">Total Database</span></div>
    <div class="stat"><span class="stat-value">{stats.get("open",0):,}</span><span class="stat-label">Open/Active</span></div>
    <div class="stat"><span class="stat-value">{stats.get("closed",0):,}</span><span class="stat-label">Closed</span></div>
    <div class="stat"><span class="stat-value">{total_pages}</span><span class="stat-label">Pages ({per_page}/pg)</span></div>
</div>'''
    
    # Search + Filter bar
    head_body += f'''<form method="get" action="/data/prs/" style="margin-bottom:1rem;">
<div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:flex-end;">
    <div style="flex:2;min-width:200px;">
        <label style="font-size:0.75rem;color:var(--text-muted);display:block;">Search</label>
        <input type="text" name="search" value="{h(search)}" placeholder="PRS number, district, category..." 
            style="width:100%;padding:0.5rem 0.75rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.85rem;">
    </div>
    <div style="flex:1;min-width:140px;">
        <label style="font-size:0.75rem;color:var(--text-muted);display:block;">Status (multi-select)</label>
        <select name="status" multiple style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;min-height:36px;" size="3">
            <option value="">All Statuses</option>'''
    for s in statuses:
        sel = 'selected' if s in status_filter.split(',') else ''
        head_body += f'<option value="{h(s)}" {sel}>{h(s)}</option>'
    head_body += '''</select>
    </div>
    <div style="flex:1;min-width:140px;">
        <label style="font-size:0.75rem;color:var(--text-muted);display:block;">Category (multi)</label>
        <select name="category" multiple style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;min-height:36px;" size="3">'''
    for c in categories:
        sel = 'selected' if c in cat_filter.split(',') else ''
        head_body += f'<option value="{h(c)}" {sel}>{h(c)}</option>'
    head_body += '''</select>
    </div>
    <div style="flex:1;min-width:120px;">
        <label style="font-size:0.75rem;color:var(--text-muted);display:block;">Closure Code</label>
        <select name="closure" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;">
            <option value="">All</option>'''
    for cl in closures:
        sel = 'selected' if cl == closure_filter else ''
        head_body += f'<option value="{h(cl)}" {sel}>{h(cl)}</option>'
    head_body += '''</select>
    </div>
    <div style="flex:1;min-width:100px;">
        <label style="font-size:0.75rem;color:var(--text-muted);display:block;">Sort By</label>
        <select name="sort" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;">'''
    sort_opts = [
        ('intake_date_desc', 'Date (Newest)'), ('intake_date_asc', 'Date (Oldest)'),
        ('prs_number_asc', 'PRS # (A-Z)'), ('prs_number_desc', 'PRS # (Z-A)'),
        ('district_asc', 'District (A-Z)'), ('district_desc', 'District (Z-A)'),
        ('status_asc', 'Status'),
    ]
    for val, label in sort_opts:
        sel = 'selected' if sort_by == val else ''
        head_body += f'<option value="{val}" {sel}>{label}</option>'
    head_body += '''</select>
    </div>
    <div style="flex:1;min-width:80px;">
        <label style="font-size:0.75rem;color:var(--text-muted);display:block;">Per Page</label>
        <select name="per_page" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;">'''
    for pp in [25, 50, 100, 200]:
        sel = 'selected' if per_page == pp else ''
        head_body += f'<option value="{pp}" {sel}>{pp}</option>'
    head_body += '''</select>
    </div>
    <div style="flex:0;min-width:80px;display:flex;align-items:flex-end;">
        <button type="submit" class="btn btn-primary" style="padding:0.5rem 1rem;font-size:0.85rem;">Filter</button>
    </div>
</div>
</form>'''
    
    # Results table
    if not rows:
        head_body += '<div class="empty-state"><p>No PRS records match your filters.</p><a href="/data/prs/" class="btn btn-ghost" style="margin-top:1rem;">Clear Filters</a></div>'
    else:
        head_body += f'<p style="color:var(--text-muted);font-size:0.8rem;margin-bottom:0.5rem;">Showing {offset+1}-{min(offset+per_page,total)} of {total:,} records</p>'
        head_body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>PRS #</th><th>District</th><th>Intake Date</th><th>Status</th><th>Findings Date</th><th>Category</th><th>Subcategory</th><th>Closure Code</th></tr></thead><tbody>'
        for r in rows:
            head_body += f'''<tr>
    <td style="font-family:var(--font-mono);font-weight:600;white-space:nowrap;">{h(r["prs_number"])}</td>
    <td><strong>{h(r["district"])}</strong></td>
    <td style="white-space:nowrap;">{format_date(r["intake_date"])}</td>
    <td>{status_badge(str(r["status"]).lower() if r["status"] else "unknown")}</td>
    <td style="white-space:nowrap;">{format_date(r["findings_date"])}</td>
    <td>{h(r["category"] or "-")}</td>
    <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{h(r["subcategory"] or "-")}</td>
    <td style="font-size:0.8rem;max-width:180px;">{h(r["closure_code"] or "-")}</td>
</tr>'''
        head_body += '</tbody></table></div>'
        
        # Pagination
        if total_pages > 1:
            head_body += f'<div style="display:flex;gap:0.5rem;justify-content:center;margin-top:1.5rem;flex-wrap:wrap;">'
            # Build query string for pagination links
            def page_link(p):
                params = []
                if search: params.append(f'search={up.quote(search)}')
                if status_filter: params.append(f'status={up.quote(status_filter)}')
                if cat_filter: params.append(f'category={up.quote(cat_filter)}')
                if closure_filter: params.append(f'closure={up.quote(closure_filter)}')
                if sort_by != 'intake_date_desc': params.append(f'sort={sort_by}')
                if per_page != 50: params.append(f'per_page={per_page}')
                params.append(f'page={p}')
                return '/data/prs/?' + '&'.join(params)
            
            if page > 1:
                head_body += f'<a href="{page_link(1)}" class="btn btn-ghost" style="padding:0.4rem 0.8rem;font-size:0.8rem;">&laquo; First</a>'
            for p in range(max(1, page-2), min(total_pages+1, page+3)):
                cls = 'btn-primary' if p == page else 'btn-ghost'
                head_body += f'<a href="{page_link(p)}" class="btn {cls}" style="padding:0.4rem 0.8rem;font-size:0.8rem;">{p}</a>'
            if page < total_pages:
                head_body += f'<a href="{page_link(total_pages)}" class="btn btn-ghost" style="padding:0.4rem 0.8rem;font-size:0.8rem;">Last &raquo;</a>'
            head_body += '</div>'
    
    return head_body + '<div style="margin-top:1.5rem;"><a href="/data/" class="btn btn-ghost">&larr; Data Hub</a></div></div></section>' + get_footer()


def handle_attendance():
    conn = get_db(); conn.row_factory = sqlite3.Row
    try:
        years = [r[0] for r in conn.execute("SELECT DISTINCT school_year FROM attendance_data ORDER BY school_year DESC").fetchall()]
        districts = conn.execute("SELECT DISTINCT district_name, district_code FROM attendance_data ORDER BY district_name").fetchall()
    except: conn.close(); return f'{get_head("Attendance")}{get_header("/data/")}<section class="section"><div class="container"><h2>Attendance Data</h2><p style="color:var(--text-muted);">Not loaded.</p></div></section>{get_footer()}'
    
    import urllib.parse as up
    qs = {}; 
    if '?' in _current_path: qs = dict(up.parse_qsl(_current_path.split('?',1)[1]))
    search = qs.get('search','').strip(); sort_by = qs.get('sort','school_year_desc')
    page = max(1,int(qs.get('page','1'))); per_page = min(200,max(10,int(qs.get('per_page','50'))))
    year_filter = qs.get('year','').strip(); district_filter = qs.get('district','').strip()
    
    where = []; params = []
    if search: where.append("(district_name LIKE ? OR district_code LIKE ?)"); params.extend([f'%{search}%',f'%{search}%'])
    if year_filter: where.append("school_year = ?"); params.append(year_filter)
    if district_filter: where.append("district_code = ?"); params.append(district_filter)
    where_clause = ' WHERE ' + ' AND '.join(where) if where else ''
    total = conn.execute(f'SELECT COUNT(*) FROM attendance_data{where_clause}', params).fetchone()[0]
    
    sort_map = {'school_year_desc':'school_year DESC','school_year_asc':'school_year ASC','district_asc':'district_name ASC',
        'attendance_desc':'attendance_rate DESC','attendance_asc':'attendance_rate ASC',
        'absences_desc':'avg_absences DESC','chronic_desc':'chronically_absent_10_pct DESC'}
    order = sort_map.get(sort_by, 'school_year DESC, district_name')
    offset = (page-1)*per_page; total_pages = max(1,(total+per_page-1)//per_page)
    rows = conn.execute(f'SELECT * FROM attendance_data{where_clause} ORDER BY {order} LIMIT ? OFFSET ?', params+[per_page,offset]).fetchall()
    conn.close()
    
    extra = f'''<div style="flex:1;min-width:110px;"><label style="font-size:0.75rem;color:var(--text-muted);display:block;">Year</label><select name="year" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;"><option value="">All</option>'''
    for y in years: extra += f'<option value="{h(y)}" {"selected" if y==year_filter else ""}>{h(y)}</option>'
    extra += '</select></div><div style="flex:1;min-width:150px;"><label style="font-size:0.75rem;color:var(--text-muted);display:block;">District</label><select name="district" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;"><option value="">All</option>'
    for d in districts: extra += f'<option value="{h(d[1])}" {"selected" if d[1]==district_filter else ""}>{h(d[0])}</option>'
    extra += '</select></div>'
    
    sort_opts = '<option value="school_year_desc">Year (Newest)</option><option value="school_year_asc">Year (Oldest)</option><option value="district_asc">District (A-Z)</option><option value="attendance_desc">Attendance % (High)</option><option value="attendance_asc">Attendance % (Low)</option><option value="absences_desc">Absences (High)</option><option value="chronic_desc">Chronic Absent % (High)</option>'
    filter_bar = data_filter_bar('/data/attendance/','District name...',extra).replace('<option value="">Default</option>', f'<option value="">Default</option>{sort_opts}').replace(f'value="{sort_by}"', f'value="{sort_by}" selected')
    
    body = f'{get_head("Attendance Data","Attendance rates, absences, chronic absenteeism.")}{get_header("/data/")}<section class="section"><div class="container">'
    body += f'<div class="hero-stats" style="margin-bottom:1rem;"><div class="stat"><span class="stat-value">{total:,}</span><span class="stat-label">Records</span></div><div class="stat"><span class="stat-value">{len(years)}</span><span class="stat-label">Years</span></div><div class="stat"><span class="stat-value">{len(districts)}</span><span class="stat-label">Districts</span></div><div class="stat"><span class="stat-value">{total_pages}</span><span class="stat-label">Pages</span></div></div>'
    body += '<h2 style="font-size:1.5rem;margin-bottom:0.75rem;">Attendance Data Explorer</h2><p style="color:var(--text-muted);margin-bottom:1rem;">Every metric sortable. Sourced from DESE.</p>'+filter_bar
    if not rows: body += '<div class="empty-state"><p>No records match.</p></div>'
    else:
        body += f'<p style="color:var(--text-muted);font-size:0.8rem;">{offset+1}-{min(offset+per_page,total)} of {total:,}</p>'
        body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>District</th><th>Year</th><th>Attend %</th><th>Avg Absences</th><th>% Absent 10+</th><th>% Chronically Absent</th><th>% Chronic (20%)</th></tr></thead><tbody>'
        for r in rows:
            body += f'<tr><td><strong>{h(r["district_name"])}</strong></td><td>{h(r["school_year"])}</td><td>{h(str(r["attendance_rate"] if "attendance_rate" in r.keys() else "-"))}%</td><td>{h(str(r["avg_absences"] if "avg_absences" in r.keys() else "-"))}</td><td>{h(str(r["absent_10_plus_pct"] if "absent_10_plus_pct" in r.keys() else "-"))}%</td><td>{h(str(r["chronically_absent_10_pct"] if "chronically_absent_10_pct" in r.keys() else "-"))}%</td><td>{h(str(r["chronically_absent_20_pct"] if "chronically_absent_20_pct" in r.keys() else "-"))}%</td></tr>'
        body += '</tbody></table></div>'+pagination_links('/data/attendance/',page,total_pages,qs)
    return body + '<div style="margin-top:1rem;"><a href="/data/" class="btn btn-ghost">&larr; Data Hub</a></div></div></section>'+get_footer()


def handle_sped_results():
    conn = get_db(); conn.row_factory = sqlite3.Row
    # Use sped_data table (seed creates sped_results but we loaded into sped_data)
    table = 'sped_data'
    try:
        conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    except:
        table = 'sped_results'
    try:
        years = [r[0] for r in conn.execute(f"SELECT DISTINCT school_year FROM {table} ORDER BY school_year DESC").fetchall()]
        districts = conn.execute(f"SELECT DISTINCT district_name, district_code FROM {table} ORDER BY district_name").fetchall()
    except: conn.close(); return f'{get_head("SPED Results")}{get_header("/data/")}<section class="section"><div class="container"><h2>SPED Results</h2><p style="color:var(--text-muted);">Not loaded.</p></div></section>{get_footer()}'
    
    import urllib.parse as up
    qs = {}; 
    if '?' in _current_path: qs = dict(up.parse_qsl(_current_path.split('?',1)[1]))
    search = qs.get('search','').strip(); sort_by = qs.get('sort','school_year_desc')
    page = max(1,int(qs.get('page','1'))); per_page = min(200,max(10,int(qs.get('per_page','50'))))
    year_filter = qs.get('year','').strip(); district_filter = qs.get('district','').strip()
    
    where = []; params = []
    if search: where.append("(district_name LIKE ? OR district_code LIKE ?)"); params.extend([f'%{search}%',f'%{search}%'])
    if year_filter: where.append("school_year = ?"); params.append(year_filter)
    if district_filter: where.append("district_code = ?"); params.append(district_filter)
    where_clause = ' WHERE ' + ' AND '.join(where) if where else ''
    total = conn.execute(f'SELECT COUNT(*) FROM {table}{where_clause}', params).fetchone()[0]
    
    sort_map = {'school_year_desc':'school_year DESC','school_year_asc':'school_year ASC','district_asc':'district_name ASC',
        'grad_desc':'sped_grad_rate DESC','dropout_desc':'sped_dropout_rate DESC',
        'inclusion_desc':'lre_full_incl_pct DESC','parent_desc':'parent_involve_pct DESC'}
    order = sort_map.get(sort_by, 'school_year DESC, district_name')
    offset = (page-1)*per_page; total_pages = max(1,(total+per_page-1)//per_page)
    rows = conn.execute(f'SELECT * FROM {table}{where_clause} ORDER BY {order} LIMIT ? OFFSET ?', params+[per_page,offset]).fetchall()
    conn.close()
    
    extra = f'''<div style="flex:1;min-width:110px;"><label style="font-size:0.75rem;color:var(--text-muted);display:block;">Year</label><select name="year" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;"><option value="">All</option>'''
    for y in years: extra += f'<option value="{h(y)}" {"selected" if y==year_filter else ""}>{h(y)}</option>'
    extra += '</select></div><div style="flex:1;min-width:150px;"><label style="font-size:0.75rem;color:var(--text-muted);display:block;">District</label><select name="district" style="width:100%;padding:0.5rem;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:0.8rem;"><option value="">All</option>'
    for d in districts: extra += f'<option value="{h(d[1])}" {"selected" if d[1]==district_filter else ""}>{h(d[0])}</option>'
    extra += '</select></div>'
    
    sort_opts = '<option value="school_year_desc">Year (Newest)</option><option value="school_year_asc">Year (Oldest)</option><option value="district_asc">District (A-Z)</option><option value="grad_desc">Grad Rate (High)</option><option value="dropout_desc">Dropout Rate (High)</option><option value="inclusion_desc">Inclusion % (High)</option><option value="parent_desc">Parent Involve % (High)</option>'
    filter_bar = data_filter_bar('/data/sped-results/','District name...',extra).replace('<option value="">Default</option>', f'<option value="">Default</option>{sort_opts}').replace(f'value="{sort_by}"', f'value="{sort_by}" selected')
    
    body = f'{get_head("SPED Results","SPED graduation, dropout, inclusion, parent involvement.")}{get_header("/data/")}<section class="section"><div class="container">'
    body += f'<div class="hero-stats" style="margin-bottom:1rem;"><div class="stat"><span class="stat-value">{total:,}</span><span class="stat-label">Records</span></div><div class="stat"><span class="stat-value">{len(years)}</span><span class="stat-label">Years</span></div><div class="stat"><span class="stat-value">{len(districts)}</span><span class="stat-label">Districts</span></div><div class="stat"><span class="stat-value">{total_pages}</span><span class="stat-label">Pages</span></div></div>'
    body += '<h2 style="font-size:1.5rem;margin-bottom:0.75rem;">SPED Results Explorer</h2><p style="color:var(--text-muted);margin-bottom:1rem;">Every metric sortable. Sourced from DESE.</p>'+filter_bar
    if not rows: body += '<div class="empty-state"><p>No records match.</p></div>'
    else:
        body += f'<p style="color:var(--text-muted);font-size:0.8rem;">{offset+1}-{min(offset+per_page,total)} of {total:,}</p>'
        body += '<div class="repo-table-wrapper"><table class="repo-table"><thead><tr><th>District</th><th>Year</th><th>Grad Rate</th><th>Dropout Rate</th><th>Full Inclusion %</th><th>Parent Involve %</th></tr></thead><tbody>'
        for r in rows:
            body += f'<tr><td><strong>{h(r["district_name"])}</strong></td><td>{h(r["school_year"])}</td><td>{h(str(r["sped_grad_rate"] if "sped_grad_rate" in r.keys() else "-"))}%</td><td>{h(str(r["sped_dropout_rate"] if "sped_dropout_rate" in r.keys() else "-"))}%</td><td>{h(str(r["lre_full_incl_pct"] if "lre_full_incl_pct" in r.keys() else "-"))}%</td><td>{h(str(r["parent_involve_pct"] if "parent_involve_pct" in r.keys() else "-"))}%</td></tr>'
        body += '</tbody></table></div>'+pagination_links('/data/sped-results/',page,total_pages,qs)
    return body + '<div style="margin-top:1rem;"><a href="/data/" class="btn btn-ghost">&larr; Data Hub</a></div></div></section>'+get_footer()


# SVG category icons for resource sections
_RES_ICONS = {
    'urgent': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>',
    'advocacy-partner': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
    'pdf-tools': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>',
    'government-legal': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"/></svg>',
    'getting-started': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
}

_CAT_ICON = {
    'special-ed': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 14l9-5-9-5-9 5 9 5z"/><path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"/></svg>',
    'public-records': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>',
    'legal': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
    'advocacy-partner': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
    'pdf-tools': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>',
    'district-contact': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>',
}

_SVG_PHONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14"><path d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>'
_SVG_EMAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14"><path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>'
_SVG_EXTERNAL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12"><path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>'
_SVG_BOLT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>'


def handle_resources():
    conn = get_db()

    # ── Filter params ──
    category = ''
    search = ''
    if '?' in _current_path:
        params = urllib.parse.parse_qs(_current_path.split('?', 1)[1])
        category = params.get('category', [''])[0]
        search = params.get('search', [''])[0]

    where = ["r.status = 'active'"]
    db_params = []
    if category and category != 'all':
        where.append('r.category = ?')
        db_params.append(category)
    if search:
        where.append('(r.title LIKE ? OR r.description LIKE ? OR r.tags LIKE ?)')
        st = f'%{search}%'
        db_params.extend([st, st, st])

    where_clause = ' AND '.join(where)
    all_resources = conn.execute(
        f"SELECT * FROM resources r WHERE {where_clause} ORDER BY r.sort_order, r.title",
        db_params
    ).fetchall()

    # Category counts for stats bar
    cat_counts = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM resources WHERE status = 'active' GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    total_active = sum(c['cnt'] for c in cat_counts)
    conn.close()

    # Category labels
    cat_labels = {
        'special-ed': 'Special Education',
        'public-records': 'Public Records',
        'legal': 'Legal',
        'advocacy-partner': 'Advocacy Partners',
        'pdf-tools': 'PDF Tools',
        'district-contact': 'District Contacts',
    }

    # ── Organize into display sections ──
    sections = OrderedDict()
    sections['urgent'] = {'resources': []}
    sections['advocacy-partner'] = {'resources': []}
    sections['pdf-tools'] = {'resources': []}
    sections['government-legal'] = {'resources': []}

    urgent_cats = {'special-ed', 'public-records', 'legal'}
    for r in all_resources:
        cat = r['category']
        if cat in urgent_cats:
            sections['urgent']['resources'].append(r)
        elif cat == 'advocacy-partner':
            sections['advocacy-partner']['resources'].append(r)
        elif cat == 'pdf-tools':
            sections['pdf-tools']['resources'].append(r)
        else:
            sections['government-legal']['resources'].append(r)

    section_labels = {
        'urgent': 'Quick Reference — Save These Numbers',
        'advocacy-partner': 'Advocacy Partners',
        'pdf-tools': 'Parent Data Force Tools',
        'government-legal': 'Government & Legal',
    }
    section_descs = {
        'urgent': 'Crisis contacts and immediate steps. Start here if your child was restrained, records were denied, or you need to file an emergency complaint.',
        'advocacy-partner': 'Organizations and advocates who can help navigate the system. Many offer free or low-cost support.',
        'pdf-tools': 'Templates, checklists, and guides built from real advocacy experience. Free to use and share.',
        'government-legal': 'Official contacts, legal aid, and reference materials for navigating state and federal systems.',
    }

    head = get_head('Resource Center', 'Advocacy tools, crisis contacts, templates, and guidance for Massachusetts families.')
    body = f'''{head}{get_header("/resources/")}<section class="section resources-page"><div class="container">
<div class="section-header"><span class="section-tag">Resource Center</span><h2 class="section-title">Advocacy Resources</h2><p class="section-subtitle">Everything you need to advocate effectively — crisis contacts, templates, partner organizations, and step-by-step guides.</p></div>'''

    # ── Stats bar ──
    body += '<div class="hero-stats" style="margin-bottom:2rem;">'
    body += f'<div class="stat"><span class="stat-value">{total_active}</span><span class="stat-label">Total Resources</span></div>'
    for cc in cat_counts:
        label = cat_labels.get(cc['category'], cc['category'].replace('-', ' ').title())
        body += f'<div class="stat"><span class="stat-value">{cc["cnt"]}</span><span class="stat-label">{label}</span></div>'
    body += '</div>'

    # ── Search + filter bar ──
    body += '<form method="get" class="resources-filters" style="display:flex;gap:0.75rem;flex-wrap:wrap;align-items:center;margin-bottom:2rem;">'
    body += f'<div class="repo-search" style="flex:1;min-width:250px;max-width:450px;"><svg class="repo-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg><input type="text" name="search" class="repo-search-input" placeholder="Search resources..." value="{h(search)}"></div>'
    body += '<div class="resources-cat-filters" style="display:flex;gap:0.4rem;flex-wrap:wrap;">'
    body += f'<a href="?category=all{chr(38)+"search="+urllib.parse.quote(search) if search else ""}" class="filter-btn{" active" if not category or category == "all" else ""}">All</a>'
    for cc in cat_counts:
        active = ' active' if category == cc['category'] else ''
        body += f'<a href="?category={cc["category"]}{chr(38)+"search="+urllib.parse.quote(search) if search else ""}" class="filter-btn{active}">{cat_labels.get(cc["category"], cc["category"])}</a>'
    body += '</div>'
    if search:
        body += f'<a href="?category={category if category and category != "all" else "all"}" class="btn btn-ghost" style="padding:0.5rem 0.75rem;font-size:0.8rem;">Clear</a>'
    body += '<button type="submit" class="btn btn-primary" style="padding:0.56rem 1rem;">Search</button></form>'

    if not all_resources:
        body += '<div class="empty-state"><p>No resources found.</p><a href="?category=all" class="btn btn-secondary" style="margin-top:1rem;">View All Resources</a></div>'
        body += '</div></section>' + get_footer()
        return body

    # ── CRISIS BAR ──
    crisis_items = []
    for r in sections['urgent']['resources']:
        links = []
        if r['phone']:
            links.append(f'<a href="tel:{h(r["phone"])}" class="rl-crisis-btn rl-crisis-phone">{_SVG_PHONE} {h(r["phone"])}</a>')
        if r['url']:
            links.append(f'<a href="{h(r["url"])}" target="_blank" rel="noopener" class="rl-crisis-btn rl-crisis-web">Visit {_SVG_EXTERNAL}</a>')
        if r['email']:
            links.append(f'<a href="mailto:{h(r["email"])}" class="rl-crisis-btn rl-crisis-email">{_SVG_EMAIL} Email</a>')
        icon = _CAT_ICON.get(r['category'], _CAT_ICON['legal'])
        crisis_items.append(f'''<div class="rl-crisis-card">
    <div class="rl-crisis-card-header"><span class="rl-crisis-icon">{icon}</span><h3 class="rl-crisis-title">{h(r["title"])}</h3></div>
    <p class="rl-crisis-desc">{h(str(r["description"] or "")[:120])}</p>
    <div class="rl-crisis-actions">{"".join(links)}</div>
</div>''')

    body += f'''<div class="rl-crisis-bar">
<div class="rl-crisis-bar-header"><span class="rl-crisis-bar-icon">{_SVG_BOLT}</span><h3 class="rl-crisis-bar-title">{section_labels["urgent"]}</h3></div>
<div class="rl-crisis-grid">{"".join(crisis_items)}</div>
</div>'''

    # ── SECTIONED RESOURCE GRID (skip urgent — already in crisis bar) ──
    section_order = ['advocacy-partner', 'pdf-tools', 'government-legal']
    for sec_key in section_order:
        sec_resources = sections[sec_key]['resources']
        if not sec_resources:
            continue
        sec_icon = _RES_ICONS.get(sec_key, _RES_ICONS['pdf-tools'])
        body += f'''<div class="resources-category-section" id="rl-{sec_key}">
<div class="resources-cat-header"><div class="resources-cat-icon">{sec_icon}</div><h3 class="resources-cat-title">{section_labels[sec_key]}</h3><span class="resources-cat-count">{len(sec_resources)} resource{"s" if len(sec_resources) != 1 else ""}</span></div>
<div class="resources-cards">'''

        for r in sec_resources:
            actions = []
            if r['url']:
                is_internal = r['url'].startswith('/')
                label = 'Open Tool' if is_internal else 'Visit Website'
                target = '' if is_internal else ' target="_blank" rel="noopener"'
                ext_icon = '' if is_internal else f' {_SVG_EXTERNAL}'
                actions.append(f'<a href="{h(r["url"])}"{target} class="rl-action-btn rl-action-primary">{label}{ext_icon}</a>')
            if r['phone']:
                actions.append(f'<a href="tel:{h(r["phone"])}" class="rl-action-btn rl-action-phone">{_SVG_PHONE} {h(r["phone"])}</a>')
            if r['email']:
                actions.append(f'<a href="mailto:{h(r["email"])}" class="rl-action-btn rl-action-email">{_SVG_EMAIL} Email</a>')
            if not actions:
                actions.append('<span class="rl-action-btn rl-action-info">Contact for details</span>')

            tags_html = ''
            if r['tags']:
                tags = [t.strip() for t in r['tags'].split(',') if t.strip()]
                tags_html = '<div class="rl-tags">' + ''.join(f'<span class="rl-tag">{h(t)}</span>' for t in tags[:4]) + '</div>'

            body += f'''<div class="resource-detail-card">
    <div class="res-card-body">
        <h4 class="res-card-title">{h(r["title"])}</h4>
        <p class="res-card-desc">{h(str(r["description"] or "")[:200])}</p>
        {tags_html}
    </div>
    <div class="rl-card-actions">{"".join(actions)}</div>
</div>'''

        body += '</div></div>'

    # ── GETTING STARTED GUIDE ──
    start_icon = _RES_ICONS['getting-started']
    body += f'''<div class="rl-section rl-getting-started" id="rl-start">
<div class="rl-section-header"><span class="rl-section-icon">{start_icon}</span><div><h3 class="rl-section-title">Don't Know Where to Start?</h3><p class="rl-section-desc">Every advocacy situation is different. Here are the most common starting points.</p></div></div>
<div class="rl-start-grid">
<div class="rl-start-card"><div class="rl-start-num">1</div><h4>My child was harmed or restrained</h4><p>Contact <strong>DESE PRS</strong> immediately at (781) 338-3700. File a complaint. Then contact <strong>OCR</strong> for federal civil rights violations. Document everything.</p></div>
<div class="rl-start-card"><div class="rl-start-num">2</div><h4>The district denied my records request</h4><p>Appeal to the <strong>Supervisor of Public Records</strong> within 90 days. Use our <strong>PRR Template</strong> for your next request. The SPR can order compliance.</p></div>
<div class="rl-start-card"><div class="rl-start-num">3</div><h4>My child's IEP isn't being followed</h4><p>Contact <strong>DESE PRS</strong> to file a compliance complaint. Bring an advocate to your next IEP meeting. <strong>Team Shawnie</strong> and <strong>FCSN</strong> can help.</p></div>
<div class="rl-start-card"><div class="rl-start-num">4</div><h4>I need an advocate at my IEP meeting</h4><p>Contact <strong>Team Shawnie Advocacy Group</strong> or the <strong>Federation for Children with Special Needs</strong>. Both provide IEP meeting support in Massachusetts.</p></div>
<div class="rl-start-card"><div class="rl-start-num">5</div><h4>I have evidence of systemic problems</h4><p>Use our <strong>PRS Complaint Guide</strong> and <strong>Methodology</strong> to build your case. Submit tips through our <a href="/submit/">intake form</a>. We investigate cross-district patterns.</p></div>
<div class="rl-start-card"><div class="rl-start-num">6</div><h4>I can't afford a lawyer</h4><p>Contact the <strong>Children's Law Center of MA</strong> (781-581-1977) for free legal aid. <strong>Massachusetts Advocates for Children</strong> also provides pro bono support.</p></div>
</div></div>'''

    body += '</div></section>' + get_footer()
    return body


# 
# Request Handler
# 

class PDFHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_ROOT), **kwargs)

    def do_GET(self):
        global _current_path
        _current_path = self.path
        path = self.path
        if '?' in path:
            path = path.split('?')[0]

        if path.startswith('/assets/'):
            return super().do_GET()
        if path == '/favicon.ico':
            self.send_response(404); self.end_headers(); return

        # Admin routes
        admin_user = get_admin_session(self)

        if path == '/admin/' or path == '/admin':
            if not admin_user:
                self.send_response(302); self.send_header('Location', '/admin/login'); self.end_headers(); return
            content = handle_admin_dashboard(admin_user)
        elif path == '/admin/login':
            if admin_user:
                self.send_response(302); self.send_header('Location', '/admin/articles/'); self.end_headers(); return
            handle_admin_login(self); return
        elif path == '/admin/logout':
            self.send_response(302); self.send_header('Location', '/'); self.send_header('Set-Cookie', clear_admin_cookie()); self.end_headers(); return
        elif path.startswith('/admin/articles/'):
            if not admin_user:
                self.send_response(302); self.send_header('Location', '/admin/login'); self.end_headers(); return
            sub = path[len('/admin/articles/'):].strip('/')
            if sub == '' or sub == 'articles':
                content = handle_admin_articles(self, admin_user)
            elif sub == 'new':
                content = handle_admin_articles(self, admin_user, 'new')
            elif sub.startswith('edit/'):
                aid = int(sub.split('/')[1]) if '/' in sub else None
                content = handle_admin_articles(self, admin_user, 'edit', aid) if aid else handle_404()
            else:
                content = handle_404()

        if not locals().get('content'):
            if path == '/data/prr-tracker/' or path == '/data/prr-tracker':
                content = handle_prr_tracker()
            elif path == '/data/public-records/' or path == '/data/public-records':
                content = handle_public_records()
            elif path == '/data/request-catalog/' or path == '/data/request-catalog':
                content = handle_request_catalog()
            elif path == '/data/discipline/' or path == '/data/discipline':
                content = handle_discipline()
            elif path == '/data/enrollment/' or path == '/data/enrollment':
                content = handle_enrollment()
            elif path == '/data/attendance/' or path == '/data/attendance':
                content = handle_attendance()
            elif path == '/data/sped-results/' or path == '/data/sped-results':
                content = handle_sped_results()
            elif path.startswith('/data/restraint/export'):
                handle_restraint_export(self); return
            elif path == '/data/restraint/' or path == '/data/restraint':
                content = handle_restraint_data()
            elif path == '/data/prs/' or path == '/data/prs':
                content = handle_prs_data()
            elif path == '/resources/' or path == '/resources':
                content = handle_resources()

        # Public routes
        if not locals().get('content'):
            if path == '/' or path == '':
                content = handle_home()
            elif path.startswith('/articles/'):
                content = handle_articles(self.path)
            elif path.startswith('/cases/'):
                content = handle_cases(self.path)
            elif path.startswith('/districts/'):
                content = handle_districts(self.path)
            elif path.startswith('/schools/'):
                content = handle_schools(self.path)
            elif path.startswith('/data/'):
                content = handle_data()
            elif path.startswith('/speeches/'):
                content = handle_speeches()
            elif path.startswith('/search/'):
                content = handle_search()
            elif path.startswith('/submit/'):
                content = handle_submit()
            elif path.startswith('/about/'):
                content = handle_about()
            else:
                return super().do_GET()

        if content is None:
            self.send_response(404); self.end_headers(); self.wfile.write(b'Not found'); return

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def do_POST(self):
        path = self.path.split('?')[0]
        admin_user = get_admin_session(self)

        if path == '/admin/login':
            handle_admin_login(self)
            return

        if path.startswith('/admin/articles/'):
            if not admin_user:
                self.send_response(302); self.send_header('Location', '/admin/login'); self.end_headers(); return
            sub = path[len('/admin/articles/'):].strip('/')
            if sub == 'new' or sub == '':
                handle_admin_articles(self, admin_user, 'new' if sub == 'new' else 'list')
                return
            elif sub.startswith('edit/'):
                pass  # handled by same post logic

        # Default: redirect
        self.send_response(302); self.send_header('Location', '/'); self.end_headers(); return

    def log_message(self, format, *args):
        if 'assets' not in str(args[0]):
            print(f"[{datetime.datetime.now():%H:%M:%S]}] {args[0]}")


def main():
    print("=" * 60)
    print("  Parent Data Force v2 - Development Server")
    print("=" * 60)

    # Initialize database
    init_db()  # Always run - CREATE IF NOT EXISTS is safe
    if not DB_PATH.exists():
        print(f"\n  First run - creating database: {DB_PATH}")
        seed_db()
        print("  Database initialized with seed data.")
    else:
        print(f"\n  Using existing database: {DB_PATH}")
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        conn.close()
        if count == 0:
            print("  Seeding sample data...")
            seed_db()

    # Load drive data if available (runs on every start)
    seed_path = ROOT / "backend" / "seed_drive_data.sql"
    if seed_path.exists():
        try:
            prr_count = get_db().execute("SELECT COUNT(*) FROM prr_tracker").fetchone()[0]
        except:
            prr_count = 0
        if prr_count == 0:
            print(f"  Loading drive data: {seed_path}")
            sql_content = seed_path.read_text(encoding="utf-8")
            conn = get_db()
            for stmt in sql_content.replace('\r', '').split(";\n"):
                stmt = stmt.strip()
                if stmt and not stmt.startswith("--"):
                    try:
                        conn.execute(stmt)
                    except Exception as e:
                        if 'UNIQUE' not in str(e) and 'duplicate' not in str(e).lower():
                            pass
            conn.commit()
            conn.close()
            try:
                prr_loaded = get_db().execute("SELECT COUNT(*) FROM prr_tracker").fetchone()[0]
                cat_loaded = get_db().execute("SELECT COUNT(*) FROM aggregate_catalog").fetchone()[0]
                print(f"  Loaded: {prr_loaded} PRR tracker, {cat_loaded} catalog entries")
            except:
                print("  Warning: could not verify loaded counts")

    print(f"\n  Server: http://{HOST}:{PORT}/")
    print(f"  Press Ctrl+C to stop")
    print("=" * 60)

    server = HTTPServer((HOST, PORT), PDFHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        server.server_close()
        if DB_PATH.exists():
            DB_PATH.unlink(missing_ok=True)
            DB_PATH.with_suffix(".db-wal").unlink(missing_ok=True)
            DB_PATH.with_suffix(".db-shm").unlink(missing_ok=True)
        print("  Done.")


if __name__ == '__main__':
    main()

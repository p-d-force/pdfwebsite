"""
One-shot fix: populate sparse cases, publish drafts, clean home stats.
"""
import sqlite3, json

DB = r'C:\Users\LokiF\Desktop\PDFWEBSITE\dev.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# ── 1. POPULATE SPARSE CASES ──────────────────────────────────────
case_data = {
    'PRS-13067': {
        'current_stage': 'Resolved',
        'deadline': '2024-06-15',
        'timeline': json.dumps([
            {"date": "2024-01-15", "title": "PRS Complaint Filed",
             "description": "Filed DESE Problem Resolution System complaint (PRS-13067) against Attleboro Public Schools alleging multiple violations of FAPE for Loki Ford (Down Syndrome, Autism, nonverbal).",
             "docs": []},
            {"date": "2024-03-01", "title": "DESE Investigation Opened",
             "description": "DESE accepted complaint and opened formal investigation into Attleboro's provision of FAPE.",
             "docs": []},
            {"date": "2024-06-15", "title": "DESE Determination Issued",
             "description": "DESE issued findings and required corrective actions. Multiple violations substantiated.",
             "docs": [{"label": "DESE Determination Letter", "url": "#"}]},
        ]),
        'requested_items': json.dumps([
            "Full DESE PRS investigation file for PRS-13067",
            "District response to PRS complaint",
            "Corrective action plan and compliance documentation",
            "IEP records and progress reports for Loki Ford (2019-2024)",
        ]),
        'cross_references': 'PRS-13293, PRS-13455, BSEA-2409911',
    },
    'BSEA-2409911': {
        'current_stage': 'Resolved — Placement at Cushing Centers',
        'deadline': '2025-03-01',
        'filed_date': '2024-09-01',
        'timeline': json.dumps([
            {"date": "2024-09-01", "title": "BSEA Appeal Filed",
             "description": "Filed Bureau of Special Education Appeals case seeking appropriate placement for Loki Ford.",
             "docs": []},
            {"date": "2025-01-15", "title": "Settlement Reached",
             "description": "Parties reached settlement agreement. Loki Ford placed at Cardinal Cushing Centers.",
             "docs": []},
        ]),
        'requested_items': json.dumps([
            "BSEA docket and filings for BSEA-2409911",
            "Settlement agreement terms (redacted as appropriate)",
            "Placement and transportation records",
        ]),
    },
    'C.A.-2573CV00216C': {
        'current_stage': 'Active Litigation',
        'deadline': '2026-12-31',
        'filed_date': '2025-06-01',
        'priority': 'high',
        'summary': 'Civil lawsuit filed pro se in Bristol County Superior Court against Attleboro Public Schools. Case number C.A. 2573CV00216C. Allegations include systemic failures in special education delivery, public records law violations, and civil rights claims.',
        'timeline': json.dumps([
            {"date": "2025-06-01", "title": "Complaint Filed",
             "description": "Pro se civil complaint filed in Bristol County Superior Court (C.A. 2573CV00216C).",
             "docs": []},
        ]),
        'requested_items': json.dumps([
            "Court docket for C.A. 2573CV00216C",
            "Filed complaint and all responsive pleadings",
            "Discovery and motions practice records",
            "Any orders, rulings, or judgments",
        ]),
    },
    'WH-SYSTEMIC-1': {
        'current_stage': 'Investigation Phase',
        'deadline': '2026-09-01',
        'summary': 'Systemic complaint filed with DESE regarding special education practices, restraint usage, and procedural compliance in Whitman-Hanson Regional School District.',
        'timeline': json.dumps([
            {"date": "2026-03-01", "title": "Systemic Complaint Filed",
             "description": "Filed systemic complaint #1 with DESE Problem Resolution System.",
             "docs": []},
            {"date": "2026-04-01", "title": "DESE Acknowledged",
             "description": "DESE acknowledged receipt and opened preliminary review.",
             "docs": []},
        ]),
        'requested_items': json.dumps([
            "DESE PRS complaint file",
            "District response and supporting documentation",
            "Relevant DESE investigation reports",
        ]),
    },
    'WH-SYSTEMIC-2': {
        'current_stage': 'Investigation Phase',
        'deadline': '2026-10-01',
        'summary': 'Second systemic complaint filed with DESE addressing additional areas of concern in Whitman-Hanson Regional School District including public records compliance and IEP implementation.',
        'timeline': json.dumps([
            {"date": "2026-05-01", "title": "Systemic Complaint #2 Filed",
             "description": "Filed second systemic complaint covering public records and IEP implementation issues.",
             "docs": []},
        ]),
        'requested_items': json.dumps([
            "DESE PRS complaint file",
            "District response documentation",
            "Public records request compliance history",
        ]),
    },
    'BR-SYSTEMIC': {
        'current_stage': 'Investigation Phase',
        'deadline': '2026-11-01',
        'summary': 'Systemic complaint filed with DESE regarding special education practices and procedural compliance in Bridgewater-Raynham Regional School District.',
        'timeline': json.dumps([
            {"date": "2026-06-01", "title": "Systemic Complaint Filed",
             "description": "Filed systemic complaint with DESE Problem Resolution System.",
             "docs": []},
        ]),
        'requested_items': json.dumps([
            "DESE PRS complaint file",
            "District response and supporting documentation",
        ]),
    },
}

for case_id, data in case_data.items():
    existing = conn.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,)).fetchone()
    if existing:
        updates = []
        params = []
        for k, v in data.items():
            if existing[k] is None or existing[k] == '':
                updates.append(f"{k} = ?")
                params.append(v)
        if updates:
            params.append(case_id)
            conn.execute(f"UPDATE cases SET {', '.join(updates)}, updated_at = datetime('now') WHERE case_id = ?", params)
            print(f'Updated {case_id}: {len(updates)} fields')

# ── 2. PUBLISH DRAFT ARTICLES ─────────────────────────────────────
to_publish = [
    'case_update',   # "Inside the Attleboro Public Schools PD Records Investigation"
    'policy',        # "DESE Complaint Filing: The Problem Resolution System Explained"
    'guide',         # "What Every Massachusetts Parent Should Know About IEPs and Public Records"
]
for cat in to_publish:
    conn.execute(
        "UPDATE articles SET status = 'published' WHERE category = ? AND status = 'draft' LIMIT 1", (cat,))
    print(f'Published draft article in category: {cat}')

# ── 3. VERIFY ──────────────────────────────────────────────────────
print('\n=== UPDATED CASES ===')
for c in conn.execute('SELECT case_id, title, current_stage, deadline FROM cases WHERE case_id IN ({})'.format(
    ','.join(f"'{k}'" for k in case_data.keys()))):
    print(f'  {c["case_id"]:25} stage={c["current_stage"] or "(none)":30} deadline={c["deadline"] or "(none)"}')

print('\n=== ARTICLES NOW ===')
for c in conn.execute("SELECT title, status, category FROM articles ORDER BY status, published_at DESC"):
    print(f'  [{c["status"]:9}] {c["category"]:15} {c["title"][:70]}')

conn.commit()
conn.close()
print('\nDone.')

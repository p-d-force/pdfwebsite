"""
DESE Restraint Data Fetcher — Socrata API (Views endpoint)
============================================================
Source: https://educationtocareer.data.mass.gov/api/views/3ss8-pnvb/rows.json
Returns ALL 7,914 rows in a single request — no pagination needed.

Usage:
  python scripts/fetch_dese_restraints_socrata.py              # Fetch & import to Firestore
"""

import sys, os, json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

API_URL = 'https://educationtocareer.data.mass.gov/api/views/3ss8-pnvb/rows.json'
APP_TOKEN = 'YHYVhNle8qBzgdh5iFLugsukm'


def fetch_all():
    """Fetch all data with app token authentication."""
    import requests
    print("Fetching from educationtocareer.data.mass.gov ...", end=" ", flush=True)
    headers = {'X-App-Token': APP_TOKEN}
    try:
        r = requests.get(API_URL, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        rows = data.get('data', [])
        print(f"{len(rows):,} rows ({len(r.text)/1024:.0f}kb)")
        return rows
    except Exception as e:
        print(f"FAILED: {e}")
        return []


def parse_row(row):
    """Parse a Socrata row array into a structured dict."""
    def num(val, default=0):
        if val is None or val == '':
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default
    
    sy = str(row[8]).strip() if len(row) > 8 else ''
    if sy.isdigit() and len(sy) == 4:
        y = int(sy)
        sy = f"{y-1}-{str(y)[-2:]}"
    
    return {
        'school_year': sy,
        'district_code': str(row[9]).strip() if len(row) > 9 else '',
        'district_name': str(row[10]).strip() if len(row) > 10 else '',
        'school_code': str(row[11]).strip() if len(row) > 11 else '',
        'school_name': str(row[12]).strip() if len(row) > 12 else '',
        'org_type': str(row[13]).strip() if len(row) > 13 else '',
        'enrollment': num(row[14]) if len(row) > 14 else 0,
        'students_restrained': num(row[15]) if len(row) > 15 else 0,
        'total_restraints': num(row[16]) if len(row) > 16 else 0,
        'total_injuries': num(row[17]) if len(row) > 17 else 0,
    }


def import_to_firestore(rows):
    """Parse and import all rows into Firestore, joining with enrollment demographics."""
    from backend.firestore_client import FirestoreClient
    
    db = FirestoreClient()
    
    # Load enrollment index
    enr_path = Path(__file__).resolve().parent.parent / 'data' / 'enrollment_index.json'
    enrollment = {}
    if enr_path.exists():
        with open(enr_path) as f:
            raw = json.load(f)
            enrollment = {tuple(k.split('|')): v for k, v in raw.items()}
        print(f"Enrollment index loaded: {len(enrollment):,} keys")
    else:
        print("WARNING: No enrollment index. Run fetch_dese_enrollment_socrata.py first.")
    
    ENRICH_FIELDS = ['swd_pct', 'li_pct', 'el_pct', 'hn_pct', 'ecd_pct',
                     'wh_pct', 'baa_pct', 'hl_pct', 'as_pct', 'fe_pct', 'ma_pct']
    
    old_count = len(db.get_all('restraint_data', limit=1))
    print(f"Current Firestore docs: {old_count}")
    
    docs = []
    year_totals = defaultdict(lambda: {'s': 0, 'r': 0, 'st': 0, 'inj': 0})
    joined = 0
    
    for row in rows:
        doc = parse_row(row)
        org_type = doc.pop('org_type', '')
        
        if org_type == 'State':
            continue
        
        enrollment_val = doc.get('enrollment', 0)
        total_restr = doc.get('total_restraints', 0)
        
        # Join with enrollment demographics
        sy = doc.get('school_year', '')
        sc = doc.get('school_code', '')
        enr_key = (sy, sc)
        if enr_key in enrollment:
            enr_data = enrollment[enr_key]
            for f in ENRICH_FIELDS:
                val = enr_data.get(f)
                if val is not None:
                    doc[f] = val
            joined += 1
        
        # Calculate rates
        rate = round((total_restr / enrollment_val) * 100, 4) if enrollment_val > 0 else None
        total_inj = doc.get('total_injuries', 0)
        ipr = round(total_inj / total_restr, 4) if total_restr > 0 and total_inj > 0 else None
        inj_rate = round((total_inj / enrollment_val) * 100, 2) if enrollment_val > 0 else None
        
        doc['restraint_rate_per_100'] = rate
        doc['injuries_per_restraint'] = ipr
        doc['injury_rate_per_100'] = inj_rate
        doc['is_summary_row'] = 1 if org_type == 'District' else 0
        doc['source_workbook'] = 'DESE Socrata API'
        doc['visibility'] = 'active'
        
        doc['_id'] = f"{sc}_{sy}" if sc and sy else None
        docs.append(doc)
        
        if org_type != 'District' and enrollment_val > 0:
            year_totals[sy]['s'] += 1
            year_totals[sy]['r'] += total_restr
            year_totals[sy]['st'] += doc.get('students_restrained', 0)
            year_totals[sy]['inj'] += total_inj
    
    print(f"Parsed {len(docs):,} documents ({joined:,} enriched with demographics)")
    
    print("\nYear-over-year data:")
    print(f"{'Year':<10} {'Schools':>8} {'Restraints':>12} {'Students':>10} {'Injuries':>9}")
    for y in sorted(year_totals.keys()):
        t = year_totals[y]
        print(f"{y:<10} {t['s']:>8} {t['r']:>12,} {t['st']:>10,} {t['inj']:>9,}")
    
    print("\nClearing old restraint data...")
    db.delete_collection('restraint_data')
    
    print(f"Writing {len(docs):,} documents to Firestore...")
    db.batch_write('restraint_data', docs)
    
    verify = db.get_all('restraint_data', order_by='school_year', limit=3)
    print(f"\nSample from Firestore:")
    for d in verify:
        sped = d.get('swd_pct', '?')
        li = d.get('li_pct', '?')
        print(f"  {d.get('school_year')} | {str(d.get('school_name',''))[:35]} | restr={d.get('total_restraints')} | SPED={sped}% LI={li}%")
    
    print(f"\nDone! {len(docs):,} enriched records in Firestore.")
    print("Refresh the sheet: python scripts/sheets_sync.py")


def main():
    print("=" * 60)
    print("  DESE Restraint Data — Socrata API")
    print("  Source: educationtocareer.data.mass.gov")
    print("=" * 60)
    
    rows = fetch_all()
    if not rows:
        print("No data fetched. Exiting.")
        sys.exit(1)
    
    import_to_firestore(rows)


if __name__ == '__main__':
    main()

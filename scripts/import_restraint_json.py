"""
Import restraint data from analytics JSON into Firestore.
Uses restraint_school_year.json (real per-year data from Excel workbooks).

Usage:
  python scripts/import_restraint_json.py
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.firestore_client import FirestoreClient

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'restraint_school_year.json')


def extract_value(val, default=0):
    """Handle values that can be int, float, dict with 'reported' key, or None."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, dict):
        inner = val.get('reported', default)
        if inner == 'suppressed' or inner is None:
            return default
        try:
            return int(inner)
        except (ValueError, TypeError):
            try:
                return float(inner)
            except (ValueError, TypeError):
                return default
    return default


def is_suppressed(val):
    """Check if a value is suppressed."""
    if val is None:
        return False
    if isinstance(val, dict):
        return val.get('suppressed', False) or val.get('reported') == 'suppressed'
    return False


def main():
    print("=" * 60)
    print("  Import Restraint Data from JSON -> Firestore")
    print("=" * 60)
    
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: {DATA_FILE} not found")
        sys.exit(1)
    
    with open(DATA_FILE, encoding='utf-8') as f:
        raw = json.load(f)
    
    records = raw.get('records', [])
    print(f"Loaded {len(records):,} records")
    
    db = FirestoreClient()
    
    # Delete old restraint data
    print("Clearing old restraint data...")
    db.delete_collection('restraint_data')
    
    batch = []
    imported = 0
    skipped = 0
    from collections import defaultdict
    year_totals = defaultdict(lambda: {'schools': 0, 'r': 0, 'st': 0, 'inj': 0})
    
    for record in records:
        if record.get('isSummaryRow'):
            skipped += 1
            continue
        
        school_code = str(record.get('schoolCode', ''))
        school_year = record.get('schoolYear', '')
        
        # Skip records without school code or year
        if not school_code or not school_year:
            skipped += 1
            continue
        
        total_restr = extract_value(record.get('totalRestraints'), 0)
        students_restr = extract_value(record.get('studentsRestrained'), 0)
        total_inj = extract_value(record.get('totalInjuries'), 0)
        enrollment = extract_value(record.get('enrollment'), 0)
        
        # Calculate rate if not present
        rate = None
        raw_rate = record.get('restraintRatePer100')
        if raw_rate:
            rate = extract_value(raw_rate, None)
        elif enrollment > 0 and total_restr > 0:
            rate = round((total_restr / enrollment) * 100, 4)
        
        # Injuries per restraint
        ipr = None
        if total_restr > 0 and total_inj > 0:
            ipr = round(total_inj / total_restr, 4)
        
        doc = {
            '_id': f"{school_code}_{school_year}",
            'school_year': school_year,
            'district_name': str(record.get('districtName', '')),
            'district_code': str(record.get('districtCode', '')),
            'school_name': str(record.get('schoolName', '')),
            'school_code': school_code,
            'enrollment': enrollment,
            'students_restrained': students_restr,
            'students_restrained_suppressed': 1 if is_suppressed(record.get('studentsRestrained')) else 0,
            'total_restraints': total_restr,
            'total_restraints_suppressed': 1 if is_suppressed(record.get('totalRestraints')) else 0,
            'total_injuries': total_inj,
            'total_injuries_suppressed': 1 if is_suppressed(record.get('totalInjuries')) else 0,
            'restraint_rate_per_100': rate,
            'injuries_per_restraint': ipr,
            'is_summary_row': 0,
            'source_workbook': str(record.get('sourceWorkbook', '')),
            'visibility': 'active',
        }
        
        year_totals[school_year]['schools'] += 1
        year_totals[school_year]['r'] += total_restr
        year_totals[school_year]['st'] += students_restr
        year_totals[school_year]['inj'] += total_inj
        
        batch.append(doc)
        imported += 1
        
        if len(batch) >= 500:
            db.batch_write('restraint_data', batch)
            print(f"  {imported:,}/{len(records):,} written...")
            batch = []
    
    if batch:
        db.batch_write('restraint_data', batch)
    
    print(f"\nImported: {imported:,} records, Skipped: {skipped:,}")
    print("\nYear totals:")
    for y in sorted(year_totals.keys()):
        t = year_totals[y]
        print(f"  {y}: {t['schools']} schools, {t['r']:,} restraints, {t['st']:,} students, {t['inj']:,} injuries")
    
    # Verify
    print("\nSample from Firestore:")
    docs = db.get_all('restraint_data', limit=3)
    for d in docs:
        suppressed = d.get('total_restraints_suppressed', 0)
        tr = d.get('total_restraints', 0)
        print(f"  {d.get('school_year')} | {str(d.get('school_name',''))[:40]} | {'<6' if suppressed else tr}")
    
    print(f"\nRefresh the sheet with: python scripts/sheets_sync.py")


if __name__ == '__main__':
    main()

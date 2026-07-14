"""
DESE Enrollment Demographics Fetcher — Socrata API
===================================================
Source: https://educationtocareer.data.mass.gov/api/views/t8td-gens/rows.json
Fields: School-level enrollment, race %, gender %, SPED %, Low Income %, EL %, etc.

Usage:
  python scripts/fetch_dese_enrollment_socrata.py
"""

import sys, os, json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

API_URL = 'https://educationtocareer.data.mass.gov/api/views/t8td-gens/rows.json'
APP_TOKEN = 'YHYVhNle8qBzgdh5iFLugsukm'

FIELD_MAP = {
    8: 'school_year',       # SY
    9: 'district_code',     # DIST_CODE
    10: 'district_name',    # DIST_NAME
    11: 'org_code',         # ORG_CODE
    12: 'org_name',         # ORG_NAME
    13: 'org_type',         # ORG_TYPE
    14: 'total_cnt',        # TOTAL_CNT
    # Demographics percentages
    30: 'aian_pct',         # Native American %
    31: 'as_pct',           # Asian %
    32: 'baa_pct',          # Black %
    33: 'hl_pct',           # Hispanic/Latino %
    34: 'mnh_pct',          # Multi-Race %
    35: 'nhpi_pct',         # Pacific Islander %
    36: 'wh_pct',           # White %
    37: 'fe_pct',           # Female %
    38: 'ma_pct',           # Male %
    # Selected populations
    41: 'el_pct',           # English Learners %
    45: 'hn_pct',           # High Needs %
    47: 'li_pct',           # Low Income %
    49: 'ecd_pct',          # Economically Disadvantaged %
    51: 'swd_pct',          # Students with Disabilities %
}


def fetch_all():
    import requests
    print("Fetching enrollment demographics from Socrata...", end=" ", flush=True)
    headers = {'X-App-Token': APP_TOKEN}
    try:
        r = requests.get(API_URL, headers=headers, timeout=120)
        r.raise_for_status()
        data = r.json()
        rows = data.get('data', [])
        print(f"{len(rows):,} rows ({len(r.text)/1024:.0f}kb)")
        return rows
    except Exception as e:
        print(f"FAILED: {e}")
        return []


def parse_row(row):
    def pct(val):
        if val is None or val == '':
            return None
        try:
            v = float(val)
            # Values in 0-1 range: convert to 0-100
            return round(v * 100, 1) if abs(v) <= 1 else round(v, 1)
        except (ValueError, TypeError):
            return None
    
    def num(val):
        if val is None or val == '':
            return 0
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0
    
    result = {}
    for idx, field_name in FIELD_MAP.items():
        if idx < len(row):
            val = row[idx]
            if field_name.endswith('_pct') or field_name.endswith('_cnt'):
                if field_name.endswith('_pct'):
                    result[field_name] = pct(val)
                else:
                    result[field_name] = num(val)
            else:
                result[field_name] = str(val).strip() if val else ''
    
    # Convert year format
    sy = result.get('school_year', '')
    if sy.isdigit() and len(sy) == 4:
        y = int(sy)
        result['school_year'] = f"{y-1}-{str(y)[-2:]}"
    
    return result


def build_index(rows):
    """Build lookup index by (school_year, org_code) for fast joins."""
    index = {}
    for row in rows:
        doc = parse_row(row)
        key = (doc.get('school_year', ''), doc.get('org_code', ''))
        if key[0] and key[1]:
            index[key] = doc
    return index


def join_with_restraint(restraint_rows, enrollment_index):
    """Join restraint data with enrollment demographics."""
    enriched = []
    joined = 0
    missed = 0
    
    for rdoc in restraint_rows:
        sy = rdoc.get('school_year', '')
        sc = rdoc.get('school_code', '')
        key = (sy, sc)
        
        if key in enrollment_index:
            enrich = enrollment_index[key]
            for f in ['swd_pct', 'li_pct', 'el_pct', 'hn_pct', 'ecd_pct',
                      'fe_pct', 'ma_pct', 'wh_pct', 'baa_pct', 'hl_pct',
                      'as_pct', 'aian_pct', 'nhpi_pct', 'mnh_pct']:
                if enrich.get(f) is not None:
                    rdoc[f] = enrich[f]
            joined += 1
        else:
            missed += 1
        
        enriched.append(rdoc)
    
    print(f"Join: {joined} enriched, {missed} missed")
    return enriched


def main():
    print("=" * 60)
    print("  DESE Enrollment Demographics — Socrata API")
    print("=" * 60)
    
    rows = fetch_all()
    if not rows:
        print("No data fetched.")
        return
    
    # Build index
    enr_index = build_index(rows)
    print(f"Enrollment index: {len(enr_index):,} unique (year, school) keys")
    
    # Save index for later use
    output_path = Path(__file__).resolve().parent.parent / 'data' / 'enrollment_index.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({f"{k[0]}|{k[1]}": v for k, v in enr_index.items()}, f)
    print(f"Index saved to {output_path} ({output_path.stat().st_size:,} bytes)")
    
    # Show sample
    if enr_index:
        sample_key = list(enr_index.keys())[0]
        sample = enr_index[sample_key]
        print(f"\nSample: {sample_key}")
        for k, v in sorted(sample.items()):
            if v is not None and v != 0 and v != '':
                print(f"  {k}: {v}")
    
    print("\nUse this index in fetch_dese_restraints_socrata.py to join data.")


if __name__ == '__main__':
    main()

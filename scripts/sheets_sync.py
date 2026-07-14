"""
Google Sheets ↔ Firestore Sync
================================
One-way sync: Firestore → Google Sheets (read-only view)
With Apps Script for bidirectional editing (optional).

Usage:
  python scripts/sheets_sync.py              # Firestore → Sheets
  python scripts/sheets_sync.py --reverse    # Sheets → Firestore (reads changes)
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from backend.firestore_client import FirestoreClient

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Collection tab configuration: (collection_name, tab_title, columns, id_column)
COLLECTIONS = [
    ('districts', 'Districts', ['code', 'name', 'location', 'description', 'dese_code', 'status'], 'code'),
    ('cases', 'Cases', ['case_id', 'district_code', 'type', 'title', 'summary', 'status', 'current_stage', 'priority', 'filed_date', 'deadline'], 'case_id'),
    ('articles', 'Articles', ['slug', 'title', 'excerpt', 'category', 'status', 'featured', 'author', 'read_time', 'published_at'], 'slug'),
    ('restraint_data', 'Restraint Data', ['school_year', 'district_name', 'district_code', 'school_name', 'school_code', 'enrollment', 'students_restrained', 'total_restraints', 'total_injuries', 'restraint_rate_per_100', 'injuries_per_restraint', 'is_summary_row'], '_id'),
    ('resources', 'Resources', ['title', 'description', 'url', 'phone', 'email', 'category', 'tags', 'status', 'sort_order'], '_id'),
    ('config', 'Config', ['config_key', 'config_value'], 'config_key'),
]


def get_sheets_service():
    token_path = os.path.expandvars(r'%LOCALAPPDATA%\hermes\google_token.json')
    if not os.path.exists(token_path):
        # Try firebase key path
        token_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '')
        if not token_path:
            raise RuntimeError("No Google credentials found")
        with open(token_path) as f:
            data = json.load(f)
        creds = Credentials(
            token=None,
            refresh_token=None,
            token_uri=data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=data.get('client_id', ''),
            client_secret=data.get('client_secret', ''),
            scopes=SCOPES,
        )
    else:
        with open(token_path) as f:
            data = json.load(f)
        creds = Credentials(
            token=data.get('token'),
            refresh_token=data.get('refresh_token'),
            token_uri=data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=data.get('client_id', ''),
            client_secret=data.get('client_secret', ''),
            scopes=data.get('scopes', SCOPES),
        )
    
    if creds.expired or not creds.token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    
    return build('sheets', 'v4', credentials=creds)


def firestore_to_sheets(fs_db, sheets_service, spreadsheet_id=None):
    """Sync all Firestore collections to Google Sheets tabs."""
    if spreadsheet_id:
        ss_id = spreadsheet_id
    else:
        # Create new spreadsheet
        ss = sheets_service.spreadsheets().create(body={
            'properties': {'title': 'Parent Data Force - Data Manager'},
            'sheets': [{'properties': {'title': c[1]}} for c in COLLECTIONS]
        }).execute()
        ss_id = ss['spreadsheetId']
        print(f"Created spreadsheet: https://docs.google.com/spreadsheets/d/{ss_id}")
    
    for col_name, tab_title, columns, id_col in COLLECTIONS:
        print(f"  Syncing {tab_title} ({col_name})...")
        docs = fs_db.get_all(col_name)
        
        # Build rows: header row + data rows
        rows = [columns]  # header
        for doc in docs:
            row = [str(doc.get(c, '')) for c in columns]
            rows.append(row)
        
        if not rows:
            print(f"    No data for {tab_title}, skipping")
            continue
        
        # Clear and write
        sheet_range = f"'{tab_title}'!A1"
        try:
            sheets_service.spreadsheets().values().clear(
                spreadsheetId=ss_id, range=sheet_range
            ).execute()
        except HttpError:
            pass  # Sheet doesn't exist yet
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=ss_id,
            range=sheet_range,
            valueInputOption='RAW',
            body={'values': rows}
        ).execute()
        
        # Format header row bold
        sheet_id = None
        ss_meta = sheets_service.spreadsheets().get(spreadsheetId=ss_id).execute()
        for s in ss_meta['sheets']:
            if s['properties']['title'] == tab_title:
                sheet_id = s['properties']['sheetId']
                break
        
        if sheet_id is not None:
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=ss_id, body={
                'requests': [
                    {'repeatCell': {
                        'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 1},
                        'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}},
                        'fields': 'userEnteredFormat.textFormat.bold'
                    }},
                    {'autoResizeDimensions': {
                        'dimensions': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': len(columns)}
                    }}
                ]
            }).execute()
        
        print(f"    {len(docs):,} rows written")
    
    print(f"\nSheet URL: https://docs.google.com/spreadsheets/d/{ss_id}")
    return ss_id


def sheets_to_firestore(fs_db, sheets_service, spreadsheet_id):
    """Read all tabs from Google Sheets and write back to Firestore."""
    ss_meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    tab_names = [s['properties']['title'] for s in ss_meta['sheets']]
    
    tab_to_col = {c[1]: (c[0], c[2]) for c in COLLECTIONS}
    
    for tab in tab_names:
        if tab not in tab_to_col:
            print(f"  Skipping unknown tab: {tab}")
            continue
        
        col_name, columns = tab_to_col[tab]
        print(f"  Reading {tab} ({col_name})...")
        
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=f"'{tab}'"
        ).execute()
        
        values = result.get('values', [])
        if not values or len(values) < 2:
            print(f"    No data rows")
            continue
        
        headers = values[0]
        header_idx = {h: i for i, h in enumerate(headers) if h in columns}
        
        docs = []
        for row in values[1:]:
            doc = {}
            for col, idx in header_idx.items():
                if idx < len(row):
                    val = row[idx].strip()
                    if val:
                        # Try to parse numbers
                        try:
                            if '.' in val:
                                val = float(val)
                            else:
                                val = int(val)
                        except (ValueError, TypeError):
                            pass
                    else:
                        val = None
                    doc[col] = val
            if doc:
                docs.append(doc)
        
        # Write to Firestore
        batch = []
        for doc in docs:
            doc_id = doc.get('_id') or doc.get('case_id') or doc.get('slug') or doc.get('code') or doc.get('config_key')
            if doc_id:
                doc.pop('_id', None)  # Remove internal id
                doc['_id'] = str(doc_id)
                batch.append(doc)
        
        fs_db.batch_write(col_name, batch)
        print(f"    {len(batch)} documents written to Firestore")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Google Sheets ↔ Firestore Sync')
    parser.add_argument('--reverse', action='store_true', help='Sheets → Firestore direction')
    parser.add_argument('--sheet-id', help='Existing spreadsheet ID (skips creation)')
    parser.add_argument('--save-id', action='store_true', help='Save sheet ID for reuse')
    args = parser.parse_args()
    
    print("=" * 50)
    print("  PDF Website - Sheets / Firestore Sync")
    print("=" * 50)
    
    sheets_service = get_sheets_service()
    fs_db = FirestoreClient()
    
    if args.reverse:
        if not args.sheet_id:
            print("ERROR: --sheet-id required for reverse sync")
            sys.exit(1)
        sheets_to_firestore(fs_db, sheets_service, args.sheet_id)
    else:
        ss_id = firestore_to_sheets(fs_db, sheets_service, args.sheet_id)
        if args.save_id:
            config_path = os.path.join(os.path.dirname(__file__), '..', '.env')
            with open(config_path, 'a') as f:
                f.write(f'\nSHEETS_SPREADSHEET_ID={ss_id}\n')
            print(f"Sheet ID saved to .env")


if __name__ == '__main__':
    main()

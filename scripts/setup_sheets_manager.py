"""
Google Sheets Manager — Setup + Deploy
=======================================
Sets up the Parent Data Force Google Sheet with:
- Status columns + dropdown validation (active/draft/deleted)
- Action checkboxes for bulk operations  
- Apps Script deployment with menu items
- Controls sheet with action buttons

Usage:
  python scripts/setup_sheets_manager.py
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from backend.firestore_client import FirestoreClient
from scripts.sheets_sync import get_sheets_service, COLLECTIONS, firestore_to_sheets

SCRIPT_ID = None  # will be populated after creation

APPS_SCRIPT_CODE = r"""
// Parent Data Force — Sheet Manager Script
var SPREADSHEET_ID = '{spreadsheet_id}';
var PROJECT_ID = 'steel-mantra-493704-f9';

var TAB_MAP = {
  'Districts':       {{ collection: 'districts',      idCol: 0 }},
  'Cases':           {{ collection: 'cases',          idCol: 0 }},
  'Articles':        {{ collection: 'articles',       idCol: 0 }},
  'Restraint Data':  {{ collection: 'restraint_data', idCol: 2 }},
  'Resources':       {{ collection: 'resources',      idCol: 0 }},
  'Config':          {{ collection: 'config',          idCol: 0 }},
};

function onOpen() {{
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('Data Manager')
    .addItem('Sync Changes to Firestore', 'syncChanges')
    .addSeparator()
    .addItem('Hide Selected Rows', 'hideSelected')
    .addItem('Unhide All in Tab', 'unhideAll')
    .addItem('Delete Selected Rows', 'deleteSelected')
    .addSeparator()
    .addItem('Refresh from Firestore', 'showRefreshInstructions')
    .addToUi();
}}

function syncChanges() {{
  var ui = SpreadsheetApp.getUi();
  var sheet = SpreadsheetApp.getActiveSheet();
  var tabName = sheet.getName();
  var config = TAB_MAP[tabName];
  if (!config) {{ ui.alert('No Firestore mapping for tab: ' + tabName); return; }}
  
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) return;
  var headers = data[0];
  var statusCol = headers.indexOf('status');
  var actionCol = headers.indexOf('action');
  var changes = 0;
  
  for (var i = 1; i < data.length; i++) {{
    var row = data[i];
    var docId = String(row[config.idCol]).trim();
    if (!docId) continue;
    
    // Only sync rows with action checkbox checked (if action column exists)
    if (actionCol >= 0 && row[actionCol] !== true) continue;
    
    var fields = {{}};
    for (var j = 0; j < headers.length; j++) {{
      var key = String(headers[j]).trim();
      var val = row[j];
      if (key === 'action' || key === '') continue;
      if (val === '' || val === undefined || val === null) continue;
      fields[key] = typeof val === 'number' ? {{ 'stringValue': String(val) }} : {{ 'stringValue': String(val) }};
    }}
    
    if (Object.keys(fields).length === 0) continue;
    
    var url = 'https://firestore.googleapis.com/v1/projects/' + PROJECT_ID +
              '/databases/(default)/documents/' + config.collection + '/' + encodeURIComponent(docId) +
              '?updateMask.fieldPaths=' + Object.keys(fields).join('&updateMask.fieldPaths=');
    
    var options = {{
      method: 'PATCH',
      headers: {{ 'Authorization': 'Bearer ' + ScriptApp.getOAuthToken() }},
      contentType: 'application/json',
      payload: JSON.stringify({{ fields: fields }}),
      muteHttpExceptions: true
    }};
    
    try {{
      var resp = UrlFetchApp.fetch(url, options);
      if (resp.getResponseCode() < 300) changes++;
    }} catch (e) {{ console.log('Error row ' + (i+1) + ': ' + e); }}
  }}
  
  // Clear action checkboxes
  if (actionCol >= 0) {{
    var lastRow = sheet.getLastRow();
    for (var i = 1; i <= lastRow; i++) {{
      var cell = sheet.getRange(i + 1, actionCol + 1);
      if (cell.getValue() === true) cell.setValue(false);
    }}
  }}
  
  ui.alert('Synced ' + changes + ' changes to Firestore!');
}}

function hideSelected() {{
  var ui = SpreadsheetApp.getUi();
  var sheet = SpreadsheetApp.getActiveSheet();
  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var actionCol = headers.indexOf('action');
  var statusCol = headers.indexOf('status');
  
  if (actionCol < 0) {{ ui.alert('No "action" column found. Add it via the Controls sheet.'); return; }}
  if (statusCol < 0) {{ ui.alert('No "status" column found. Add it via the Controls sheet.'); return; }}
  
  var hidden = 0;
  for (var i = data.length - 1; i >= 1; i--) {{
    if (data[i][actionCol] === true) {{
      sheet.getRange(i + 1, statusCol + 1).setValue('hidden');
      hidden++;
    }}
  }}
  ui.alert(hidden + ' rows marked as hidden. Click "Sync Changes" to save to Firestore.');
}}

function unhideAll() {{
  var ui = SpreadsheetApp.getUi();
  var sheet = SpreadsheetApp.getActiveSheet();
  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var statusCol = headers.indexOf('status');
  if (statusCol < 0) {{ ui.alert('No status column found.'); return; }}
  
  var unhidden = 0;
  for (var i = 1; i < data.length; i++) {{
    var cell = sheet.getRange(i + 1, statusCol + 1);
    if (cell.getValue() === 'hidden' || cell.getValue() === 'deleted') {{
      cell.setValue('active');
      unhidden++;
    }}
  }}
  ui.alert(unhidden + ' rows set back to active.');
}}

function deleteSelected() {{
  var ui = SpreadsheetApp.getUi();
  var resp = ui.alert('Permanently Delete?', 'This will mark selected rows as "deleted" in Firestore. They can be recovered via the Python sync script.', ui.ButtonSet.OK_CANCEL);
  if (resp !== ui.Button.OK) return;
  
  var sheet = SpreadsheetApp.getActiveSheet();
  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var actionCol = headers.indexOf('action');
  var statusCol = headers.indexOf('status');
  
  if (actionCol < 0) {{ ui.alert('No action column found.'); return; }}
  if (statusCol < 0) {{ ui.alert('No status column found.'); return; }}
  
  var deleted = 0;
  for (var i = data.length - 1; i >= 1; i--) {{
    if (data[i][actionCol] === true) {{
      sheet.getRange(i + 1, statusCol + 1).setValue('deleted');
      deleted++;
    }}
  }}
  ui.alert(deleted + ' rows marked as deleted. Click "Sync Changes" to save.');
}}

function showRefreshInstructions() {{
  SpreadsheetApp.getUi().alert(
    'Refresh from Firestore',
    'Run this command in your terminal to pull the latest data from Firestore into this sheet:\n\npython scripts/sheets_sync.py\n\nThe sheet ID to use is in the Controls tab.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}}
""".replace('{{', '{').replace('}}', '}')  # fix brace escaping for Python format


def setup_sheet(sheets_service, spreadsheet_id, fs_db):
    """Add status columns, data validation, action checkboxes, and a Controls tab."""
    ss_meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets_list = ss_meta['sheets']
    requests = []
    
    for sheet_info in sheets_list:
        title = sheet_info['properties']['title']
        sheet_id = sheet_info['properties']['sheetId']
        
        if title == 'Controls':
            continue
        
        # Get header row to count columns
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=f"'{title}'!1:1"
        ).execute()
        headers = result.get('values', [[]])[0]
        num_cols = len(headers)
        
        # Add "status" column header
        requests.append({
            'updateCells': {
                'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 1, 'startColumnIndex': num_cols, 'endColumnIndex': num_cols + 1},
                'rows': [{'values': [{'userEnteredValue': {'stringValue': 'status'}, 'userEnteredFormat': {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2}}}]}],
                'fields': 'userEnteredValue,userEnteredFormat'
            }
        })
        
        # Add "action" column header with checkbox note
        requests.append({
            'updateCells': {
                'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 1, 'startColumnIndex': num_cols + 1, 'endColumnIndex': num_cols + 2},
                'rows': [{'values': [{'userEnteredValue': {'stringValue': 'action'}, 'userEnteredFormat': {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2}}}]}],
                'fields': 'userEnteredValue,userEnteredFormat'
            }
        })
        
        # Add data validation for status column (dropdown)
        requests.append({
            'setDataValidation': {
                'range': {'sheetId': sheet_id, 'startRowIndex': 1, 'startColumnIndex': num_cols, 'endColumnIndex': num_cols + 1},
                'rule': {
                    'condition': {'type': 'ONE_OF_LIST', 'values': [
                        {'userEnteredValue': 'active'},
                        {'userEnteredValue': 'draft'},
                        {'userEnteredValue': 'hidden'},
                        {'userEnteredValue': 'deleted'}
                    ]},
                    'showCustomUi': True,
                    'strict': True
                }
            }
        })
        
        # Add checkbox format for action column
        requests.append({
            'repeatCell': {
                'range': {'sheetId': sheet_id, 'startRowIndex': 1, 'startColumnIndex': num_cols + 1, 'endColumnIndex': num_cols + 2},
                'cell': {'dataValidation': {'condition': {'type': 'BOOLEAN'}}},
                'fields': 'dataValidation'
            }
        })
        
        # Set default status to 'active' for all existing rows
        last_row = len(result.get('values', [[], []])) if False else 500  # rough estimate
        try:
            row_data = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=f"'{title}'!A2:A"
            ).execute().get('values', [])
            data_rows = len(row_data)
        except:
            data_rows = 0
        
        if data_rows > 0:
            default_statuses = [['active']] * data_rows
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"'{title}'!{chr(65 + num_cols)}2",
                valueInputOption='USER_ENTERED',
                body={'values': default_statuses}
            ).execute()
    
    # Execute batch update
    if requests:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={'requests': requests}
        ).execute()
    
    # Add Controls tab
    controls_sheet_id = None
    for s in sheets_list:
        if s['properties']['title'] == 'Controls':
            controls_sheet_id = s['properties']['sheetId']
            break
    
    if controls_sheet_id is None:
        resp = sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={
            'requests': [{'addSheet': {'properties': {'title': 'Controls', 'tabColor': {'red': 0.1, 'green': 0.1, 'blue': 0.3}}}}]
        }).execute()
        controls_sheet_id = resp['replies'][0]['addSheet']['properties']['sheetId']
    
    # Populate controls tab
    controls_data = [
        ['Parent Data Force — Sheet Manager', '', ''],
        ['', '', ''],
        ['INSTRUCTIONS', '', ''],
        ['1. Check the "action" checkbox on rows you want to sync/hide/delete', '', ''],
        ['2. Set "status" to active, draft, hidden, or deleted', '', ''],
        ['3. Use the "Data Manager" menu (top bar) to apply changes', '', ''],
        ['4. Rows marked "deleted" will be excluded from the website', '', ''],
        ['5. "hidden" = not visible on site but kept in database', '', ''],
        ['', '', ''],
        ['QUICK ACTIONS (check "action" box then use menu)', '', ''],
        ['sync', 'Sync to Firestore', 'Data Manager → Sync Changes'],
        ['hide', 'Hide Selected', 'Data Manager → Hide Selected'],
        ['delete', 'Delete Selected', 'Data Manager → Delete Selected'],
        ['unhide', 'Unhide All', 'Data Manager → Unhide All'],
        ['', '', ''],
        ['SHEET ID (for Python sync)', spreadsheet_id, ''],
        ['FIREBASE PROJECT', 'steel-mantra-493704-f9', ''],
    ]
    
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="'Controls'!A1",
        valueInputOption='USER_ENTERED',
        body={'values': controls_data}
    ).execute()
    
    # Format controls tab
    sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={
        'requests': [
            {'repeatCell': {
                'range': {'sheetId': controls_sheet_id, 'startRowIndex': 0, 'endRowIndex': 1},
                'cell': {'userEnteredFormat': {'textFormat': {'bold': True, 'fontSize': 14}, 'backgroundColor': {'red': 0.15, 'green': 0.15, 'blue': 0.35}}},
                'fields': 'userEnteredFormat'
            }},
            {'repeatCell': {
                'range': {'sheetId': controls_sheet_id, 'startRowIndex': 2, 'endRowIndex': 3},
                'cell': {'userEnteredFormat': {'textFormat': {'bold': True, 'fontSize': 12}}},
                'fields': 'userEnteredFormat.textFormat'
            }},
            {'autoResizeDimensions': {
                'dimensions': {'sheetId': controls_sheet_id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 3}
            }}
        ]
    }).execute()
    
    print(f"  Added status + action columns to all tabs")
    print(f"  Created Controls tab with instructions")


def deploy_apps_script(sheets_service, spreadsheet_id):
    """Create and deploy an Apps Script project bound to the sheet."""
    # Apps Script projects are bound via the Sheets API 'container-bound script' pattern
    # We need to use the Apps Script API directly
    
    creds = sheets_service._http.credentials
    
    script_code = APPS_SCRIPT_CODE.replace('{spreadsheet_id}', spreadsheet_id)
    
    script_service = build('script', 'v1', credentials=creds)
    
    # Create a new script project
    project = script_service.projects().create(body={
        'title': 'PDF Sheet Manager',
        'parentId': spreadsheet_id
    }).execute()
    
    script_id = project['scriptId']
    print(f"  Apps Script project created: {script_id}")
    
    # Update script content
    script_service.projects().updateContent(
        scriptId=script_id,
        body={
            'files': [
                {'name': 'Code', 'type': 'SERVER_JS', 'source': script_code},
                {'name': 'appsscript', 'type': 'JSON', 'source': json.dumps({
                    'timeZone': 'America/New_York',
                    'dependencies': {'enabledAdvancedServices': []},
                    'exceptionLogging': 'STACKDRIVER',
                    'oauthScopes': [
                        'https://www.googleapis.com/auth/spreadsheets.currentonly',
                        'https://www.googleapis.com/auth/script.external_request',
                        'https://www.googleapis.com/auth/cloud-platform'
                    ]
                })}
            ]
        }
    ).execute()
    print(f"  Script code deployed to project {script_id}")
    
    # Create a deployment
    deployment = script_service.projects().deployments().create(
        scriptId=script_id,
        body={
            'versionNumber': 1,
            'manifestFileName': 'appsscript',
            'description': 'Initial deployment'
        }
    ).execute()
    
    print(f"  Deployment ID: {deployment['deploymentId']}")
    
    return script_id


def main():
    print("=" * 60)
    print("  PDF Website — Sheet Manager Setup")
    print("=" * 60)
    
    sheets_service = get_sheets_service()
    fs_db = FirestoreClient()
    
    # Use existing or create new spreadsheet
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    spreadsheet_id = None
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith('SHEETS_SPREADSHEET_ID='):
                    spreadsheet_id = line.split('=', 1)[1].strip()
    
    if not spreadsheet_id:
        print("Syncing data to new sheet first...")
        spreadsheet_id = firestore_to_sheets(fs_db, sheets_service)
    
    print(f"\nSpreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    
    print("\nSetting up status columns + validation...")
    setup_sheet(sheets_service, spreadsheet_id, fs_db)
    
    print("\nDeploying Apps Script...")
    try:
        script_id = deploy_apps_script(sheets_service, spreadsheet_id)
        print(f"\nSheet Manager ready! Open the sheet and use the 'Data Manager' menu.")
        print(f"URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    except Exception as e:
        print(f"\nApps Script deployment failed: {e}")
        print("You can manually install the script from: C:\\agents\\sheets_apps_script.gs")
        print("Open sheet -> Extensions -> Apps Script -> Paste code -> Run onOpen() once")


if __name__ == '__main__':
    main()

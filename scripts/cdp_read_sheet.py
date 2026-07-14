import json, time, sys
import urllib.request
import websocket

# Get page target
resp = urllib.request.urlopen('http://localhost:9222/json').read()
tabs = json.loads(resp)
pages = [t for t in tabs if t['type'] == 'page']
if not pages:
    print("No pages found")
    sys.exit(1)

page = pages[0]
ws_url = page['webSocketDebuggerUrl']
print(f"Page: {page['title']}")

ws = websocket.create_connection(ws_url)

def send_cmd(method, params=None):
    msg = json.dumps({'id': 1, 'method': method, 'params': params or {}})
    ws.send(msg)
    resp = ws.recv()
    return json.loads(resp)

# Navigate to Aggregate Request Catalog
url = 'https://docs.google.com/spreadsheets/d/1Ws9ZPkySVwpaMxpkJ56gjOPz4iF--rnE-dVGKxZZC2s/edit'
print(f"Navigating to: {url}")
send_cmd('Page.navigate', {'url': url})

time.sleep(6)

# Get title
result = send_cmd('Runtime.evaluate', {'expression': 'document.title', 'returnByValue': True})
title = result.get('result', {}).get('result', {}).get('value', '?')
print(f"Title: {title}")

# Extract table data from the sheet
script = """
(function() {
    var cells = document.querySelectorAll('[data-row] [data-col], td, th');
    var result = [];
    for (var i = 0; i < Math.min(cells.length, 60); i++) {
        result.push(cells[i].textContent.trim().substring(0, 100));
    }
    return JSON.stringify({cellCount: cells.length, sample: result});
})()
"""

result = send_cmd('Runtime.evaluate', {'expression': script, 'returnByValue': True})
value = result.get('result', {}).get('result', {}).get('value', '')
print(f"Sheet data: {value[:3000]}")

# Also try the waffle grid (the actual sheet cells)
script2 = """
(function() {
    var grid = document.querySelector('.waffle');
    if (!grid) return 'no waffle grid';
    var rows = grid.querySelectorAll('tr');
    var data = [];
    for (var i = 0; i < Math.min(rows.length, 25); i++) {
        var cells = rows[i].querySelectorAll('td');
        var row = [];
        for (var j = 0; j < Math.min(cells.length, 10); j++) {
            row.push(cells[j].textContent.trim().substring(0, 50));
        }
        data.push(row);
    }
    return JSON.stringify(data);
})()
"""
result2 = send_cmd('Runtime.evaluate', {'expression': script2, 'returnByValue': True})
value2 = result2.get('result', {}).get('result', {}).get('value', '')
print(f"Grid data: {value2[:3000]}")

ws.close()

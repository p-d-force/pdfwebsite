#!/usr/bin/env python3
"""DESE PRS Intakes Scraper — reads Excel, writes SQLite + MariaDB seed output"""
import openpyxl, json, datetime, time, os, sys, re, requests, sqlite3

DB_PATH = r"C:\Users\LokiF\Desktop\PDFWEBSITE\dev.db"
OUTPUT_DIR = r"C:\Users\LokiF\Desktop\PDFWEBSITE\backend"
PRS_XLSX = r"C:\agents\drive_exports\PRS_Intakes_Received_and_Findings_since_1.1.21 (1).xlsx"
TABLE = "prs_intakes_data"
DATASET = "prs_intakes"
BATCH_SIZE = 500


def esc(val):
    if val is None or val == "": return "NULL"
    if isinstance(val, (int, float)): return str(val)
    return "'" + str(val).replace("\\", "\\\\").replace("'", "''") + "'"

def parse_int(val):
    if val is None or str(val).strip() in ("", "-", "N/A", "n/a"): return None
    try: return int(str(val).replace(",", "").strip())
    except: return None

def parse_float(val):
    if val is None or str(val).strip() in ("", "-", "N/A", "n/a"): return None
    try: return float(str(val).replace("%", "").replace(",", "").strip())
    except: return None

def needs_refresh(db_path, dataset, new_update_date):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT MAX(update_date) FROM sync_log WHERE dataset = ?", (dataset,))
        row = c.fetchone()
        conn.close()
        if row and row[0] and str(row[0]) >= str(new_update_date):
            return False
    except Exception:
        pass
    return True

def record_sync(db_path, dataset, url, row_count, update_date):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sync_log WHERE dataset = ?", (dataset,))
        exists = c.fetchone()[0]
        if exists:
            c.execute("UPDATE sync_log SET url=?, row_count=?, update_date=?, synced_at=? WHERE dataset=?",
                      (url, row_count, update_date, datetime.datetime.now().isoformat(), dataset))
        else:
            c.execute("INSERT INTO sync_log (dataset, url, row_count, update_date, synced_at) VALUES (?,?,?,?,?)",
                      (dataset, url, row_count, update_date, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  sync_log warning: {e}")

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset TEXT NOT NULL,
        url TEXT,
        row_count INTEGER,
        update_date TEXT,
        synced_at TEXT
    )""")
    c.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prs_number TEXT,
        district TEXT,
        intake_date TEXT,
        status TEXT,
        findings_date TEXT,
        category TEXT,
        subcategory TEXT,
        closure_code TEXT,
        UNIQUE(prs_number)
    )""")
    conn.commit()
    conn.close()

def prs_has_data(db_path):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(f"SELECT COUNT(*) FROM {TABLE}")
        count = c.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False

def read_excel_stream(filepath):
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active
    headers = []
    records = []
    first = True
    for row in ws.iter_rows():
        vals = [str(c.value).strip() if c.value is not None else "" for c in row]
        if first:
            headers = vals
            first = False
        else:
            records.append(dict(zip(headers, vals)))
    wb.close()
    return headers, records

def read_excel_stream_batched(filepath):
    print(f"Reading {filepath}...")
    headers, records = read_excel_stream(filepath)
    if not headers:
        print("  No headers found")
        return []
    if not records:
        print("  No data rows found")
        return []
    hset = set(h.lower() for h in headers)
    col_map = {}
    if "number" in hset or "prs" in hset:
        for h in headers:
            hl = h.lower()
            if "number" in hl or "prs" in hl:
                col_map["prs_number"] = h
                break
    for h in headers:
        hl = h.lower()
        if "district" in hl or "agency" in hl:
            col_map["district"] = h
        elif "intake" in hl or "received" in hl:
            col_map["intake_date"] = h
        elif "status" in hl:
            col_map["status"] = h
        elif "finding" in hl and "issued" in hl:
            col_map["findings_date"] = h
        elif "categor" in hl and "sub" not in hl:
            col_map["category"] = h
        elif "subcategor" in hl:
            col_map["subcategory"] = h
        elif "closure" in hl or "code" in hl:
            col_map["closure_code"] = h
    if "prs_number" not in col_map:
        col_map["prs_number"] = headers[0] if headers else "Number"
    if "district" not in col_map:
        col_map["district"] = headers[1] if len(headers) > 1 else "District"
    print(f"  Column map: {json.dumps(col_map)}")
    return records, col_map

def extract_prs_records(records, col_map):
    results = []
    for r in records:
        try:
            prs_num = str(r.get(col_map.get("prs_number", ""), "")).strip()
            if not prs_num:
                continue
            results.append({
                "prs_number": prs_num,
                "district": str(r.get(col_map.get("district", ""), "")).strip() or None,
                "intake_date": str(r.get(col_map.get("intake_date", ""), "")).strip() or None,
                "status": str(r.get(col_map.get("status", ""), "")).strip() or None,
                "findings_date": str(r.get(col_map.get("findings_date", ""), "")).strip() or None,
                "category": str(r.get(col_map.get("category", ""), "")).strip() or None,
                "subcategory": str(r.get(col_map.get("subcategory", ""), "")).strip() or None,
                "closure_code": str(r.get(col_map.get("closure_code", ""), "")).strip() or None,
            })
        except Exception as e:
            continue
    return results

def write_sqlite_batched(db_path, records):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    sql = f"""INSERT OR REPLACE INTO {TABLE}
        (prs_number, district, intake_date, status, findings_date, category, subcategory, closure_code)
        VALUES (?,?,?,?,?,?,?,?)"""
    written = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        for rec in batch:
            c.execute(sql, (
                rec["prs_number"], rec["district"], rec["intake_date"],
                rec["status"], rec["findings_date"], rec["category"],
                rec["subcategory"], rec["closure_code"]
            ))
        conn.commit()
        written += len(batch)
        print(f"  SQLite: {written}/{len(records)} rows")
    conn.close()

def generate_seed_sql(output_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"""SELECT prs_number, district, intake_date, status, findings_date,
        category, subcategory, closure_code FROM {TABLE} ORDER BY intake_date, prs_number""")
    rows = c.fetchall()
    conn.close()
    if not rows:
        print("  No data to generate SQL")
        return

    cols = ["prs_number", "district", "intake_date", "status", "findings_date",
            "category", "subcategory", "closure_code"]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("-- PRS Intakes Data (from Excel)\n")
        f.write(f"-- Generated {datetime.datetime.now().isoformat()}\n")
        f.write(f"-- Records: {len(rows)}\n\n")
        f.write("SET NAMES utf8mb4;\n\n")
        f.write(f"CREATE TABLE IF NOT EXISTS {TABLE} (\n")
        f.write("    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,\n")
        f.write("    prs_number VARCHAR(100),\n")
        f.write("    district VARCHAR(255),\n")
        f.write("    intake_date VARCHAR(50),\n")
        f.write("    status VARCHAR(100),\n")
        f.write("    findings_date VARCHAR(50),\n")
        f.write("    category VARCHAR(255),\n")
        f.write("    subcategory VARCHAR(255),\n")
        f.write("    closure_code VARCHAR(100),\n")
        f.write("    UNIQUE KEY uq_prs_number (prs_number)\n")
        f.write(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n\n")
        f.write(f"INSERT IGNORE INTO {TABLE} ({', '.join(cols)}) VALUES\n")
        vals = [f"({esc(r[0])},{esc(r[1])},{esc(r[2])},{esc(r[3])},{esc(r[4])},{esc(r[5])},{esc(r[6])},{esc(r[7])})" for r in rows]
        f.write(",\n".join(vals) + ";\n")
    print(f"  SQL: {output_path} ({len(rows)} rows, {os.path.getsize(output_path):,} bytes)")


def main():
    print("=" * 60)
    print("PRS Intakes Scraper")
    print("=" * 60)
    init_db(DB_PATH)

    if prs_has_data(DB_PATH):
        print("prs_intakes_data already has rows — skipping ingest, regenerating SQL only")
        generate_seed_sql(os.path.join(OUTPUT_DIR, "seed_prs.sql"))
        print("Done (SQL regenerated from existing data)")
        print()
        return

    xlsx_path = PRS_XLSX
    if not os.path.exists(xlsx_path):
        print(f"PRS Excel not found: {xlsx_path}")
        print("Trying fallback locations...")
        fallbacks = [
            r"C:\agents\drive_exports\PRS_Intakes_Received_and_Findings_since_1.1.21 (1).xlsx",
            r"C:\agents\drive_exports\PRS_Intakes_Received_and_Findings_since_1.1.21.xlsx",
        ]
        found = False
        for fb in fallbacks:
            if os.path.exists(fb):
                print(f"  Found: {fb}")
                xlsx_path = fb
                found = True
                break
        if not found:
            print("  No PRS file found. Aborting.")
            return

    today = datetime.date.today().isoformat()
    if not needs_refresh(DB_PATH, DATASET, today):
        print("Already synced today — skipping")
        generate_seed_sql(os.path.join(OUTPUT_DIR, "seed_prs.sql"))
        return

    records, col_map = read_excel_stream_batched(xlsx_path)
    if not records:
        print("No records extracted")
        return

    prs_records = extract_prs_records(records, col_map)
    print(f"Parsed {len(prs_records)} PRS records")

    if prs_records:
        write_sqlite_batched(DB_PATH, prs_records)
        record_sync(DB_PATH, DATASET, PRS_XLSX, len(prs_records), today)

    output_path = os.path.join(OUTPUT_DIR, "seed_prs.sql")
    generate_seed_sql(output_path)
    print(f"Done: {len(prs_records)} rows written")
    print()

if __name__ == "__main__":
    main()

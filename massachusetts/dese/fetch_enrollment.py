#!/usr/bin/env python3
"""DESE Selected Populations / Enrollment Scraper — SQLite + MariaDB seed output"""
import openpyxl, json, datetime, time, os, sys, re, requests, sqlite3
from html.parser import HTMLParser

DB_PATH = r"C:\Users\LokiF\Desktop\PDFWEBSITE\dev.db"
OUTPUT_DIR = r"C:\Users\LokiF\Desktop\PDFWEBSITE\backend"
BASE_URL = "https://profiles.doe.mass.edu/statereport/selectedpopulations.aspx"
YEARS = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
TABLE = "enrollment_data"
DATASET = "enrollment"

COL_HIGH_NEEDS_NUM = 2
COL_HIGH_NEEDS_PCT = 3
COL_EL_NUM = 4
COL_EL_PCT = 5
COL_FLNE_NUM = 6
COL_FLNE_PCT = 7
COL_LOW_INCOME_NUM = 8
COL_LOW_INCOME_PCT = 9
COL_SPED_NUM = 10
COL_SPED_PCT = 11


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
        district_name TEXT,
        district_code TEXT,
        school_year TEXT,
        high_needs_num INTEGER,
        high_needs_pct REAL,
        el_num INTEGER,
        el_pct REAL,
        flne_num INTEGER,
        flne_pct REAL,
        low_income_num INTEGER,
        low_income_pct REAL,
        sped_num INTEGER,
        sped_pct REAL,
        UNIQUE(district_code, school_year)
    )""")
    conn.commit()
    conn.close()


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = []
        self.current_cell = ""
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.skipped = False

    def handle_starttag(self, tag, attrs):
        if tag == "table": self.in_table = True
        if self.in_table and tag == "tr":
            self.in_row = True; self.current_row = []; self.skipped = False
        if self.in_row and tag in ("td", "th"):
            self.in_cell = True; self.current_cell = ""

    def handle_endtag(self, tag):
        if tag == "table": self.in_table = False
        if self.in_row and tag == "tr":
            self.in_row = False
            if len(self.current_row) >= 8 and self.skipped:
                self.rows.append(self.current_row)
            self.skipped = True
        if self.in_cell and tag in ("td", "th"):
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())

    def handle_data(self, data):
        if self.in_cell: self.current_cell += data


def is_district_code(val):
    return bool(val and re.match(r"^\d{4,8}$", str(val).strip()))

def fetch_year(year):
    print(f"Fetching {year}...", end=" ", flush=True)
    url = f"{BASE_URL}?year={year}"
    try:
        resp = requests.get(url, headers={"User-Agent": "ParentDataForce/2.0"}, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR: {e}")
        return []
    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', resp.text, re.I | re.DOTALL)
    valid = []
    for tr in trs[1:]:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.I | re.DOTALL)
        clean = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if len(clean) >= 10 and re.match(r'^\d{4,8}$', clean[1]):
            valid.append(clean)
    print(f"{len(valid)} districts")
    return valid

def extract_records(rows, year_label):
    records = []
    max_col = max(COL_HIGH_NEEDS_NUM, COL_HIGH_NEEDS_PCT, COL_EL_NUM, COL_EL_PCT,
                  COL_FLNE_NUM, COL_FLNE_PCT, COL_LOW_INCOME_NUM, COL_LOW_INCOME_PCT,
                  COL_SPED_NUM, COL_SPED_PCT)
    for r in rows:
        if len(r) <= max_col:
            continue
        try:
            records.append({
                "district_name": r[0],
                "district_code": r[1],
                "school_year": year_label,
                "high_needs_num": parse_int(r[COL_HIGH_NEEDS_NUM]),
                "high_needs_pct": parse_float(r[COL_HIGH_NEEDS_PCT]),
                "el_num": parse_int(r[COL_EL_NUM]),
                "el_pct": parse_float(r[COL_EL_PCT]),
                "flne_num": parse_int(r[COL_FLNE_NUM]),
                "flne_pct": parse_float(r[COL_FLNE_PCT]),
                "low_income_num": parse_int(r[COL_LOW_INCOME_NUM]),
                "low_income_pct": parse_float(r[COL_LOW_INCOME_PCT]),
                "sped_num": parse_int(r[COL_SPED_NUM]),
                "sped_pct": parse_float(r[COL_SPED_PCT]),
            })
        except Exception as e:
            print(f"  skip row: {e}")
    return records

def write_sqlite(db_path, records):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    sql = f"""INSERT OR REPLACE INTO {TABLE}
        (district_name, district_code, school_year, high_needs_num, high_needs_pct,
         el_num, el_pct, flne_num, flne_pct, low_income_num, low_income_pct,
         sped_num, sped_pct)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    for rec in records:
        c.execute(sql, (
            rec["district_name"], rec["district_code"], rec["school_year"],
            rec["high_needs_num"], rec["high_needs_pct"],
            rec["el_num"], rec["el_pct"],
            rec["flne_num"], rec["flne_pct"],
            rec["low_income_num"], rec["low_income_pct"],
            rec["sped_num"], rec["sped_pct"]
        ))
    conn.commit()
    conn.close()

def generate_seed_sql(output_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"""SELECT district_name, district_code, school_year,
        high_needs_num, high_needs_pct,
        el_num, el_pct, flne_num, flne_pct,
        low_income_num, low_income_pct,
        sped_num, sped_pct
        FROM {TABLE} ORDER BY school_year, district_code""")
    rows = c.fetchall()
    conn.close()

    cols = ["district_name", "district_code", "school_year",
            "high_needs_num", "high_needs_pct",
            "el_num", "el_pct", "flne_num", "flne_pct",
            "low_income_num", "low_income_pct",
            "sped_num", "sped_pct"]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("-- DESE Selected Populations / Enrollment Data\n")
        f.write(f"-- Generated {datetime.datetime.now().isoformat()}\n")
        f.write(f"-- Records: {len(rows)}\n\n")
        f.write("SET NAMES utf8mb4;\n\n")
        f.write(f"CREATE TABLE IF NOT EXISTS {TABLE} (\n")
        f.write("    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,\n")
        f.write("    district_name VARCHAR(255) NOT NULL,\n")
        f.write("    district_code VARCHAR(10) NOT NULL,\n")
        f.write("    school_year VARCHAR(10) NOT NULL,\n")
        f.write("    high_needs_num INT NULL,\n")
        f.write("    high_needs_pct DECIMAL(5,1) NULL,\n")
        f.write("    el_num INT NULL,\n")
        f.write("    el_pct DECIMAL(5,1) NULL,\n")
        f.write("    flne_num INT NULL,\n")
        f.write("    flne_pct DECIMAL(5,1) NULL,\n")
        f.write("    low_income_num INT NULL,\n")
        f.write("    low_income_pct DECIMAL(5,1) NULL,\n")
        f.write("    sped_num INT NULL,\n")
        f.write("    sped_pct DECIMAL(5,1) NULL,\n")
        f.write("    UNIQUE KEY uq_district_year (district_code, school_year)\n")
        f.write(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n\n")
        if rows:
            f.write(f"INSERT IGNORE INTO {TABLE} ({', '.join(cols)}) VALUES\n")
            vals = []
            for r in rows:
                vals.append(f"({esc(r[0])},{esc(r[1])},{esc(r[2])},{esc(r[3])},{esc(r[4])},{esc(r[5])},{esc(r[6])},{esc(r[7])},{esc(r[8])},{esc(r[9])},{esc(r[10])},{esc(r[11])},{esc(r[12])})")
            f.write(",\n".join(vals) + ";\n")
    print(f"  SQL: {output_path} ({len(rows)} rows, {os.path.getsize(output_path):,} bytes)")


def main():
    print("=" * 60)
    print("DESE Selected Populations / Enrollment Scraper")
    print(f"Column indices: high_needs=({COL_HIGH_NEEDS_NUM},{COL_HIGH_NEEDS_PCT}) el=({COL_EL_NUM},{COL_EL_PCT}) flne=({COL_FLNE_NUM},{COL_FLNE_PCT}) low_income=({COL_LOW_INCOME_NUM},{COL_LOW_INCOME_PCT}) sped=({COL_SPED_NUM},{COL_SPED_PCT})")
    print("=" * 60)
    init_db(DB_PATH)
    today = datetime.date.today().isoformat()
    all_rows = 0

    for year in YEARS:
        ds_key = f"{DATASET}_{year}"
        if not needs_refresh(DB_PATH, ds_key, today):
            print(f"Skipping {year} (already synced)")
            continue
        rows = fetch_year(year)
        if not rows:
            continue
        records = extract_records(rows, year)
        if records:
            write_sqlite(DB_PATH, records)
            record_sync(DB_PATH, ds_key, f"{BASE_URL}?year={year}", len(records), today)
            all_rows += len(records)
        time.sleep(0.3)

    if all_rows:
        output_path = os.path.join(OUTPUT_DIR, "seed_enrollment.sql")
        generate_seed_sql(output_path)
    print(f"Done: {all_rows} new rows written")
    print()

if __name__ == "__main__":
    main()

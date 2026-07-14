#!/usr/bin/env python3
"""
DESE Student Restraint Data Scraper
Source: https://profiles.doe.mass.edu/statereport/restraints.aspx

Extracts all school-level restraint data for every available year (2016-17 through 2024-25),
parses the HTML table, calculates rates, and outputs a .sql seed file for the restraint_data table.

Usage:
    python fetch_dese_restraints.py

Output:
    backend/seed_restraint.sql (ready for MySQL/MariaDB import)
"""

import re
import json
import sys
import time
from pathlib import Path
from html.parser import HTMLParser

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

BASE_URL = "https://profiles.doe.mass.edu/statereport/restraints.aspx"
YEARS = [
    "2016-17", "2017-18", "2018-19", "2019-20",
    "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"
]

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "backend" / "seed_restraint.sql"


class RestraintTableParser(HTMLParser):
    """Parses the DESE restraint HTML table into structured rows."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = []
        self.current_cell = ""
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.in_link = False
        self.cell_index = 0
        self.header_skipped = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "table":
            self.in_table = True
        if self.in_table and tag == "tr":
            self.in_row = True
            self.current_row = []
            self.cell_index = 0
        if self.in_row and tag in ("td", "th"):
            self.in_cell = True
            self.current_cell = ""
        if self.in_cell and tag == "a":
            self.in_link = True

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        if self.in_row and tag == "tr":
            self.in_row = False
            if len(self.current_row) >= 5 and self.header_skipped:
                self.rows.append(self.current_row)
            self.header_skipped = True
        if self.in_cell and tag in ("td", "th"):
            self.in_cell = False
            cell = self.current_cell.strip()
            self.current_row.append(cell)
            self.cell_index += 1
        if tag == "a":
            self.in_link = False

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


def parse_number(value):
    """Parse a cell value to a number or None. Dash means suppressed."""
    value = value.strip()
    if value in ("-", "", "n/a", "N/A"):
        return None
    return int(value.replace(",", ""))


def extract_district_and_school(school_link_text, school_code_text):
    """Extract district name, school name, and district code from the school name cell and code."""
    school_link_text = school_link_text.strip()

    # District code: first 4 digits of school code
    district_code = school_code_text.strip()[:4] if school_code_text.strip() else ""

    # Try "District - School" or "District — School" pattern
    parts = re.split(r'\s*[-—]\s*', school_link_text, maxsplit=1)
    if len(parts) == 2:
        district_name = parts[0].strip()
        school_name = parts[1].strip() if parts[1].strip() else school_link_text.strip()
    else:
        # Single entry (could be a collaborative or standalone program)
        district_name = school_link_text.strip()
        school_name = school_link_text.strip()

    return district_name, school_name, district_code


def escape_sql(value):
    if value is None:
        return "NULL"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def build_sql(rows_by_year):
    """Build the SQL seed file from parsed data."""
    lines = []
    lines.append("-- DESE Student Restraint Data — School-Level Records")
    lines.append(f"-- Scraped from {BASE_URL}")
    lines.append(f"-- Years: {', '.join(YEARS)}")
    lines.append("-- Generated automatically — do not edit by hand")
    lines.append("")
    lines.append("SET NAMES utf8mb4;")
    lines.append("")
    lines.append("CREATE TABLE IF NOT EXISTS restraint_data (")
    lines.append("    id INT AUTO_INCREMENT PRIMARY KEY,")
    lines.append("    school_year VARCHAR(10) NOT NULL,")
    lines.append("    district_name VARCHAR(255),")
    lines.append("    district_code VARCHAR(20),")
    lines.append("    school_name VARCHAR(255),")
    lines.append("    school_code VARCHAR(20),")
    lines.append("    enrollment INT,")
    lines.append("    students_restrained INT,")
    lines.append("    students_restrained_suppressed TINYINT(1) DEFAULT 0,")
    lines.append("    total_restraints INT,")
    lines.append("    total_restraints_suppressed TINYINT(1) DEFAULT 0,")
    lines.append("    total_injuries INT,")
    lines.append("    total_injuries_suppressed TINYINT(1) DEFAULT 0,")
    lines.append("    restraint_rate_per_100 DECIMAL(12,4),")
    lines.append("    injuries_per_restraint DECIMAL(12,4),")
    lines.append("    is_summary_row TINYINT(1) DEFAULT 0,")
    lines.append("    source_workbook VARCHAR(255),")
    lines.append("    INDEX idx_year (school_year),")
    lines.append("    INDEX idx_district (district_code),")
    lines.append("    INDEX idx_school (school_code)")
    lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;")
    lines.append("")

    total_inserts = 0

    for year, rows in rows_by_year.items():
        for row in rows:
            school_link = row[0]
            school_code = row[1]
            enrollment_str = row[2]
            students_str = row[3]
            total_str = row[4]
            injuries_str = row[5]

            district_name, school_name, district_code = extract_district_and_school(school_link, school_code)
            enrollment = parse_number(enrollment_str)
            students = parse_number(students_str)
            total_restraints = parse_number(total_str)
            injuries = parse_number(injuries_str)

            students_suppressed = 1 if students is None else 0
            total_suppressed = 1 if total_restraints is None else 0
            injuries_suppressed = 1 if injuries is None else 0

            students_val = students if students is not None else 0
            total_val = total_restraints if total_restraints is not None else 0
            injuries_val = injuries if injuries is not None else 0

            # Restraint rate per 100 students
            rate = None
            if enrollment and enrollment > 0 and total_val > 0:
                rate = (total_val / enrollment) * 100.0

            # Injuries per restraint
            ipr = None
            if total_val > 0 and injuries_val > 0:
                ipr = injuries_val / total_val

            is_summary = district_name and "Public Schools Total" in district_name

            lines.append(
                f"INSERT INTO restraint_data (school_year, district_name, district_code, school_name, "
                f"school_code, enrollment, students_restrained, students_restrained_suppressed, "
                f"total_restraints, total_restraints_suppressed, total_injuries, total_injuries_suppressed, "
                f"restraint_rate_per_100, injuries_per_restraint, is_summary_row, source_workbook) VALUES ("
                f"{escape_sql(year)}, {escape_sql(district_name)}, {escape_sql(district_code)}, "
                f"{escape_sql(school_name)}, {escape_sql(school_code)}, {escape_sql(enrollment)}, "
                f"{escape_sql(students_val)}, {students_suppressed}, "
                f"{escape_sql(total_val)}, {total_suppressed}, "
                f"{escape_sql(injuries_val)}, {injuries_suppressed}, "
                f"{escape_sql(rate)}, {escape_sql(ipr)}, "
                f"{1 if is_summary else 0}, "
                f"{escape_sql(f'DESE Student Restraints Report {year}')}"
                f");"
            )
            total_inserts += 1

    lines.append("")
    lines.append(f"-- Total rows: {total_inserts}")
    lines.append("")

    return "\n".join(lines)


def is_summary_row(row_text):
    """Check if a row is the 'Public Schools Total' summary row."""
    return "Public Schools Total" in row_text or "All Schools" in row_text


def fetch_year(year):
    """Fetch and parse data for a single school year."""
    print(f"  Fetching {year}...", end=" ", flush=True)

    url = f"{BASE_URL}?year={year}"
    headers = {
        "User-Agent": "ParentDataForce/2.0 (research; parentdataforce.com)",
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f"FAILED: {e}")
        return []

    parser = RestraintTableParser()
    parser.feed(resp.text)

    valid_rows = []
    for row in parser.rows:
        if len(row) >= 6:
            # Skip summary rows and empty rows
            school_link = row[0].strip()
            if not school_link or is_summary_row(school_link):
                continue
            # Ensure school_code is present (column 2)
            if row[1].strip() and row[1].strip() != "-":
                valid_rows.append(row)

    print(f"{len(valid_rows)} schools")
    return valid_rows


def main():
    print("=" * 60)
    print("DESE Student Restraint Data Scraper")
    print(f"Source: {BASE_URL}")
    print(f"Years: {len(YEARS)} ({YEARS[0]} — {YEARS[-1]})")
    print("=" * 60)
    print()

    all_data = {}

    for year in YEARS:
        rows = fetch_year(year)
        all_data[year] = rows
        time.sleep(0.5)

    total_rows = sum(len(rows) for rows in all_data.values())
    print(f"\nTotal: {total_rows} rows across {len(YEARS)} years")

    sql = build_sql(all_data)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(sql, encoding="utf-8")

    print(f"\nSQL seed file written: {OUTPUT_PATH}")
    print(f"Size: {len(sql):,} bytes")
    print("\nImport with:")
    print(f"  mysql -u pdf_user -p pdf_db < {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

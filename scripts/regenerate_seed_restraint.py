#!/usr/bin/env python3
"""
Regenerate seed_restraint.sql from the actual Excel source files.
Fixes the data duplication bug where all years had identical data.
"""
import openpyxl
import os, sys
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "dese-restraint"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "backend" / "seed_restraint.sql"

YEARS = [
    '2016-17', '2017-18', '2018-19', '2019-20',
    '2020-21', '2021-22', '2022-23', '2023-24', '2024-25'
]

def escape_sql(value):
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return str(value)
    return str(value)


def parse_int(raw):
    """Parse a cell value to int or None (suppressed). Returns (value, is_suppressed)."""
    if raw is None or str(raw).strip() in ('', '-', '—', 'None'):
        return 0, 1
    try:
        return int(str(raw).replace(',', '')), 0
    except (ValueError, TypeError):
        return 0, 1


def main():
    print("Regenerating seed_restraint.sql from Excel files...")
    print(f"Source: {DATA_DIR}")
    print(f"Output: {OUTPUT_PATH}")
    print()

    lines = []
    lines.append("-- DESE Student Restraint Data — School-Level Records")
    lines.append("-- Regenerated from Excel source files (data/raw/dese-restraint/)")
    lines.append("-- Years: 2016-17 through 2024-25")
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
    year_totals = {}
    # Track stats per year for verification
    year_stats = defaultdict(lambda: {'schools': 0, 'restraints': 0, 'students': 0, 'injuries': 0})

    for year in YEARS:
        filename = f"dese-student-restraints-{year}-public-schools.xlsx"
        filepath = DATA_DIR / filename
        if not filepath.exists():
            print(f"  WARNING: {filename} not found, skipping")
            continue

        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb.active
        school_count = 0

        for row in ws.iter_rows(min_row=3, values_only=True):
            district_code = str(row[0]).strip() if row[0] else ''
            district_name = str(row[1]).strip() if row[1] else ''
            school_code = str(row[2]).strip() if row[2] else ''
            school_name = str(row[3]).strip() if row[3] else ''

            if not school_name or school_name == 'None':
                continue

            enrollment, _ = parse_int(row[4])
            students, students_suppressed = parse_int(row[5])
            total_restraints, total_suppressed = parse_int(row[6])
            injuries, injuries_suppressed = parse_int(row[7])

            # Restraint rate per 100
            rate = None
            if enrollment and enrollment > 0 and total_restraints > 0 and not total_suppressed:
                rate = round((total_restraints / enrollment) * 100.0, 4)

            # Injuries per restraint
            ipr = None
            if total_restraints > 0 and injuries > 0 and not total_suppressed and not injuries_suppressed:
                ipr = round(injuries / total_restraints, 4)

            is_summary = 'Public Schools Total' in school_name

            lines.append(
                f"INSERT INTO restraint_data (school_year, district_name, district_code, school_name, "
                f"school_code, enrollment, students_restrained, students_restrained_suppressed, "
                f"total_restraints, total_restraints_suppressed, total_injuries, total_injuries_suppressed, "
                f"restraint_rate_per_100, injuries_per_restraint, is_summary_row, source_workbook) VALUES ("
                f"{escape_sql(year)}, {escape_sql(district_name)}, {escape_sql(district_code)}, "
                f"{escape_sql(school_name)}, {escape_sql(school_code)}, {escape_sql(enrollment)}, "
                f"{escape_sql(students)}, {students_suppressed}, "
                f"{escape_sql(total_restraints)}, {total_suppressed}, "
                f"{escape_sql(injuries)}, {injuries_suppressed}, "
                f"{escape_sql(rate)}, {escape_sql(ipr)}, "
                f"{1 if is_summary else 0}, "
                f"{escape_sql(f'DESE Student Restraints Report {year}')}"
                f");"
            )

            if not is_summary:
                year_stats[year]['schools'] += 1
                year_stats[year]['restraints'] += total_restraints
                year_stats[year]['students'] += students
                year_stats[year]['injuries'] += injuries

            school_count += 1
            total_inserts += 1

        year_totals[year] = school_count
        wb.close()
        print(f"  {year}: {school_count} rows")

    lines.append("")
    lines.append(f"-- Total rows: {total_inserts}")
    lines.append("")

    sql = "\n".join(lines)
    OUTPUT_PATH.write_text(sql, encoding="utf-8")

    print(f"\nTotal: {total_inserts} INSERT statements")
    print(f"Size: {len(sql):,} bytes")
    print(f"\nYear summaries (non-summary rows only):")
    for year in YEARS:
        if year in year_stats:
            s = year_stats[year]
            print(f"  {year}: {s['schools']} schools, {s['restraints']:,} restraints, {s['students']:,} students, {s['injuries']:,} injuries")
    print(f"\nWritten to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Import JSON case files into MariaDB database.
Part of Phase 3 migration (JSON → MariaDB).
"""

import os
import sys
import json
import pymysql
from pathlib import Path
from datetime import datetime


def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        sys.exit(1)

    env = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip("\"'")
    return env


def get_db_connection(env):
    """Create database connection"""
    db_config = {
        "host": "127.0.0.1",
        "port": 3306,
        "user": env.get("DB_USER", "pdf_user"),
        "password": env.get("DB_PASSWORD", "dev_password"),
        "database": env.get("DB_NAME", "pdf_db"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
    }

    try:
        connection = pymysql.connect(**db_config)
        return connection
    except pymysql.Error as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)


def ensure_district_exists(connection, district_code, district_name, location=None):
    """Ensure district exists in database, return district ID"""
    with connection.cursor() as cursor:
        # Check if district exists
        cursor.execute(
            "SELECT id FROM districts WHERE district_code = %s", (district_code,)
        )
        district = cursor.fetchone()

        if district:
            return district["id"]

        # Create new district
        cursor.execute(
            """
            INSERT INTO districts (district_code, district_name, location, status)
            VALUES (%s, %s, %s, 'active')
            """,
            (district_code, district_name, location or district_name),
        )
        connection.commit()
        return cursor.lastrowid


def import_case(connection, case_data, dry_run=False):
    """Import a single case from JSON data"""
    # Map JSON fields to database columns
    case_code = case_data.get("caseId", "")
    district_code = case_data.get("districtCode", "")
    district_name = case_data.get("districtName", "")
    title = case_data.get("title", "")
    subject = case_data.get("subject", "")
    case_type = case_data.get("caseType", "case")
    status = case_data.get("status", "open")
    stage = case_data.get("currentStage", "")

    # Parse dates (might be null or empty)
    filed_date_str = case_data.get("filedDate", "")
    next_deadline_str = case_data.get("nextDeadline", "")

    filed_date = None
    next_deadline = None

    if filed_date_str:
        try:
            filed_date = datetime.strptime(filed_date_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"Warning: Invalid filed_date format: {filed_date_str}")

    if next_deadline_str:
        try:
            next_deadline = datetime.strptime(next_deadline_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"Warning: Invalid next_deadline format: {next_deadline_str}")

    next_deadline_description = case_data.get("nextDeadlineDescription", "")

    print(f"Processing case: {case_code} ({district_code})")

    if dry_run:
        print(f"  Would insert: {case_code} - {title}")
        return None

    try:
        with connection.cursor() as cursor:
            # Get or create district
            district_id = ensure_district_exists(
                connection, district_code, district_name
            )

            # Check if case already exists
            cursor.execute("SELECT id FROM cases WHERE case_code = %s", (case_code,))
            existing_case = cursor.fetchone()

            if existing_case:
                print(f"  Case already exists, updating: {case_code}")
                # Update existing case
                cursor.execute(
                    """
                    UPDATE cases SET
                        district_id = %s,
                        title = %s,
                        case_type = %s,
                        status = %s,
                        stage = %s,
                        subject = %s,
                        filed_date = %s,
                        next_deadline = %s,
                        next_deadline_description = %s,
                        updated_at = UTC_TIMESTAMP()
                    WHERE case_code = %s
                    """,
                    (
                        district_id,
                        title,
                        case_type,
                        status,
                        stage,
                        subject,
                        filed_date,
                        next_deadline,
                        next_deadline_description,
                        case_code,
                    ),
                )
                case_id = existing_case["id"]
            else:
                # Insert new case
                cursor.execute(
                    """
                    INSERT INTO cases (
                        case_code, district_id, title, case_type, status,
                        stage, subject, filed_date, next_deadline,
                        next_deadline_description, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, UTC_TIMESTAMP(), UTC_TIMESTAMP())
                    """,
                    (
                        case_code,
                        district_id,
                        title,
                        case_type,
                        status,
                        stage,
                        subject,
                        filed_date,
                        next_deadline,
                        next_deadline_description,
                    ),
                )
                case_id = cursor.lastrowid
                print(f"  Inserted new case with ID: {case_id}")

            connection.commit()
            return case_id

    except pymysql.Error as e:
        print(f"  Error importing case {case_code}: {e}")
        connection.rollback()
        return None


def find_case_json_files(data_dir):
    """Find all case JSON files in the data directory"""
    cases_dir = Path(data_dir) / "entities" / "cases"
    if not cases_dir.exists():
        print(f"Error: Cases directory not found: {cases_dir}")
        return []

    case_files = list(cases_dir.glob("case-*.json"))
    print(f"Found {len(case_files)} case JSON files")
    return case_files


def main():
    print("Parent Data Force - JSON Case Import")
    print("====================================")
    print("")

    # Parse command line arguments
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("Running in dry-run mode (no changes will be made)")
        print("")

    # Load environment and connect to database
    env = load_env()

    if not dry_run:
        connection = get_db_connection(env)
    else:
        connection = None

    # Find case files
    data_dir = Path(__file__).parent.parent / "data"
    case_files = find_case_json_files(data_dir)

    if not case_files:
        print("No case files found. Exiting.")
        return

    imported_count = 0
    skipped_count = 0
    error_count = 0

    for case_file in case_files:
        try:
            with open(case_file, "r", encoding="utf-8") as f:
                case_data = json.load(f)

            if dry_run:
                import_case(None, case_data, dry_run=True)
                imported_count += 1
            else:
                case_id = import_case(connection, case_data, dry_run=False)
                if case_id:
                    imported_count += 1
                else:
                    error_count += 1

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file {case_file.name}: {e}")
            error_count += 1
        except Exception as e:
            print(f"Unexpected error processing {case_file.name}: {e}")
            error_count += 1

    print("")
    print("Import Summary:")
    print(f"  Total files: {len(case_files)}")
    print(f"  Successfully imported: {imported_count}")
    print(f"  Errors: {error_count}")

    if not dry_run:
        connection.close()
        print("")
        print("Database connection closed.")

    if dry_run:
        print("")
        print("Dry run completed. No changes were made to the database.")


if __name__ == "__main__":
    main()

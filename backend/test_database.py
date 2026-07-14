#!/usr/bin/env python3
"""
Test database connectivity and schema.
"""

import os
import sys
from pathlib import Path
import pymysql


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


def test_connection():
    env = load_env()

    db_config = {
        "host": "127.0.0.1",
        "port": 3306,
        "user": env.get("DB_USER", "pdf_user"),
        "password": env.get("DB_PASSWORD", "dev_password"),
        "database": env.get("DB_NAME", "pdf_db"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
    }

    print("Testing database connection with config:")
    print(f"  Host: {db_config['host']}:{db_config['port']}")
    print(f"  Database: {db_config['database']}")
    print(f"  User: {db_config['user']}")
    print()

    try:
        connection = pymysql.connect(**db_config)
        print("[OK] Connection successful!")

        with connection.cursor() as cursor:
            # List tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_names = [list(table.values())[0] for table in tables]
            print(f"[TABLE] Found {len(table_names)} tables:")
            for name in sorted(table_names):
                cursor.execute(f"SELECT COUNT(*) as cnt FROM `{name}`")
                count = cursor.fetchone()["cnt"]
                print(f"  - {name}: {count} rows")

            # Check admin_users has at least one user
            if "admin_users" in table_names:
                cursor.execute("SELECT username, role, status FROM admin_users")
                users = cursor.fetchall()
                print(f"\n[USER] Admin users ({len(users)}):")
                for user in users:
                    print(f"  - {user['username']} ({user['role']}, {user['status']})")

            # Check cases count
            if "cases" in table_names:
                cursor.execute(
                    "SELECT status, COUNT(*) as cnt FROM cases GROUP BY status"
                )
                status_counts = cursor.fetchall()
                print(f"\n[CASE] Cases by status:")
                for row in status_counts:
                    print(f"  - {row['status']}: {row['cnt']}")

            # Check foreign key constraints
            cursor.execute(
                """
                SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY TABLE_NAME, COLUMN_NAME
            """,
                (db_config["database"],),
            )
            fks = cursor.fetchall()
            print(f"\n[FK] Foreign key constraints ({len(fks)}):")
            for fk in fks:
                print(
                    f"  - {fk['TABLE_NAME']}.{fk['COLUMN_NAME']} -> {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}"
                )

        connection.close()
        print("\nSUCCESS: All tests passed!")
        return True

    except pymysql.Error as e:
        print(f"ERROR: Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Docker containers are running: docker-compose up -d")
        print("2. Check if MariaDB is listening on port 3306")
        print("3. Verify credentials in .env file match docker-compose.yml")
        print("4. Wait for database initialization (first run may take 30 seconds)")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

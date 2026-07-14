#!/usr/bin/env python3
"""
Check if the Parent Data Force database setup is ready.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_docker():
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def check_files():
    required = [
        ".env",
        "docker-compose.yml",
        "backend/schema.sql",
        "backend/admin_schema.sql",
        "backend/seed_from_metadata.sql",
        "admin/includes/config.php",
        "admin/includes/Database.php",
        "admin/includes/Auth.php",
        "admin/login.php",
        "admin/dashboard.php",
        "docker/php/php.ini",
        "docker/php/startup.sh",
    ]

    missing = []
    for path in required:
        if not Path(path).exists():
            missing.append(path)

    return missing


def main():
    print("Parent Data Force - Setup Check")
    print("=" * 40)

    # Check Docker
    print("\n1. Docker status:", end=" ")
    if check_docker():
        print("[OK] Running")
    else:
        print("[FAIL] Not running")
        print("   Please start Docker Desktop and ensure it's ready.")

    # Check required files
    print("\n2. Required files:", end=" ")
    missing = check_files()
    if not missing:
        print("[OK] All present")
    else:
        print(f"[FAIL] Missing {len(missing)} file(s)")
        for m in missing:
            print(f"   - {m}")

    # Check .env configuration
    print("\n3. Environment configuration:", end=" ")
    env_path = Path(".env")
    if env_path.exists():
        try:
            content = env_path.read_text()
            if "dev_root_pass" in content and "dev_password" in content:
                print("[WARN]  Using default passwords (change for production!)")
            else:
                print("[OK] Custom passwords detected")
        except Exception:
            print("[OK] Present")
    else:
        print("[FAIL] Missing .env file")

    # Check if containers are running
    print("\n4. Docker containers:", end=" ")
    if check_docker():
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    "name=pdf_",
                    "--format",
                    "table {{.Names}}\t{{.Status}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                print("")
                for line in lines[1:]:
                    if line.strip():
                        print(f"   {line}")
            else:
                print("[FAIL] No PDF containers running")
        except subprocess.SubprocessError:
            print("[WARN]  Could not check containers")
    else:
        print("Skipped (Docker not running)")

    # Summary
    print("\n" + "=" * 40)
    print("SUMMARY:")

    if not check_docker():
        print("• Start Docker Desktop before proceeding")

    if missing:
        print(f"• Fix missing files ({len(missing)} total)")

    if check_docker() and not missing:
        print(
            "• Run 'scripts/start-database.bat' (Windows) or 'scripts/start-database.sh' (Linux/Mac)"
        )
        print("• After startup, access:")
        print("  - Admin login: http://localhost:8081/admin/login.php")
        print("  - phpMyAdmin: http://localhost:8080")
        print("• Default credentials: admin / admin")

    print("\nFor detailed instructions, see DATABASE-SETUP.md")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate bcrypt password hash compatible with PHP password_hash().
"""

import bcrypt
import getpass
import sys


def generate_hash(password):
    # Generate salt and hash with bcrypt (cost=10)
    salt = bcrypt.gensalt(rounds=10, prefix=b"2b")
    hash_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hash_bytes.decode("utf-8")


def main():
    print("Password Hash Generator")
    print("=" * 40)

    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match")
            sys.exit(1)

    if not password:
        print("Error: Password cannot be empty")
        sys.exit(1)

    hash_value = generate_hash(password)

    print("\nGenerated hash:")
    print(f"  {hash_value}")

    print("\nSQL update statement:")
    print(
        f"  UPDATE admin_users SET password_hash = '{hash_value}', password_changed_at = NOW() WHERE username = 'admin';"
    )

    print("\nPHP code to verify:")
    print(f"  <?php")
    print(f"  $hash = '{hash_value}';")
    print(f"  $password = 'your_password';")
    print(f"  if (password_verify($password, $hash)) echo 'OK';")
    print(f"  ?>")


if __name__ == "__main__":
    main()

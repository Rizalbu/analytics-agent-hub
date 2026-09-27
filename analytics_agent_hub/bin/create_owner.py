"""Create (or promote) the first owner account.

Run from a terminal on the machine hosting the app. This is deliberately
NOT an HTTP endpoint. Owner is the only role that can trigger the
autonomous engineering loop (see app/engineer.py); if creating an owner
were reachable over the API, anyone who could reach any endpoint that
calls it would effectively hold that power. A local script means it takes
actual access to the box, same as `createsuperuser` in Django or the
first-run flow in most self-hosted apps.

Usage:
    python bin/create_owner.py <username> <password>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import auth  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python bin/create_owner.py <username> <password>")
        return 1
    username, password = sys.argv[1], sys.argv[2]

    users = auth._load_users()
    if username in users:
        if not auth.set_role(username, "owner"):
            print(f"Could not promote existing user {username!r}.")
            return 1
        print(f"Promoted existing user {username!r} to owner.")
        return 0

    if not auth.register(username, password):
        print("Registration failed (invalid username/password).")
        return 1
    auth.set_role(username, "owner")
    print(f"Created owner account {username!r}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

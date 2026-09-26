"""Real login: hashed passwords + issued session tokens.

Replaces the old scheme where the frontend hardcoded `Bearer tryon` and the
backend checked that literal string — any request with that string worked,
logged-in or not. Users are stored in a local JSON file (single shared
warehouse still, no per-org isolation yet — that's the next layer).
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]  # analytics_agent_hub/, independent
                                              # of where the warehouse resolves
                                              # to (own repo vs. sibling vendor)
USERS_PATH = _ROOT / "data" / "users.json"
_SESSIONS: dict[str, dict] = {}  # token -> {username, issued_at}
SESSION_TTL = 60 * 60 * 12  # 12h


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def _load_users() -> dict[str, dict]:
    if not USERS_PATH.exists():
        salt = secrets.token_hex(16)
        users = {"try": {"salt": salt, "hash": _hash("tryon", salt)}}
        _save_users(users)
        return users
    return json.loads(USERS_PATH.read_text())


def _save_users(users: dict[str, dict]) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    USERS_PATH.write_text(json.dumps(users))


def register(username: str, password: str) -> bool:
    users = _load_users()
    if not username or not password or username in users:
        return False
    salt = secrets.token_hex(16)
    users[username] = {"salt": salt, "hash": _hash(password, salt)}
    _save_users(users)
    return True


def login(username: str, password: str) -> str | None:
    users = _load_users()
    u = users.get(username)
    if not u or _hash(password, u["salt"]) != u["hash"]:
        return None
    token = secrets.token_urlsafe(32)
    _SESSIONS[token] = {"username": username, "issued_at": time.time()}
    return token


def username_for(token: str | None) -> str | None:
    if not token:
        return None
    session = _SESSIONS.get(token)
    if not session:
        return None
    if time.time() - session["issued_at"] > SESSION_TTL:
        del _SESSIONS[token]
        return None
    return session["username"]

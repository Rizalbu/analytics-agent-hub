# ADR-007: Real login (replacing the hardcoded Bearer token)

## Context

The API gate checked `Authorization: Bearer tryon`, a literal string baked
into both the frontend (`CREDS = { try: 'tryon' }`, always sent regardless of
what the user typed) and the backend middleware. Anyone could call the API
directly with that string with no login at all; the login form was cosmetic.

## Decision

`app/auth.py` stores users (username + salted PBKDF2 hash) in a local JSON
file next to the warehouse. `POST /api/auth/login` verifies the password and
issues a random session token (`secrets.token_urlsafe`), held server-side
in-memory with a 12h TTL. The middleware now resolves the bearer token to a
real username via `auth.username_for()` instead of comparing to a constant.
The demo user `try`/`tryon` is seeded on first run so the existing demo flow
still works. `POST /api/auth/register` lets a second user sign up.

## Not done here

Still a single shared warehouse: every logged-in user sees the same data.
Per-organization data isolation (`X-Org-Id`, separate data slices) is the
next layer, tracked in `docs/BRIEF.md`.

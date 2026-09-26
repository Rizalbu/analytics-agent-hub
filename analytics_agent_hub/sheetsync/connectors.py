"""Source connectors. The demo uses LocalCsvConnector (emulated sheets).
GoogleSheetsConnector is the drop-in real-world option — same interface, so
engine.py is unchanged when you switch. Requires gspread + a service account
(set GOOGLE_APPLICATION_CREDENTIALS and HUB_SHEET_IDS); kept optional so the
demo stays keyless.
"""
from __future__ import annotations

from pathlib import Path

from app.config import settings


class LocalCsvConnector:
    """Reads the emulated studio sheets from data/sheets/*.csv."""
    def list_sheets(self) -> list[Path]:
        return sorted(Path(settings.sheets_dir).glob("*.csv"))


class GoogleSheetsConnector:  # pragma: no cover - optional path
    """Real Google Sheets source. Not used in the keyless demo.

    Usage:
        pip install gspread google-auth
        export GOOGLE_APPLICATION_CREDENTIALS=sa.json
        export HUB_SHEET_IDS="<id1>,<id2>"
    Then point engine at this connector. Each worksheet is exported to the same
    row shape the engine expects, so contracts/drift logic are identical.
    """
    def __init__(self, sheet_ids: list[str]):
        import gspread  # noqa: F401  (import here so demo needs no dep)
        from google.oauth2.service_account import Credentials  # noqa: F401
        self.sheet_ids = sheet_ids

    def list_sheets(self):
        raise NotImplementedError(
            "Configure gspread + service account, then map worksheets to the "
            "engine's (header, rows) contract. Left as a documented extension.")

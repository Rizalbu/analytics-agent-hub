"""Sheet Sync engine: drift quarantine, idempotency, deletion detection."""
import csv
from pathlib import Path

import pytest

from app.config import settings
from sheetsync import engine, seed


@pytest.fixture(autouse=True)
def fresh(tmp_path, monkeypatch):
    # isolate sheets + sync db per test
    sheets = tmp_path / "sheets"
    monkeypatch.setattr(settings, "sheets_dir", str(sheets))
    monkeypatch.setattr(settings, "sync_db", str(tmp_path / "sync.duckdb"))
    monkeypatch.setattr(engine, "SHEETS_DIR", sheets)
    seed.gen(days=20, seed=1, inject_drift=True)
    yield


def test_clean_sheets_merge_and_dedupe():
    res = {r["sheet_file"]: r for r in engine.sync_all()}
    s01 = res["S01.csv"]
    assert s01["status"] == "clean"
    assert s01["rows_merged"] < s01["rows_in"]  # dupes removed


def test_drift_is_quarantined_with_suggestion():
    res = {r["sheet_file"]: r for r in engine.sync_all()}
    s07 = res["S07.csv"]
    assert s07["status"] == "quarantined"
    assert s07["rows_merged"] == 0
    assert s07["drift"][0]["suggestion"] == "cash_collected"


def test_idempotent_resync_is_noop():
    engine.sync_all()
    res2 = {r["sheet_file"]: r for r in engine.sync_all()}
    assert res2["S01.csv"]["status"] == "unchanged"
    assert res2["S01.csv"]["rows_merged"] == 0


def test_deletion_detected():
    engine.sync_all()
    f = Path(settings.sheets_dir) / "S01.csv"
    rows = list(csv.reader(open(f, encoding="utf-8")))
    with open(f, "w", newline="", encoding="utf-8") as out:
        csv.writer(out).writerows([rows[0]] + rows[2:])  # drop a unique row
    res = {r["sheet_file"]: r for r in engine.sync_all()}
    assert res["S01.csv"]["deletes"] >= 1

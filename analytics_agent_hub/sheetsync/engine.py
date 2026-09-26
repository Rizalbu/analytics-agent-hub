"""Sheet Sync engine: snapshot -> contract/drift check -> validate -> MERGE.

State lives in its own DuckDB (settings.sync_db) so it never touches the
analytics warehouse. Everything is idempotent: re-running a clean sheet is a
no-op (content hash); re-running after an edit MERGEs only changed rows.
"""
from __future__ import annotations

import csv
import difflib
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from app.config import settings
from .contracts import CONTRACTS, Contract

SHEETS_DIR = Path(settings.sheets_dir)


# ---- store ----

def _db() -> duckdb.DuckDBPyConnection:
    Path(settings.sync_db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(settings.sync_db)
    con.execute("""create table if not exists sync_log(
        sync_id varchar, sheet varchar, started_at timestamp, status varchar,
        rows_in int, rows_valid int, rows_error int, rows_merged int,
        deletes int, drift json, errors json, duration_ms double)""")
    con.execute("""create table if not exists snapshots(
        sheet varchar, snapshot_ts timestamp, content_hash varchar, n_rows int)""")
    con.execute("""create table if not exists row_lineage(
        sheet varchar, fingerprint varchar, first_seen timestamp,
        last_seen timestamp, deleted_at timestamp)""")
    return con


def _fingerprint(sheet: str, key_vals: tuple) -> str:
    return hashlib.sha1((sheet + "|" + "|".join(map(str, key_vals))).encode()).hexdigest()[:16]


# ---- parsing helpers ----

def _coerce(val: str, typ: str):
    v = (val or "").strip()
    if v == "":
        return None if typ != "str" else ""
    try:
        if typ == "int":
            return int(re.sub(r"[^0-9-]", "", v))
        if typ == "float":
            return float(re.sub(r"[^0-9.\-]", "", v.replace("Rp", "").replace(".", "").strip())) \
                if "Rp" in v or v.count(".") > 1 else float(re.sub(r"[^0-9.\-]", "", v))
        if typ == "date":
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y"):
                try:
                    return datetime.strptime(v, fmt).date().isoformat()
                except ValueError:
                    continue
            return None
        if typ == "bool":
            return v.lower() in ("y", "yes", "1", "true")
        return v
    except (ValueError, TypeError):
        return None


def suggest_mapping(unknown_header: str, contract: Contract, sample: list[str]) -> dict:
    """Heuristic mapping suggestion for a drifted/unknown column:
    fuzzy name match + value-shape signal. (Swap in an LLM here behind the
    same interface; deterministic keeps the demo keyless and testable.)"""
    candidates = [c.name for c in contract.columns]
    name_score = {c: difflib.SequenceMatcher(None, unknown_header.lower(), c).ratio()
                  for c in candidates}
    # value-shape: numeric magnitude hints at cash vs counts
    # (strip thousands dots: "Rp 2.829.192" -> 2829192)
    nums = []
    for s in sample[:20]:
        digits = re.sub(r"[^0-9]", "", s or "")
        if digits:
            nums.append(float(digits))
    avg = sum(nums) / len(nums) if nums else 0
    shape_bonus = {}
    for c in contract.columns:
        b = 0.0
        if c.type == "float" and avg > 10000:
            b = 0.25
        if c.type == "int" and 0 < avg < 200:
            b = 0.15
        shape_bonus[c.name] = b
    scored = sorted(candidates, key=lambda c: name_score[c] + shape_bonus[c], reverse=True)
    best = scored[0]
    conf = round(min(0.99, name_score[best] + shape_bonus[best]), 2)
    return {"unknown_header": unknown_header, "suggestion": best,
            "confidence": conf, "evidence": f"name~{name_score[best]:.2f}, avg_value~{avg:,.0f}"}


# ---- core sync ----

def _read_sheet(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r)
        rows = list(r)
    return header, rows


def resolve_contract(header: list[str]) -> Contract | None:
    """Pick the contract whose alias map best covers this sheet's headers,
    requiring all of its required columns to be present. Truly multi-contract;
    falls back to the sole contract if there is only one."""
    norm = [h.strip().lower() for h in header]
    best, best_score = None, -1
    for contract in CONTRACTS.values():
        amap = contract.alias_map()
        mapped = {amap[h] for h in norm if h in amap}
        required = {c.name for c in contract.columns if c.required}
        if not required.issubset(mapped):
            continue
        if len(mapped) > best_score:
            best, best_score = contract, len(mapped)
    if best is None and len(CONTRACTS) == 1:
        best = next(iter(CONTRACTS.values()))
    return best

def sync_sheet(sheet_file: Path, con: duckdb.DuckDBPyConnection) -> dict:
    t0 = datetime.now(timezone.utc)
    header, rows = _read_sheet(sheet_file)
    contract = resolve_contract(header)
    if contract is None:
        return {"sync_id": "", "sheet_file": sheet_file.name, "status": "error_no_contract",
                "rows_in": len(rows), "rows_valid": 0, "rows_error": 0, "rows_merged": 0,
                "deletes": 0, "drift": [], "errors": ["No matching contract found."]}
    sheet = contract.sheet
    content_hash = hashlib.sha1(json.dumps([header, rows]).encode()).hexdigest()[:16]

    sync_id = hashlib.sha1((str(sheet_file) + t0.isoformat()).encode()).hexdigest()[:10]
    result = {"sync_id": sync_id, "sheet_file": sheet_file.name, "status": "clean",
              "rows_in": len(rows), "rows_valid": 0, "rows_error": 0,
              "rows_merged": 0, "deletes": 0, "drift": [], "errors": []}

    # 1) skip unchanged (idempotent / cheap polling)
    prev = con.execute("select content_hash from snapshots where sheet=? and snapshot_ts="
                       "(select max(snapshot_ts) from snapshots where sheet=?)",
                       [sheet_file.name, sheet_file.name]).fetchone()
    if prev and prev[0] == content_hash:
        result["status"] = "unchanged"
        return result

    # 2) contract / drift check on headers
    amap = contract.alias_map()
    col_index, drift = {}, []
    for i, h in enumerate(header):
        canon = amap.get(h.strip().lower())
        if canon:
            col_index[canon] = i
        else:
            sample = [r[i] for r in rows[:20] if i < len(r)]
            sug = suggest_mapping(h, contract, sample)
            drift.append(sug)
    result["drift"] = drift
    missing_required = [c.name for c in contract.columns if c.required and c.name not in col_index]
    if drift or missing_required:
        result["status"] = "quarantined"
        result["errors"] = ([f"missing required: {m}" for m in missing_required] +
                            [f"unmapped header '{d['unknown_header']}' -> suggest "
                             f"'{d['suggestion']}' ({int(d['confidence']*100)}%)" for d in drift])
        _log(con, result, t0, content_hash, len(rows), commit_snapshot=False)
        return result

    # 3) row validation + typing
    typed = []
    for ridx, raw in enumerate(rows):
        rec, errs = {}, []
        for c in contract.columns:
            idx = col_index.get(c.name)
            val = _coerce(raw[idx] if idx is not None and idx < len(raw) else "", c.type)
            if c.required and (val is None or val == ""):
                errs.append(f"row {ridx+2}: {c.name} required")
            rec[c.name] = val
        if errs:
            result["rows_error"] += 1
            result["errors"].extend(errs[:3])
        else:
            typed.append(rec)
    result["rows_valid"] = len(typed)

    # 4) dedupe on natural key + MERGE into staging table
    seen, deduped = set(), []
    for rec in typed:
        kv = tuple(rec[k] for k in contract.key)
        if kv in seen:
            continue
        seen.add(kv)
        deduped.append((rec, kv))

    con.execute(f"""create table if not exists stg_{sheet}(
        {', '.join(c.name + ' ' + _ddl(c.type) for c in contract.columns)},
        _fingerprint varchar, _synced_at timestamp, _source_sheet varchar)""")

    now = t0
    fps_now = set()
    for rec, kv in deduped:
        fp = _fingerprint(sheet_file.name, kv)
        fps_now.add(fp)
        con.execute(f"delete from stg_{sheet} where _fingerprint=?", [fp])
        con.execute(
            f"insert into stg_{sheet} values ({', '.join(['?']*len(contract.columns))}, ?, ?, ?)",
            [rec[c.name] for c in contract.columns] + [fp, now, sheet_file.name])
        ln = con.execute("select fingerprint from row_lineage where fingerprint=?", [fp]).fetchone()
        if ln:
            con.execute("update row_lineage set last_seen=?, deleted_at=null where fingerprint=?", [now, fp])
        else:
            con.execute("insert into row_lineage values (?,?,?,?,null)",
                        [sheet_file.name, fp, now, now])
    result["rows_merged"] = len(deduped)

    # 5) deletion detection: rows previously live for this sheet but now absent
    live = {r[0] for r in con.execute(
        "select fingerprint from row_lineage where sheet=? and deleted_at is null", [sheet_file.name]).fetchall()}
    gone = live - fps_now
    for fp in gone:
        con.execute("update row_lineage set deleted_at=? where fingerprint=?", [now, fp])
        con.execute(f"delete from stg_{sheet} where _fingerprint=?", [fp])
    result["deletes"] = len(gone)
    if gone:
        result["status"] = "synced+deletes"

    _log(con, result, t0, content_hash, len(rows), commit_snapshot=True)
    return result


def _ddl(typ: str) -> str:
    return {"int": "bigint", "float": "double", "date": "date", "bool": "boolean"}.get(typ, "varchar")


def _log(con, result, t0, content_hash, n_rows, commit_snapshot):
    dt = (datetime.now(timezone.utc) - t0).total_seconds() * 1000
    con.execute("insert into sync_log values (?,?,?,?,?,?,?,?,?,?,?,?)", [
        result["sync_id"], result["sheet_file"], t0, result["status"],
        result["rows_in"], result["rows_valid"], result["rows_error"],
        result["rows_merged"], result["deletes"], json.dumps(result["drift"]),
        json.dumps(result["errors"][:8]), round(dt, 1)])
    if commit_snapshot:
        con.execute("insert into snapshots values (?,?,?,?)",
                    [result["sheet_file"], t0, content_hash, n_rows])


def sync_all() -> list[dict]:
    con = _db()
    files = sorted(SHEETS_DIR.glob("*.csv"))
    out = [sync_sheet(f, con) for f in files]
    con.close()
    return out


def status() -> dict:
    """Health snapshot per sheet for the UI."""
    if not Path(settings.sync_db).exists():
        return {"available": False}
    con = _db()
    sheets = []
    files = sorted(SHEETS_DIR.glob("*.csv"))
    for f in files:
        last = con.execute("""select status, rows_in, rows_valid, rows_error, rows_merged,
            deletes, drift, errors, started_at, duration_ms from sync_log
            where sheet=? order by started_at desc limit 1""", [f.name]).fetchone()
        if last:
            sheets.append({
                "sheet": f.name, "status": last[0], "rows_in": last[1],
                "rows_valid": last[2], "rows_error": last[3], "rows_merged": last[4],
                "deletes": last[5], "drift": json.loads(last[6] or "[]"),
                "errors": json.loads(last[7] or "[]"),
                "last_sync": str(last[8])[:19], "duration_ms": last[9],
            })
        else:
            sheets.append({"sheet": f.name, "status": "never", "rows_in": 0,
                           "drift": [], "errors": []})
    recent = con.execute("""select sync_id, sheet, status, rows_merged, deletes,
        started_at from sync_log order by started_at desc limit 12""").fetchall()
    totals = con.execute("""select count(*), sum(rows_merged), sum(deletes),
        count(*) filter (where status='quarantined') from sync_log""").fetchone()
    con.close()
    return {
        "available": True, "sheets": sheets,
        "recent": [{"sync_id": r[0], "sheet": r[1], "status": r[2],
                    "merged": r[3], "deletes": r[4], "at": str(r[5])[:19]} for r in recent],
        "totals": {"syncs": totals[0] or 0, "rows_merged": totals[1] or 0,
                   "deletes": totals[2] or 0, "quarantined": totals[3] or 0},
    }

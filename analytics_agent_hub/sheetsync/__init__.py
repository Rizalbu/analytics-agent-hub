"""Sheet Sync — governed spreadsheet→warehouse ingestion.

Reimplements (clean, anonymized) the pattern of treating Google Sheets as an
ops UI while keeping warehouse-grade trust: per-sheet contracts, header-drift
quarantine with mapping suggestions, row validation, idempotent MERGE,
snapshots/time-travel and deletion detection.

Default source is emulated 'studio sheets' (messy CSVs in data/sheets/) so the
demo runs with zero Google setup; a GoogleSheetsConnector is the drop-in
real-world option (see connectors.py).
"""

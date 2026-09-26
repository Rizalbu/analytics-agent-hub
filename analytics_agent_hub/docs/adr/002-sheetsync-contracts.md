# ADR 002: Sheetsync Contracts

## Context
The sheetsync pipeline ingests raw CSV exports from studio managers. Initially, the engine relied on filename matching (e.g., `sheet_file.name.startswith(k)`) to resolve the data contract. However, filenames are often inconsistent or renamed by users (e.g., `S01.csv`, `daily_log_jan.csv`), causing the sync to fail with `error_no_contract`.

## Decision
We switched to a **header-signature resolver** (content-based matching).
Instead of trusting the filename, the engine parses the first row (the header) and compares it against the `alias_map` of all known contracts. The contract that satisfies its required columns and achieves the highest match score is selected.

## Consequences
- **Robustness:** Sheets can be named anything. As long as the headers match the contract aliases, ingestion succeeds.
- **Multi-contract Support:** The system can truly handle multiple distinct sheet contracts within the same directory.
- **Drift Tolerance:** Unmapped columns (drift) are still captured and quarantined, preserving the schema validation logic without breaking the resolution step.

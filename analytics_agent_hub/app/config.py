"""Runtime configuration. All values come from env / .env with safe defaults.

No secrets in code. The warehouse defaults to the sibling funnel-warehouse
project's DuckDB; override with HUB_DB_PATH.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]


def _default_db() -> str:
    # sibling project built & verified earlier in this portfolio
    sibling = ROOT.parent / "funnel-warehouse" / "warehouse" / "funnel.duckdb"
    local = ROOT / "data" / "warehouse" / "funnel.duckdb"
    return str(sibling if sibling.exists() else local)


class Settings:
    db_path: str = os.getenv("HUB_DB_PATH", _default_db())
    dbt_target: str = os.getenv(
        "HUB_DBT_TARGET",
        str(ROOT.parent / "funnel-warehouse" / "dbt" / "target"),
    )
    sheets_dir: str = os.getenv("HUB_SHEETS_DIR", str(ROOT / "data" / "sheets"))
    sync_db: str = os.getenv("HUB_SYNC_DB", str(ROOT / "data" / "sync.duckdb"))

    # Optional tier-2 LLM (OpenAI-compatible). Absent => deterministic-only.
    agent_db_path: str = os.getenv("HUB_AGENT_DB", str(ROOT / "data" / "agent.duckdb"))

    llm_api_key: str | None = os.getenv("LLM_API_KEY") or None
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")

    rate_limit_per_min: int = int(os.getenv("HUB_RATE_LIMIT", "30"))
    company_name: str = "FitFlow Studios"
    currency: str = "Rp"

    @property
    def llm_enabled(self) -> bool:
        return self.llm_api_key is not None


settings = Settings()

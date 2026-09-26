import duckdb
from pathlib import Path
import sys
import os

# Add the project root to sys.path so we can import app.config
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from app.config import settings

def bootstrap(db_path: str):
    p = Path(db_path)
    if p.exists():
        print(f"Database already exists at {db_path}. Skipping bootstrap.")
        return

    print(f"Bootstrapping dummy warehouse at {db_path}...")
    p.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(p))

    schemas = ["main_marts", "main_intermediate", "main_seeds", "snapshots"]
    for s in schemas:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {s}")

    ddl = """
    CREATE TABLE main_marts.dim_studio (studio_key VARCHAR, studio_code VARCHAR, studio_name VARCHAR, city VARCHAR, capacity_tier VARCHAR);
    CREATE TABLE main_marts.dim_channel (channel_key VARCHAR, channel_name VARCHAR, channel_group VARCHAR);
    CREATE TABLE main_marts.dim_date (date_day DATE, year_month VARCHAR);
    CREATE TABLE main_marts.fct_funnel_daily (date_day DATE, studio_key VARCHAR, channel_key VARCHAR, leads INT, qualified INT, booked INT, visited INT, purchased INT);
    CREATE TABLE main_marts.fct_revenue (sold_date DATE, studio_key VARCHAR, channel_key VARCHAR, amount DOUBLE, lead_id VARCHAR, plan_name VARCHAR);
    CREATE TABLE main_marts.fct_ad_spend (date_day DATE, channel_key VARCHAR, spend DOUBLE);
    CREATE TABLE main_marts.mart_executive_scorecard (year_month VARCHAR, city VARCHAR, revenue DOUBLE, target_revenue DOUBLE, cr_lead_qualified_pct DOUBLE);
    CREATE TABLE main_marts.fct_targets (studio_key VARCHAR, target_revenue DOUBLE);
    CREATE TABLE main_intermediate.int_funnel_atomic (lead_id VARCHAR, created_date DATE, studio_code VARCHAR, channel_key VARCHAR);
    CREATE TABLE main_seeds.price_book (plan_code VARCHAR, plan_name VARCHAR, monthly_price DOUBLE, valid_from DATE, valid_to DATE);
    CREATE TABLE snapshots.snap_channel_mapping (channel_raw VARCHAR, channel_name VARCHAR, channel_group VARCHAR, dbt_valid_from TIMESTAMP, dbt_valid_to TIMESTAMP);
    """
    
    for stmt in ddl.strip().split(';'):
        if stmt.strip():
            con.execute(stmt)
            
    # Insert a dummy row so dimensions() doesn't fail completely with empty lists
    con.execute("INSERT INTO main_marts.dim_studio VALUES ('s1', 'DUMMY', 'Dummy Studio', 'Dummy City', 'Tier 1')")
    con.execute("INSERT INTO main_marts.dim_channel VALUES ('c1', 'Dummy Channel', 'Organic')")
    con.execute("INSERT INTO main_marts.dim_date VALUES ('2025-01-01', '2025-01')")
    con.execute("INSERT INTO main_marts.mart_executive_scorecard VALUES ('2025-01', 'Dummy City', 0, 0, 0)")
    
    con.close()
    print("Bootstrap complete. (Note: this is an empty shell for standalone mode).")

if __name__ == "__main__":
    bootstrap(settings.db_path)

PY = .venv/bin/python
DBT = ../.venv/bin/dbt

setup:
	uv venv -p 3.12 .venv && uv pip install -r requirements.txt

generate:
	$(PY) generator/generate.py --days 365

load:
	$(PY) pipeline/load_raw.py

build:
	cd dbt && $(DBT) build --profiles-dir .

dashboard:
	$(PY) dashboard/build_dashboard.py

demo: generate load build dashboard

scd2-demo:
	$(PY) scripts/demo_scd2.py

test:
	$(PY) -m pytest tests/ -q

docs:
	cd dbt && $(DBT) docs generate --profiles-dir .

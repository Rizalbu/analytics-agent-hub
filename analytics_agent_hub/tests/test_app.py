import os

os.chdir(os.path.dirname(os.path.dirname(__file__)))
os.makedirs("data", exist_ok=True)

from fastapi.testclient import TestClient

from app import app, ensure_schema

client = TestClient(app)
ensure_schema()


def _new_org():
    r = client.post("/api/orgs", json={"name": "Acme"})
    assert r.status_code == 200
    return r.json()


def test_create_org_and_kpis():
    org = _new_org()
    r = client.get("/api/kpis", params={"x_org_key": org["api_key"]})
    assert r.status_code == 200
    assert r.json()["leads"] > 0


def test_ask_routes_to_data_analyst():
    org = _new_org()
    r = client.post("/api/ask", params={"x_org_key": org["api_key"]}, json={"question": "revenue this month?"})
    assert r.json()["agent"] == "da"


def test_ask_routes_to_growth_manager():
    org = _new_org()
    r = client.post("/api/ask", params={"x_org_key": org["api_key"]}, json={"question": "how's our funnel retention?"})
    assert r.json()["agent"] == "gm"


def test_telegram_webhook():
    org = _new_org()
    payload = {"message": {"chat": {"id": 123}, "text": "revenue please"}}
    r = client.post(f"/webhooks/telegram/{org['api_key']}", json=payload)
    body = r.json()
    assert body["ok"] is True
    assert body["chat_id"] == 123

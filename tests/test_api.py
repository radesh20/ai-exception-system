import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(temp_store):
    from api.app import app
    from store import factory
    factory._store_instance = temp_store
    temp_store.save_policy({"category":"payment_mismatch","action_type":"three_way_match_recheck","success_rate":0.89,"avg_resolution_time":30,"sample_size":45})
    return TestClient(app)

def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"

def test_process(client, sample_raw):
    r = client.post("/api/process", json={"raw_input": sample_raw})
    assert r.status_code == 200
    assert "id" in r.json()

def test_stats(client):
    assert "total_exceptions" in client.get("/api/stats").json()
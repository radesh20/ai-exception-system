import os, sys, pytest, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture
def temp_store():
    from store.json_store import JsonStore
    with tempfile.TemporaryDirectory() as d:
        s = JsonStore(d)
        s.initialize()
        yield s

@pytest.fixture
def sample_raw():
    return {
        "case_id": "TEST-001",
        "event_log": [
            {"activity":"PO Created","timestamp":"2024-01-01T08:00:00","resource":"buyer"},
            {"activity":"GR Posted","timestamp":"2024-01-02T10:00:00","resource":"warehouse"},
            {"activity":"Payment Blocked","timestamp":"2024-01-03T08:00:00","resource":"system"}],
        "exception_alert": {"type":"payment_mismatch","triggered_at":"2024-01-03T08:00:00","financial_value":50000},
        "process_variants": [{"path":["PO Created","GR Posted","Invoice Received","Payment"],"frequency":0.8},
                             {"path":["PO Created","GR Posted","Payment Blocked"],"frequency":0.2}],
        "metadata": {"vendor":"TestV","po_value":50000,"sla_hours":48,"assigned_team":"AP","compliance_flag":False}}
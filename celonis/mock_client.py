import json, os

class MockCelonisClient:
    def __init__(self):
        self._data = {"cases": []}
        path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_input.json")
        if os.path.exists(path):
            with open(path) as f:
                content = f.read().strip()
                if content:
                    self._data = json.loads(content)

    def get_open_exceptions(self):
        return self._data.get("cases", [])

    def get_case_data(self, case_id):
        for c in self._data.get("cases", []):
            if c.get("case_id") == case_id:
                return c
        return {}

    def get_process_variants(self):
        return [
            {"path": ["PO Created", "GR Posted", "Invoice Received", "Payment"], "frequency": 0.72},
            {"path": ["PO Created", "Invoice Received", "GR Posted", "Payment"], "frequency": 0.18},
            {"path": ["PO Created", "GR Posted", "Invoice Received", "Payment Blocked", "Manual Review", "Payment"], "frequency": 0.10},
        ]
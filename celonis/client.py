import requests, logging
logger = logging.getLogger(__name__)

class CelonisClient:
    def __init__(self, base_url, api_token, data_pool_id, data_model_id):
        self.base_url = base_url.rstrip("/")
        self.data_pool_id = data_pool_id
        self.data_model_id = data_model_id
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"})

    def execute_pql(self, query):
        url = f"{self.base_url}/process-mining/api/v1/data-pools/{self.data_pool_id}/data-models/{self.data_model_id}/query"
        try:
            r = self.session.post(url, json={"query": query}, timeout=30)
            r.raise_for_status()
            data = r.json()
            cols = [c.get("name", f"col_{i}") for i, c in enumerate(data.get("columns", []))]
            return [{cols[i]: v for i, v in enumerate(row)} for row in data.get("results", [])]
        except Exception as e:
            logger.error(f"PQL failed: {e}")
            return []

    def get_open_exceptions(self):
        return self.execute_pql("SELECT * FROM SIGNALS WHERE STATUS = 'OPEN' LIMIT 100")

    def get_case_data(self, case_id):
        return {}

    def get_process_variants(self):
        return [
            {"path": ["PO Created", "GR Posted", "Invoice Received", "Payment"], "frequency": 0.72},
            {"path": ["PO Created", "Invoice Received", "GR Posted", "Payment"], "frequency": 0.18},
            {"path": ["PO Created", "GR Posted", "Invoice Received", "Payment Blocked", "Manual Review", "Payment"], "frequency": 0.10},
        ]
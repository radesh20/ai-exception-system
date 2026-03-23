import os, json, uuid
from datetime import datetime
from typing import Optional
from store.base import BaseStore
from models import ExceptionModel, ExceptionStatus, Decision, Action


class JsonStore(BaseStore):
    def __init__(self, base_path="data/db"):
        self.base_path = base_path
        self.files = {
            "exceptions": os.path.join(base_path, "exceptions.json"),
            "decisions":  os.path.join(base_path, "decisions.json"),
            "actions":    os.path.join(base_path, "actions.json"),
            "historical": os.path.join(base_path, "historical.json"),
            "policies":   os.path.join(base_path, "policies.json"),
            "processed_cases": os.path.join(base_path, "processed_celonis_cases.json"),
            "process_turnaround": os.path.join(base_path, "process_turnaround.json"),
            "agent_recommendations": os.path.join(base_path, "agent_recommendations.json"),
            "agent_interactions": os.path.join(base_path, "agent_interactions.json"),
            "process_insights": os.path.join(base_path, "process_insights.json"),
            "happy_path_cases": os.path.join(base_path, "happy_path_cases.json"),
        }

    def initialize(self):
        os.makedirs(self.base_path, exist_ok=True)
        for path in self.files.values():
            if not os.path.exists(path):
                self._write(path, [])

    def _read(self, path):
        try:
            with open(path, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _write(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _upsert(self, path, record, key):
        data = self._read(path)
        val = record.get(key)
        for i, item in enumerate(data):
            if item.get(key) == val:
                data[i] = record
                self._write(path, data)
                return
        data.append(record)
        self._write(path, data)

    def _append_unique(self, path, record, key):
        data = self._read(path)
        val = record.get(key)
        for item in data:
            if item.get(key) == val:
                return
        data.append(record)
        self._write(path, data)

    # ── Exceptions ──
    def save_exception(self, exc):
        exc.updated_at = datetime.now().isoformat()
        if not exc.id: exc.id = str(uuid.uuid4())
        self._upsert(self.files["exceptions"], exc.to_dict(), "id")
        return exc.id

    def get_exception(self, exc_id):
        for item in self._read(self.files["exceptions"]):
            if item.get("id") == exc_id:
                return ExceptionModel.from_dict(item)
        return None

    def list_exceptions(self, status=None, limit=500, offset=0):
        data = self._read(self.files["exceptions"])
        if status: data = [d for d in data if d.get("status") == status]
        data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return [ExceptionModel.from_dict(d) for d in data[offset:offset + limit]]

    def update_exception(self, exc):
        exc.updated_at = datetime.now().isoformat()
        data = self._read(self.files["exceptions"])
        for i, item in enumerate(data):
            if item.get("id") == exc.id:
                data[i] = exc.to_dict()
                self._write(self.files["exceptions"], data)
                return True
        return False

    # ── Decisions ──
    def save_decision(self, dec):
        if not dec.id: dec.id = str(uuid.uuid4())
        self._append_unique(self.files["decisions"], dec.to_dict(), "id")
        return dec.id

    def get_decisions(self, exception_id):
        return [Decision.from_dict(d) for d in self._read(self.files["decisions"]) if d.get("exception_id") == exception_id]

    def list_decisions(self, limit=100):
        data = sorted(self._read(self.files["decisions"]), key=lambda x: x.get("created_at", ""), reverse=True)
        return [Decision.from_dict(d) for d in data[:limit]]

    # ── Actions ──
    def save_action(self, action):
        if not action.id: action.id = str(uuid.uuid4())
        self._append_unique(self.files["actions"], action.to_dict(), "id")
        return action.id

    def get_actions(self, exception_id):
        return [Action.from_dict(d) for d in self._read(self.files["actions"]) if d.get("exception_id") == exception_id]

    def list_actions(self, limit=100):
        data = sorted(self._read(self.files["actions"]), key=lambda x: x.get("created_at", ""), reverse=True)
        return [Action.from_dict(d) for d in data[:limit]]

    # ── Historical ──
    def save_historical_case(self, case):
        if "id" not in case: case["id"] = str(uuid.uuid4())
        key = case.get("case_id") or case.get("id")
        data = self._read(self.files["historical"])
        for i, item in enumerate(data):
            if (item.get("case_id") or item.get("id")) == key:
                data[i] = case
                self._write(self.files["historical"], data)
                return case["id"]
        data.append(case)
        self._write(self.files["historical"], data)
        return case["id"]

    def get_historical_cases(self, exception_type=None):
        data = self._read(self.files["historical"])
        return [d for d in data if d.get("exception_type") == exception_type] if exception_type else data

    # ── Policies ──
    def save_policy(self, policy):
        data = self._read(self.files["policies"])
        for i, p in enumerate(data):
            if p.get("category") == policy.get("category") and p.get("action_type") == policy.get("action_type"):
                data[i] = policy
                self._write(self.files["policies"], data)
                return policy.get("category", "")
        data.append(policy)
        self._write(self.files["policies"], data)
        return policy.get("category", "")

    def get_policies(self, category=None):
        data = self._read(self.files["policies"])
        return [d for d in data if d.get("category") == category] if category else data

    def update_policy_stats(self, category, action, success):
        data = self._read(self.files["policies"])
        for p in data:
            if p.get("category") == category and p.get("action_type") == action:
                n = p.get("sample_size", 0)
                rate = p.get("success_rate", 0.0)
                p["sample_size"] = n + 1
                p["success_rate"] = round(((rate * n) + (1.0 if success else 0.0)) / (n + 1), 4)
                break
        self._write(self.files["policies"], data)

    # ── Processed Celonis Cases ──
    def mark_case_processed(self, case_id, exception_id, notification_sent=False, notification_sent_at=None):
        """Record that a Celonis case has been processed to prevent re-processing on subsequent runs."""
        now = datetime.now().isoformat()
        record = {
            "case_id": str(case_id),
            "exception_id": str(exception_id),
            "processed_at": now,
            "notification_sent": notification_sent,
            "notification_sent_at": notification_sent_at or (now if notification_sent else None),
        }
        self._upsert(self.files["processed_cases"], record, "case_id")

    def is_case_processed(self, case_id):
        """Return True if this Celonis case_id was already processed in a previous run."""
        case_id = str(case_id)
        for item in self._read(self.files["processed_cases"]):
            if item.get("case_id") == case_id:
                return True
        return False

    def get_processed_cases(self):
        """Return all processed case_id strings."""
        return [item["case_id"] for item in self._read(self.files["processed_cases"]) if "case_id" in item]

    # ── Stats ──
    def get_stats(self):
        exc = self._read(self.files["exceptions"])
        dec = self._read(self.files["decisions"])
        act = self._read(self.files["actions"])
        total = len(exc)
        pending = sum(1 for e in exc if e.get("status") == "pending_decision")
        completed = sum(1 for e in exc if e.get("status") == "completed")
        approved = sum(1 for d in dec if d.get("decision_type") == "approved")
        rejected = sum(1 for d in dec if d.get("decision_type") == "rejected")
        by_cat = {}
        for e in exc:
            cat = (e.get("classification") or {}).get("category", "unknown")
            by_cat[cat] = by_cat.get(cat, 0) + 1
        by_status = {}
        for e in exc:
            s = e.get("status", "unknown")
            by_status[s] = by_status.get(s, 0) + 1
        return {
            "total_exceptions": total, "pending_review": pending, "completed": completed,
            "total_decisions": len(dec), "approved": approved, "rejected": rejected,
            "approval_rate": round(approved / max(len(dec), 1), 3),
            "total_actions": len(act), "by_category": by_cat, "by_status": by_status,
        }

    # ── Process Turnaround ──
    def save_process_turnaround(self, data: dict):
        """Overwrite the full process turnaround snapshot."""
        self._write(self.files["process_turnaround"], data)

    def get_process_turnaround(self) -> dict:
        """Return the latest process turnaround snapshot (dict) or empty dict."""
        raw = self._read(self.files["process_turnaround"])
        if isinstance(raw, dict):
            return raw
        # File was initialised as [] — return empty dict
        return {}

    # ── Agent Recommendations ──
    def save_agent_recommendations(self, recommendations: list):
        """Overwrite the agent recommendations list."""
        self._write(self.files["agent_recommendations"], recommendations)

    def get_agent_recommendations(self) -> list:
        """Return the latest agent recommendations list."""
        raw = self._read(self.files["agent_recommendations"])
        return raw if isinstance(raw, list) else []

    # ── Agent Interaction Traces ──
    def save_agent_interaction(self, interaction: dict):
        """Append a full agent interaction trace record."""
        if "id" not in interaction:
            interaction["id"] = str(uuid.uuid4())
        self._append_unique(self.files["agent_interactions"], interaction, "id")

    def get_agent_interactions(self, exception_id: str = None) -> list:
        """Return all agent interaction traces, optionally filtered by exception_id."""
        data = self._read(self.files["agent_interactions"])
        if not isinstance(data, list):
            return []
        if exception_id:
            return [d for d in data if d.get("exception_id") == exception_id]
        return data

    # ── Process Insights ──
    def save_process_insight(self, insight: dict):
        """Append a process insight record."""
        if "id" not in insight:
            insight["id"] = str(uuid.uuid4())
        if "recorded_at" not in insight:
            insight["recorded_at"] = datetime.now().isoformat()
        self._append_unique(self.files["process_insights"], insight, "id")

    def save_process_insights(self, case_id: str, insights: dict):
        """Upsert a process insights record keyed by case_id."""
        if "id" not in insights:
            insights["id"] = str(uuid.uuid4())
        if "recorded_at" not in insights:
            insights["recorded_at"] = datetime.now().isoformat()
        insights["case_id"] = case_id
        self._upsert(self.files["process_insights"], insights, "case_id")

    def get_process_insights(self, limit: int = 200) -> list:
        """Return the most recent process insights."""
        data = self._read(self.files["process_insights"])
        if not isinstance(data, list):
            return []
        return sorted(data, key=lambda x: x.get("recorded_at", ""), reverse=True)[:limit]

    def get_process_insight(self, case_id: str) -> dict:
        """Return the process insight record for a specific case_id."""
        for item in self._read(self.files["process_insights"]):
            if item.get("case_id") == case_id:
                return item
        return {}

    # ── Happy Path Cases ──
    def save_happy_path_case(self, case: dict):
        """Upsert a happy path case record keyed by context.case_id."""
        key = (case.get("context") or {}).get("case_id") or case.get("case_id") or case.get("id", "")
        if not key:
            key = str(uuid.uuid4())
        case["_happy_path_key"] = key
        self._upsert(self.files["happy_path_cases"], case, "_happy_path_key")

    def get_happy_path_cases(self, limit: int = 200, offset: int = 0) -> list:
        """Return happy path cases sorted by created_at descending."""
        data = self._read(self.files["happy_path_cases"])
        if not isinstance(data, list):
            return []
        data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return data[offset: offset + limit]

    def get_happy_path_case(self, case_id: str) -> dict:
        """Return a single happy path case by context.case_id or exception id."""
        for item in self._read(self.files["happy_path_cases"]):
            ctx = item.get("context") or {}
            if ctx.get("case_id") == case_id or item.get("id") == case_id:
                return item
        return {}
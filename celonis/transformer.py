from datetime import datetime, timedelta
from models import ExceptionContext

class CelonisTransformer:
    @staticmethod
    def transform(raw):
        event_log = raw.get("event_log", [])
        alert = raw.get("exception_alert", {})
        metadata = raw.get("metadata", {})
        variants = raw.get("process_variants", [])

        actual_path = [e.get("activity", "") for e in event_log]
        happy_path = max(variants, key=lambda v: v.get("frequency", 0)).get("path", []) if variants else []

        deviation = "no_deviation"
        for i, (a, h) in enumerate(zip(actual_path, happy_path)):
            if a != h:
                deviation = a
                break
        if len(actual_path) > len(happy_path):
            deviation = actual_path[len(happy_path)]

        financial = float(alert.get("financial_value", 0))
        sla_hours = int(metadata.get("sla_hours", 48))
        triggered = alert.get("triggered_at", datetime.now().isoformat())
        try:
            trigger_dt = datetime.fromisoformat(triggered.replace("Z", "+00:00"))
        except:
            trigger_dt = datetime.now()
        deadline = trigger_dt + timedelta(hours=sla_hours)
        hours_left = max(0, (deadline - datetime.now()).total_seconds() / 3600)
        severity = min(1.0, max(0.0, (financial / 100000) * 0.6 + (hours_left / 48) * 0.4))

        return ExceptionContext(
            case_id=raw.get("case_id", ""), exception_type=alert.get("type", "unknown"),
            financial_exposure=financial, severity_score=round(severity, 3),
            deviation_point=deviation, actual_path=actual_path, happy_path=happy_path,
            assigned_team=metadata.get("assigned_team", "Unassigned"),
            vendor=metadata.get("vendor", "Unknown"), sla_hours=sla_hours,
            compliance_flag=bool(metadata.get("compliance_flag", False)),
            timestamp=triggered, raw_data=raw)
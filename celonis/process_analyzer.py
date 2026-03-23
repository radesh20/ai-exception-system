"""
Process Analyzer — pulls enriched P2P data from Celonis and computes
structured turnaround metrics used by path classification, prompt
enrichment, and escalation prediction.
"""
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

import config.settings as settings

logger = logging.getLogger(__name__)


class ProcessAnalyzer:
    """
    Fetches the full P2P activity stream and computes:
      - Per-vendor statistics
      - Per-case / PO stage breakdown
      - Per-activity throughput metrics
      - Per-exception-type resolution stats
      - Overall process health
    """

    # Average stage durations (days) used when no live data is available
    _DEFAULT_STAGE_DAYS = {
        "Purchase Requisition Created": 1.0,
        "Purchase Order Created": 2.0,
        "Invoice Received": 3.0,
        "Payment Open": 5.0,
        "Invoice Cleared": 1.5,
    }

    # Typical happy-path P2P sequence
    HAPPY_PATH = [
        "Purchase Requisition Created",
        "Purchase Order Created",
        "Invoice Received",
        "Invoice Cleared",
    ]

    def __init__(self):
        self._client = None
        self._raw_cases: list = []

    # ─────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────

    def fetch_and_analyze(self) -> dict:
        """
        Main entry point.  Fetches cases from Celonis (or mock),
        computes all metrics, and returns a structured dict.
        """
        self._raw_cases = self._fetch_cases()
        logger.info("[INFO] ProcessAnalyzer: fetched %d raw cases", len(self._raw_cases))

        result = {
            "fetched_at": datetime.now().isoformat(),
            "case_count": len(self._raw_cases),
            "vendor_stats": self._vendor_stats(),
            "case_stats": self._case_stats(),
            "activity_stats": self._activity_stats(),
            "exception_type_stats": self._exception_type_stats(),
            "process_health": self._process_health(),
        }
        logger.info("[OK] ProcessAnalyzer: analysis complete")
        return result

    # ─────────────────────────────────────────────────────────
    # DATA FETCH
    # ─────────────────────────────────────────────────────────

    def _fetch_cases(self) -> list:
        try:
            from celonis import get_celonis_client
            client = get_celonis_client()
            cases = client.get_open_exceptions()
            if cases:
                return cases
        except Exception as exc:
            logger.warning("[WARN] ProcessAnalyzer: Celonis fetch failed (%s). Using mock.", exc)

        # Fallback: generate synthetic cases for analysis
        return self._synthetic_cases()

    def _synthetic_cases(self) -> list:
        """Return lightweight synthetic cases when Celonis is unavailable."""
        import random
        random.seed(42)
        vendors = ["VendorA", "VendorB", "VendorC", "VendorI9", "VendorN14"]
        exc_types = ["payment_mismatch", "quantity_mismatch", "invoice_mismatch",
                     "goods_receipt_mismatch", "tax_code_change"]
        cases = []
        for i in range(30):
            vendor = vendors[i % len(vendors)]
            exc_type = exc_types[i % len(exc_types)]
            base = datetime.now() - timedelta(days=random.randint(1, 30))
            event_log = [
                {"activity": "Purchase Requisition Created",
                 "timestamp": (base).isoformat(), "resource": "procurement"},
                {"activity": "Purchase Order Created",
                 "timestamp": (base + timedelta(days=1)).isoformat(), "resource": "procurement"},
                {"activity": "Invoice Received",
                 "timestamp": (base + timedelta(days=random.uniform(2, 8))).isoformat(),
                 "resource": "ap_team"},
                {"activity": "Payment Open",
                 "timestamp": (base + timedelta(days=random.uniform(8, 15))).isoformat(),
                 "resource": "system"},
            ]
            cases.append({
                "case_id": f"CASE_{i:04d}",
                "event_log": event_log,
                "exception_alert": {
                    "type": exc_type,
                    "triggered_at": event_log[-1]["timestamp"],
                    "financial_value": round(random.uniform(5000, 200000), 2),
                },
                "metadata": {
                    "vendor": vendor,
                    "po_value": round(random.uniform(5000, 200000), 2),
                    "sla_hours": 48,
                    "assigned_team": f"AP_Team_{i % 3 + 1}",
                    "compliance_flag": random.random() > 0.85,
                },
            })
        return cases

    # ─────────────────────────────────────────────────────────
    # VENDOR STATS
    # ─────────────────────────────────────────────────────────

    def _vendor_stats(self) -> dict:
        """Per-vendor aggregated metrics."""
        stats: dict = defaultdict(lambda: {
            "case_count": 0,
            "total_cycle_days": 0.0,
            "stage_totals": defaultdict(float),
            "stage_counts": defaultdict(int),
            "payment_delays": 0,
            "exception_type_counts": defaultdict(int),
            "exception_type_resolved": defaultdict(int),
            "deviation_points": defaultdict(int),
            "advance_days_needed": [],
        })

        for case in self._raw_cases:
            vendor = (case.get("metadata") or {}).get("vendor") or "Unknown"
            v = stats[vendor]
            v["case_count"] += 1

            exc_type = (case.get("exception_alert") or {}).get("type", "unknown")
            v["exception_type_counts"][exc_type] += 1

            events = case.get("event_log") or []
            cycle = self._cycle_days(events)
            if cycle is not None:
                v["total_cycle_days"] += cycle

            for i in range(len(events) - 1):
                a, b = events[i], events[i + 1]
                delta = self._ts_diff_days(a.get("timestamp"), b.get("timestamp"))
                if delta is not None:
                    stage = a.get("activity", "unknown")
                    v["stage_totals"][stage] += delta
                    v["stage_counts"][stage] += 1

            # Detect payment delay — any path that includes "Payment Open"
            activities = [e.get("activity", "") for e in events]
            if "Payment Open" in activities:
                v["payment_delays"] += 1

        result = {}
        for vendor, v in stats.items():
            cnt = v["case_count"] or 1
            avg_cycle = round(v["total_cycle_days"] / cnt, 2)

            stage_avg = {}
            for stage, total in v["stage_totals"].items():
                n = v["stage_counts"][stage] or 1
                stage_avg[stage] = round(total / n, 2)

            exc_success = {}
            for exc_type, total in v["exception_type_counts"].items():
                resolved = v["exception_type_resolved"].get(exc_type, 0)
                exc_success[exc_type] = round(resolved / total, 3) if total else 0.0

            result[vendor] = {
                "case_count": v["case_count"],
                "avg_cycle_days": avg_cycle,
                "avg_stage_days": stage_avg,
                "payment_delay_frequency": round(v["payment_delays"] / cnt, 3),
                "advance_initiation_days": round(
                    sum(v["advance_days_needed"]) / len(v["advance_days_needed"]), 2
                ) if v["advance_days_needed"] else avg_cycle,
                "exception_type_success_rate": exc_success,
                "common_deviation_points": dict(sorted(
                    v["deviation_points"].items(), key=lambda x: -x[1]
                )[:3]),
            }

        return result

    # ─────────────────────────────────────────────────────────
    # CASE STATS
    # ─────────────────────────────────────────────────────────

    def _case_stats(self) -> list:
        """Per-case stage breakdown and risk score."""
        results = []
        for case in self._raw_cases:
            events = case.get("event_log") or []
            case_id = case.get("case_id", "unknown")
            vendor = (case.get("metadata") or {}).get("vendor", "Unknown")
            exc_type = (case.get("exception_alert") or {}).get("type", "unknown")
            financial_value = (case.get("exception_alert") or {}).get("financial_value", 0)

            stage_durations = {}
            for i in range(len(events) - 1):
                delta = self._ts_diff_days(
                    events[i].get("timestamp"), events[i + 1].get("timestamp")
                )
                if delta is not None:
                    stage_durations[events[i].get("activity", f"stage_{i}")] = round(delta, 2)

            # Risk score: blend of cycle position vs happy path and financial exposure
            cycle = self._cycle_days(events)
            expected = sum(self._DEFAULT_STAGE_DAYS.values())
            if cycle is not None and expected > 0:
                delay_ratio = min(cycle / expected, 3.0)
            else:
                delay_ratio = 1.0

            exp_norm = min(financial_value / 200000.0, 1.0)
            risk_score = round(min(delay_ratio * 0.5 + exp_norm * 0.5, 1.0), 3)

            # Compare to happy path
            actual_activities = [e.get("activity") for e in events]
            happy_path_match = all(step in actual_activities for step in self.HAPPY_PATH[:2])

            results.append({
                "case_id": case_id,
                "vendor": vendor,
                "exception_type": exc_type,
                "financial_value": financial_value,
                "stage_durations": stage_durations,
                "total_cycle_days": cycle,
                "happy_path_match": happy_path_match,
                "risk_score": risk_score,
            })

        return results

    # ─────────────────────────────────────────────────────────
    # ACTIVITY STATS
    # ─────────────────────────────────────────────────────────

    def _activity_stats(self) -> dict:
        """Per-activity throughput and bottleneck metrics."""
        totals: dict = defaultdict(float)
        counts: dict = defaultdict(int)
        team_counts: dict = defaultdict(lambda: defaultdict(int))

        for case in self._raw_cases:
            events = case.get("event_log") or []
            for i in range(len(events) - 1):
                delta = self._ts_diff_days(
                    events[i].get("timestamp"), events[i + 1].get("timestamp")
                )
                activity = events[i].get("activity", "unknown")
                resource = events[i].get("resource", "system")
                if delta is not None:
                    totals[activity] += delta
                    counts[activity] += 1
                    team_counts[activity][resource] += 1

        total_cases = len(self._raw_cases) or 1
        result = {}
        for activity, total in totals.items():
            n = counts[activity] or 1
            avg_days = round(total / n, 2)
            expected = self._DEFAULT_STAGE_DAYS.get(activity, 3.0)
            bottleneck_freq = round(min(avg_days / expected, 1.0), 3) if expected else 0.0
            primary_team = max(team_counts[activity], key=team_counts[activity].get) if team_counts[activity] else "unknown"
            result[activity] = {
                "avg_processing_days": avg_days,
                "case_count": counts[activity],
                "bottleneck_frequency": bottleneck_freq,
                "primary_team": primary_team,
                "team_breakdown": dict(team_counts[activity]),
                "occurrence_rate": round(counts[activity] / total_cases, 3),
            }

        return result

    # ─────────────────────────────────────────────────────────
    # EXCEPTION TYPE STATS
    # ─────────────────────────────────────────────────────────

    def _exception_type_stats(self) -> dict:
        """Per-exception-type resolution and clustering metrics."""
        counts: dict = defaultdict(int)
        vendor_counts: dict = defaultdict(lambda: defaultdict(int))
        team_counts: dict = defaultdict(lambda: defaultdict(int))
        cycle_totals: dict = defaultdict(float)
        cycle_case_counts: dict = defaultdict(int)

        for case in self._raw_cases:
            exc_type = (case.get("exception_alert") or {}).get("type", "unknown")
            vendor = (case.get("metadata") or {}).get("vendor", "Unknown")
            team = (case.get("metadata") or {}).get("assigned_team", "unknown")

            counts[exc_type] += 1
            vendor_counts[exc_type][vendor] += 1
            team_counts[exc_type][team] += 1

            events = case.get("event_log") or []
            cycle = self._cycle_days(events)
            if cycle is not None:
                cycle_totals[exc_type] += cycle
                cycle_case_counts[exc_type] += 1

        result = {}
        for exc_type, total in counts.items():
            n = cycle_case_counts.get(exc_type, 0)
            avg_resolution = round(cycle_totals[exc_type] / n, 2) if n else 0.0
            top_vendors = sorted(vendor_counts[exc_type].items(), key=lambda x: -x[1])[:3]
            top_teams = sorted(team_counts[exc_type].items(), key=lambda x: -x[1])[:3]

            # Recurrence: vendor cases that see this type more than once
            recurrence = {}
            for vendor, cnt in vendor_counts[exc_type].items():
                if cnt > 1:
                    recurrence[vendor] = cnt

            result[exc_type] = {
                "total_cases": total,
                "avg_resolution_days": avg_resolution,
                "highest_success_action": self._default_action(exc_type),
                "top_vendors": dict(top_vendors),
                "top_teams": dict(top_teams),
                "recurrence_per_vendor": recurrence,
            }

        return result

    # ─────────────────────────────────────────────────────────
    # PROCESS HEALTH
    # ─────────────────────────────────────────────────────────

    def _process_health(self) -> dict:
        """Overall P2P process health metrics."""
        if not self._raw_cases:
            return {
                "sla_compliance_rate": 0.0,
                "avg_end_to_end_days": 0.0,
                "delay_causing_stages": [],
                "problematic_vendors": [],
            }

        sla_ok = 0
        cycle_total = 0.0
        cycle_count = 0
        stage_delay: dict = defaultdict(float)
        stage_cnt: dict = defaultdict(int)
        vendor_delay: dict = defaultdict(int)

        for case in self._raw_cases:
            events = case.get("event_log") or []
            sla_hours = (case.get("metadata") or {}).get("sla_hours", 48)
            vendor = (case.get("metadata") or {}).get("vendor", "Unknown")

            cycle = self._cycle_days(events)
            if cycle is not None:
                cycle_total += cycle
                cycle_count += 1
                if cycle <= sla_hours / 24.0:
                    sla_ok += 1
                else:
                    vendor_delay[vendor] += 1

            for i in range(len(events) - 1):
                delta = self._ts_diff_days(
                    events[i].get("timestamp"), events[i + 1].get("timestamp")
                )
                if delta is not None:
                    stage = events[i].get("activity", "unknown")
                    expected = self._DEFAULT_STAGE_DAYS.get(stage, 3.0)
                    if delta > expected:
                        stage_delay[stage] += delta - expected
                        stage_cnt[stage] += 1

        total = len(self._raw_cases)
        sla_rate = round(sla_ok / total, 3) if total else 0.0
        avg_e2e = round(cycle_total / cycle_count, 2) if cycle_count else 0.0

        delay_stages = sorted(
            [(s, round(stage_delay[s] / (stage_cnt[s] or 1), 2)) for s in stage_delay],
            key=lambda x: -x[1],
        )[:5]

        problematic = sorted(vendor_delay.items(), key=lambda x: -x[1])[:5]

        return {
            "sla_compliance_rate": sla_rate,
            "avg_end_to_end_days": avg_e2e,
            "delay_causing_stages": [{"stage": s, "avg_excess_days": d} for s, d in delay_stages],
            "problematic_vendors": [{"vendor": v, "delay_cases": c} for v, c in problematic],
        }

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _ts_diff_days(ts_a: Optional[str], ts_b: Optional[str]) -> Optional[float]:
        """Return difference in days between two ISO timestamps, or None."""
        if not ts_a or not ts_b:
            return None
        try:
            fmt_a = ts_a.replace("Z", "").replace("+00:00", "")
            fmt_b = ts_b.replace("Z", "").replace("+00:00", "")
            a = datetime.fromisoformat(fmt_a)
            b = datetime.fromisoformat(fmt_b)
            return abs((b - a).total_seconds() / 86400)
        except Exception:
            return None

    @staticmethod
    def _cycle_days(events: list) -> Optional[float]:
        """Total cycle time from first to last event in days."""
        if len(events) < 2:
            return None
        timestamps = [e.get("timestamp") for e in events if e.get("timestamp")]
        if len(timestamps) < 2:
            return None
        try:
            parsed = [
                datetime.fromisoformat(t.replace("Z", "").replace("+00:00", ""))
                for t in timestamps
            ]
            return abs((parsed[-1] - parsed[0]).total_seconds() / 86400)
        except Exception:
            return None

    @staticmethod
    def _default_action(exc_type: str) -> str:
        defaults = {
            "payment_mismatch": "three_way_match_recheck",
            "quantity_mismatch": "adjust_quantity",
            "invoice_mismatch": "request_invoice_correction",
            "goods_receipt_mismatch": "reverse_and_repost_gr",
            "tax_code_change": "update_tax_code",
        }
        return defaults.get(exc_type, "escalate_to_human")

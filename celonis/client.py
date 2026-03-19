# celonis/client.py
"""
Celonis live client using PyCelonis.

Uses verified working object-table aliases:
  "o_custom_VendorMaster"
  "o_custom_PurchasingDocumentItem"
  "o_custom_PurchasingDocumentHeader"
  "o_custom_AccountingDocumentSegment"
  "o_custom_ApBsegOpen"
  "o_custom_DocumentItemIncomingInvoice"
  "o_custom_PurchaseRequisition"

Event tables (e_custom_*) are NOT directly queryable in PQL
for this perspective model, so we derive process state from objects.
"""

import os
import math
import logging
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger(__name__)

# Verified working PQL aliases
T_VENDOR     = "o_custom_VendorMaster"
T_PO_ITEM    = "o_custom_PurchasingDocumentItem"
T_PO_HEADER  = "o_custom_PurchasingDocumentHeader"
T_ACCT_SEG   = "o_custom_AccountingDocumentSegment"
T_AP_OPEN    = "o_custom_ApBsegOpen"
T_INVOICE    = "o_custom_DocumentItemIncomingInvoice"
T_PURCH_REQ  = "o_custom_PurchaseRequisition"


class CelonisClient:
    def __init__(self, base_url, api_token, data_pool_id, data_model_id):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.data_pool_id = data_pool_id
        self.data_model_id = data_model_id
        self._celonis = None
        self._pool = None
        self._data_model = None
        self._connect()

    # ─────────────────────────────────────────────
    # CONNECTION
    # ─────────────────────────────────────────────
    def _connect(self):
        """Connect using PyCelonis."""
        try:
            from pycelonis import get_celonis

            os.environ["CELONIS_URL"] = self.base_url
            os.environ["CELONIS_API_TOKEN"] = self.api_token

            self._celonis = get_celonis(
                base_url=self.base_url,
                api_token=self.api_token,
                key_type="USER_KEY"
            )

            # Resolve pool
            if hasattr(self._celonis, "data_integration"):
                for p in self._celonis.data_integration.get_data_pools():
                    if p.id == self.data_pool_id:
                        self._pool = p
                        break

            if not self._pool:
                raise ValueError(f"Pool not found: {self.data_pool_id}")

            # Resolve model
            for m in self._pool.get_data_models():
                if m.id == self.data_model_id:
                    self._data_model = m
                    break

            if not self._data_model:
                raise ValueError(f"Data model not found: {self.data_model_id}")

            logger.info("Connected to Celonis | Model: %s", self._data_model.name)

        except Exception as e:
            logger.error("Failed to connect to Celonis: %s", e, exc_info=True)
            raise

    # ─────────────────────────────────────────────
    # PQL EXECUTION
    # ─────────────────────────────────────────────
    def execute_pql(self, columns, limit=1000):
        """
        Execute PQL using column tuples.
        columns: list of (pql_expression, alias_name)
        """
        try:
            import pycelonis.pql as pql
            from pycelonis.pql import DataFrame

            query = pql.PQL()
            for expr, name in columns:
                query += pql.PQLColumn(query=expr, name=name)
            query.limit = limit

            df = DataFrame.from_pql(query, data_model=self._data_model)
            pdf = df.to_pandas()
            return pdf.to_dict("records") if pdf is not None and not pdf.empty else []

        except Exception as e:
            logger.error("PQL failed: %s", e, exc_info=True)
            return []

    # ─────────────────────────────────────────────
    # RAW DATA QUERIES
    # ─────────────────────────────────────────────
    def get_vendor_data(self, limit=500):
        return self.execute_pql([
            (f'"{T_VENDOR}"."ID"', 'vendor_id'),
            (f'"{T_VENDOR}"."LIFNR"', 'vendor_number'),
            (f'"{T_VENDOR}"."NAME1"', 'vendor_name'),
            (f'"{T_VENDOR}"."LAND1"', 'vendor_country'),
        ], limit)

    def get_po_data(self, limit=500):
        return self.execute_pql([
            (f'"{T_PO_ITEM}"."ID"', 'po_item_id'),
            (f'"{T_PO_ITEM}"."EBELN"', 'po_number'),
            (f'"{T_PO_ITEM}"."EBELP"', 'po_item'),
            (f'"{T_PO_ITEM}"."NETWR"', 'po_net_value'),
            (f'"{T_PO_ITEM}"."NetwrConverted"', 'po_net_value_converted'),
            (f'"{T_PO_ITEM}"."MENGE"', 'po_quantity'),
            (f'"{T_PO_ITEM}"."PurchasingDocumentHeader_ID"', 'po_header_ref'),
        ], limit)

    def get_invoice_data(self, limit=500):
        return self.execute_pql([
            (f'"{T_INVOICE}"."ID"', 'invoice_id'),
            (f'"{T_INVOICE}"."BELNR"', 'invoice_number'),
            (f'"{T_INVOICE}"."WRBTR"', 'invoice_amount'),
            (f'"{T_INVOICE}"."GJAHR"', 'fiscal_year'),
            (f'"{T_INVOICE}"."MENGE"', 'invoice_quantity'),
            (f'"{T_INVOICE}"."CaseKey"', 'case_key'),
            (f'"{T_INVOICE}"."PurchasingDocumentItem_ID"', 'po_item_ref'),
            (f'"{T_INVOICE}"."AccountingDocumentSegment_ID"', 'acct_seg_ref'),
        ], limit)

    def get_open_ap_items(self, limit=500):
        return self.execute_pql([
            (f'"{T_AP_OPEN}"."ID"', 'open_item_id'),
            (f'"{T_AP_OPEN}"."BUKRS"', 'company_code'),
            (f'"{T_AP_OPEN}"."BUZEI"', 'line_item'),
            (f'"{T_AP_OPEN}"."AccountingDocumentSegment_ID"', 'acct_seg_ref'),
        ], limit)

    def get_accounting_segments(self, limit=500):
        return self.execute_pql([
            (f'"{T_ACCT_SEG}"."ID"', 'acct_seg_id'),
            (f'"{T_ACCT_SEG}"."BUKRS"', 'acct_company_code'),
            (f'"{T_ACCT_SEG}"."VendorMaster_ID"', 'vendor_ref'),
        ], limit)

    def get_purchase_requisitions(self, limit=500):
        return self.execute_pql([
            (f'"{T_PURCH_REQ}"."ID"', 'pr_id'),
            (f'"{T_PURCH_REQ}"."BNFPO"', 'pr_item'),
            (f'"{T_PURCH_REQ}"."PurchasingDocumentItem_ID"', 'po_item_ref'),
        ], limit)

    def get_tables(self):
        try:
            return [t.name for t in self._data_model.get_tables()]
        except Exception:
            return []

    # ─────────────────────────────────────────────
    # ENRICH CASES
    # ─────────────────────────────────────────────
    def _build_enriched_cases(self):
        """Join invoice + PO + vendor + AP open + PR data."""
        invoices = self.get_invoice_data(limit=50000)
        if not invoices:
            logger.info("No invoice data from Celonis")
            return []

        open_ap = {r.get("acct_seg_ref"): r for r in self.get_open_ap_items(limit=5000)}
        acct_segs = {r.get("acct_seg_id"): r for r in self.get_accounting_segments(limit=5000)}
        vendors = {r.get("vendor_id"): r for r in self.get_vendor_data(limit=5000)}
        po_items = {r.get("po_item_id"): r for r in self.get_po_data(limit=5000)}
        prs = {r.get("po_item_ref"): r for r in self.get_purchase_requisitions(limit=5000)}

        enriched = []
        for inv in invoices:
            case = dict(inv)

            seg_id = inv.get("acct_seg_ref")
            seg = acct_segs.get(seg_id, {})
            case["company_code"] = seg.get("acct_company_code", "")
            case["vendor_ref"] = seg.get("vendor_ref", "")

            vendor = vendors.get(seg.get("vendor_ref", ""), {})
            case["vendor_number"] = vendor.get("vendor_number", "")
            case["vendor_name"] = vendor.get("vendor_name", "Unknown")
            case["vendor_country"] = vendor.get("vendor_country", "")

            po_ref = inv.get("po_item_ref")
            po = po_items.get(po_ref, {})
            case["po_number"] = po.get("po_number", "")
            case["po_item"] = po.get("po_item", "")
            case["po_net_value"] = po.get("po_net_value", 0)
            case["po_net_value_converted"] = po.get("po_net_value_converted", 0)
            case["po_quantity"] = po.get("po_quantity", 0)

            pr = prs.get(po_ref, {})
            case["pr_id"] = pr.get("pr_id", "")
            case["has_pr"] = bool(pr)

            ap = open_ap.get(seg_id, {})
            case["has_open_ap"] = bool(ap)
            case["open_item_id"] = ap.get("open_item_id", "")
            case["open_company_code"] = ap.get("company_code", "")

            enriched.append(case)

        logger.info("Enriched %d invoice cases from Celonis", len(enriched))
        return enriched

    # ─────────────────────────────────────────────
    # PROCESS VARIANTS
    # ─────────────────────────────────────────────
    def get_process_variants(self):
        """Derive process path variants from object presence."""
        enriched = self._build_enriched_cases()
        if not enriched:
            return []

        paths = []
        for case in enriched:
            path = []
            if case.get("has_pr"):          path.append("Purchase Requisition Created")
            if case.get("po_number"):       path.append("Purchase Order Created")
            if case.get("invoice_number"):  path.append("Invoice Received")
            if case.get("has_open_ap"):     path.append("Payment Open")
            elif case.get("invoice_number"): path.append("Invoice Cleared")
            if not path:                    path = ["Unknown State"]
            paths.append(tuple(path))

        counts = Counter(paths)
        total = sum(counts.values()) or 1
        return [
            {"path": list(p), "frequency": round(c / total, 4)}
            for p, c in counts.most_common()
        ]

    # ─────────────────────────────────────────────
    # EVENT LOG
    # ─────────────────────────────────────────────
    def _build_event_log(self, case):
        """Build synthetic event log from object state."""
        base_time = datetime.now().replace(microsecond=0)
        events = []
        step = 0

        def add(cond, activity, resource="system"):
            nonlocal step
            if cond:
                events.append({
                    "activity": activity,
                    "timestamp": (base_time - timedelta(days=(30 - step))).isoformat(),
                    "resource": resource,
                })
                step += 1

        add(case.get("has_pr"), "Purchase Requisition Created", "procurement")
        add(case.get("po_number"), "Purchase Order Created", "procurement")
        add(case.get("invoice_number"), "Invoice Received", "ap_team")
        add(case.get("has_open_ap"), "Payment Open", "system")
        add(not case.get("has_open_ap") and case.get("invoice_number"), "Invoice Cleared", "system")

        if not events:
            events.append({"activity": "Unknown State", "timestamp": base_time.isoformat(), "resource": "system"})
        return events

    # ─────────────────────────────────────────────
    # EXCEPTION TYPE
    # ─────────────────────────────────────────────
    def _map_exception_type(self, case):
        has_open_ap = case.get("has_open_ap", False)
        has_invoice = bool(case.get("invoice_number"))
        has_po = bool(case.get("po_number"))
        inv_amount = self._safe_number(case.get("invoice_amount"))
        po_amount = self._safe_number(case.get("po_net_value_converted")) or self._safe_number(case.get("po_net_value"))
        inv_qty = self._safe_number(case.get("invoice_quantity"))
        po_qty = self._safe_number(case.get("po_quantity"))

        if has_open_ap and has_invoice:
            if inv_qty > 0 and po_qty > 0 and abs(inv_qty - po_qty) > 0.01:
                return "quantity_mismatch"
            if inv_amount > 0 and po_amount > 0 and abs(inv_amount - po_amount) > 0.01:
                return "payment_mismatch"
            return "invoice_mismatch"
        if has_invoice and not has_po:
            return "invoice_mismatch"
        if has_po and not has_invoice:
            return "goods_receipt_mismatch"
        return "novel_exception"

    # ─────────────────────────────────────────────
    # MAIN: PIPELINE-READY EXCEPTIONS
    # ─────────────────────────────────────────────
    def get_open_exceptions(self):
        """Build pipeline-ready cases from live Celonis data."""
        enriched = self._build_enriched_cases()
        if not enriched:
            return []

        variants = self.get_process_variants()
        cases = []
        seen = set()

        for case in enriched:
            if not case.get("has_open_ap"):
                continue

            case_id = (
                str(case.get("invoice_number") or "")
                or str(case.get("po_number") or "")
                or str(case.get("invoice_id") or "")
            ).strip()

            if not case_id or case_id in seen:
                continue
            seen.add(case_id)

            event_log = self._build_event_log(case)
            exception_type = self._map_exception_type(case)

            invoice_amount = self._safe_number(case.get("invoice_amount"))
            po_value = self._safe_number(case.get("po_net_value_converted")) or self._safe_number(case.get("po_net_value"))
            financial_value = invoice_amount if invoice_amount > 0 else po_value

            raw_case = {
                "case_id": case_id,
                "event_log": event_log,
                "exception_alert": {
                    "type": exception_type,
                    "triggered_at": event_log[-1]["timestamp"],
                    "financial_value": financial_value,
                },
                "process_variants": variants,
                "metadata": {
                    "vendor": case.get("vendor_name") or case.get("vendor_number") or "Unknown Vendor",
                    "po_value": po_value or financial_value,
                    "sla_hours": 48,
                    "assigned_team": self._map_team(case.get("company_code") or case.get("open_company_code")),
                    "compliance_flag": False,
                    "company_code": case.get("company_code") or case.get("open_company_code"),
                    "po_number": case.get("po_number", ""),
                    "invoice_number": case.get("invoice_number", ""),
                    "invoice_amount": invoice_amount,
                    "po_net_value": po_value,
                    "po_quantity": self._safe_number(case.get("po_quantity")),
                    "invoice_quantity": self._safe_number(case.get("invoice_quantity")),
                    "vendor_number": case.get("vendor_number", ""),
                    "vendor_country": case.get("vendor_country", ""),
                    "fiscal_year": case.get("fiscal_year", ""),
                    "case_key": case.get("case_key", ""),
                    "source": "celonis_live",
                },
                "description": (
                    f"Live Celonis | Invoice {case.get('invoice_number', '?')} | "
                    f"Vendor {case.get('vendor_name', '?')} | ${financial_value:,.0f}"
                ),
            }
            cases.append(raw_case)

        logger.info("Built %d pipeline-ready live cases", len(cases))
        return cases

    def get_case_data(self, case_id):
        """Get data for a specific case (for compatibility)."""
        for case in self.get_open_exceptions():
            if case.get("case_id") == case_id:
                return case
        return {}

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────
    def _map_team(self, company_code):
        code = str(company_code or "").strip()
        return {
            "AC33": "AP_Team_AC33", "1000": "AP_Team_1",
            "2000": "AP_Team_2", "3000": "AP_Team_3",
        }.get(code, f"AP_Team_{code}" if code else "AP_Team_Default")

    def _safe_number(self, value):
        try:
            if value is None: return 0.0
            if isinstance(value, float) and math.isnan(value): return 0.0
            text = str(value).strip().lower()
            if text in ("", "nan", "none", "null"): return 0.0
            return float(value)
        except Exception:
            return 0.0
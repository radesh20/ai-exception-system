# main.py
"""
Main Entry Point — Processes exceptions from Celonis (or mock).

Data flow:
  CELONIS_MODE=mock → MockCelonisClient → reads data/sample_input.json
  CELONIS_MODE=live → CelonisClient → calls real Celonis APIs via PyCelonis
"""

import os
import sys
import json
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.logging_config import setup_logging
setup_logging()

import config.settings as settings
from store import get_store
from celonis import get_celonis_client
from agents.orchestrator import ExceptionOrchestrator
from notifications.manager import NotificationManager

logger = logging.getLogger(__name__)


def run(force=False):
    print(f"\n{'='*60}")
    print(f"  P2P Exception Management System v2.0")
    print(f"  AI Mode: {'Deep Agent' if settings.AZURE_OPENAI_ENABLED else 'Rule-Based'}")
    print(f"  Storage: {settings.STORAGE_BACKEND.upper()}")
    print(f"  Celonis: {settings.CELONIS_MODE.upper()}")
    print(f"{'='*60}\n")

    # ─── Initialize Storage ───
    store = get_store()
    if not store.get_policies():
        logger.info("No policies found. Seeding...")
        from scripts.seed import seed
        seed()

    # ─── Initialize Agents ───
    orchestrator = ExceptionOrchestrator(store)
    notifier = NotificationManager(store=store)

    # ─── Initialize Celonis Client ───
    # This automatically picks Live or Mock based on .env
    celonis = get_celonis_client()
    
    print(f"📡 Connecting to Celonis ({settings.CELONIS_MODE} mode)...")
    
    # 1. Fetch Exceptions
    try:
        cases = celonis.get_open_exceptions()
    except Exception as e:
        print(f"❌ Failed to fetch exceptions from Celonis: {e}")
        return

    if not cases:
        print("ℹ️  No open exceptions found to process.")
        return

    print(f"📥 Received {len(cases)} exception(s) from Celonis")

    # 2. Fetch Process Variants (Happy Paths)
    try:
        variants = celonis.get_process_variants()
        print(f"📊 Loaded {len(variants)} process variants.")
    except Exception as e:
        variants = []
        logger.warning(f"Could not load process variants: {e}")

    # 3. Deduplication Check — use both exception store and persistent processing state
    existing = {e.context.case_id for e in store.list_exceptions(limit=10000) if e.context}
    
    results, skipped = [], 0
    print(f"🔄 Starting Pipeline Execution...\n")

    for i, raw_case in enumerate(cases, 1):
        # Clean up data
        case = {k: v for k, v in raw_case.items()}
        desc = case.pop("description", f"Case {i}")
        cid = case.get("case_id", f"CASE-{i}")

        # Skip if already processed (check both persistent state and exception store)
        if not force and (store.is_case_processed(cid) or cid in existing):
            print(f"  [{i}] ⏭️  SKIP: {cid} (Already Processed)")
            skipped += 1
            continue

        # Inject variants into case for Agent Analysis
        if "process_variants" not in case or not case["process_variants"]:
            case["process_variants"] = variants

        print(f"  [{i}] Processing: {cid} — {desc}")
        
        try:
            # ─── EXECUTE AI PIPELINE ───
            exc = orchestrator.process(case)
            
            ctx, cls = exc.context, exc.classification
            print(f"      Type: {ctx.exception_type} | P{cls.priority} | {cls.routing.upper()} | Action: {exc.recommended_action}")
            
            # ─── NOTIFICATIONS ───
            if exc.status.value in ("pending_decision", "escalated"):
                notifier.notify(
                    exc.id, 
                    f"Exception: {ctx.exception_type}\nExposure: ${ctx.financial_exposure:,.2f}\nRecommended: {exc.recommended_action}",
                    cls.priority, 
                    cls.category, 
                    f"http://localhost:3000/exception/{exc.id}"
                )
            
            results.append(exc)
            store.mark_case_processed(cid, exc.id)
            
        except Exception as e:
            print(f"      ❌ Error processing case {cid}: {e}")
            logger.error(f"Pipeline error for case {cid}: {e}")

    # ─── Summary ───
    print(f"\n{'='*60}")
    print(f"  PIPELINE SUMMARY")
    print(f"  ─────────────────────────────")
    print(f"  Processed: {len(results)}")
    print(f"  Skipped:   {skipped}")
    print(f"  Pending:   {sum(1 for r in results if r.status.value == 'pending_decision')}")
    print(f"")
    print(f"  Frontend: http://localhost:3000")
    print(f"  API Docs: http://localhost:8000/docs")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="Process even if case already exists")
    p.add_argument("--clear", action="store_true", help="Clear local database before running")
    args = p.parse_args()
    
    if args.clear:
        import glob
        for f in glob.glob("data/db/*.json"):
            try: os.remove(f)
            except: pass
        print("🗑️ Database Cleared.")
        
    run(force=args.force)
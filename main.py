import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config.settings as settings
from store import get_store
from agents.orchestrator import ExceptionOrchestrator
from notifications.manager import NotificationManager

def run(force=False):
    print(f"\n{'='*60}")
    print(f"  P2P Exception Management System")
    print(f"  Mode:    {'Deep Agent' if settings.AZURE_OPENAI_ENABLED else 'Rule-Based'}")
    print(f"  Storage: {settings.STORAGE_BACKEND.upper()}")
    print(f"  Celonis: {settings.CELONIS_MODE.upper()}")
    print(f"{'='*60}\n")

    store = get_store()
    if not store.get_policies():
        print("📦 Seeding...")
        from scripts.seed import seed
        seed()

    orchestrator = ExceptionOrchestrator(store)
    notifier = NotificationManager()

    sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_input.json")
    if not os.path.exists(sample_path):
        print(f"❌ Not found: {sample_path}")
        return
    with open(sample_path) as f:
        content = f.read().strip()
        if not content:
            print("❌ sample_input.json is empty")
            return
        data = json.loads(content)

    cases = data.get("cases", [])
    existing = {e.context.case_id for e in store.list_exceptions(limit=10000) if e.context}
    print(f"🔄 Processing {len(cases)} cases...\n")

    results, skipped = [], 0
    for i, raw in enumerate(cases, 1):
        case = {k: v for k, v in raw.items()}
        desc = case.pop("description", f"Case {i}")
        cid = case.get("case_id", f"CASE-{i}")

        if cid in existing and not force:
            print(f"  [{i}] ⏭️  SKIP: {cid}")
            skipped += 1
            continue

        print(f"  [{i}] {desc}")
        try:
            exc = orchestrator.process(case)
            ctx, cls = exc.context, exc.classification
            print(f"      Type: {ctx.exception_type} | Priority: {cls.priority}/5 | Route: {cls.routing.upper()} | Action: {exc.recommended_action}")
            if exc.status.value == "pending_decision":
                rc = exc.root_cause
                notifier.notify(exc.id, f"Exception: {ctx.exception_type}\nExposure: ${ctx.financial_exposure:,.2f}\nRecommended: {exc.recommended_action}",
                    cls.priority, cls.category, f"http://localhost:3000/exception/{exc.id}")
            results.append(exc)
        except Exception as e:
            print(f"      ❌ {e}")

    print(f"\n{'='*60}\n  Processed: {len(results)} | Skipped: {skipped} | Pending: {sum(1 for r in results if r.status.value == 'pending_decision')}")
    print(f"  Frontend: http://localhost:3000\n  API:      http://localhost:8000/docs\n{'='*60}\n")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    p.add_argument("--clear", action="store_true")
    args = p.parse_args()
    if args.clear:
        import glob
        for f in glob.glob("data/db/*.json"): os.remove(f)
        print("🗑️ Cleared")
    run(force=args.force)
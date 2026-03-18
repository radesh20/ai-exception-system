from models import ExceptionModel, ExceptionStatus, ExceptionContext, Decision, DecisionType

def _exc():
    ctx = ExceptionContext("T1","payment_mismatch",50000,0.7,"X",["A"],["A"],"T","V",48,False,"2024-01-01T00:00:00")
    return ExceptionModel(id="", status=ExceptionStatus.PENDING_DECISION, context=ctx, recommended_action="test")

def test_save_get(temp_store):
    exc = _exc()
    temp_store.save_exception(exc)
    r = temp_store.get_exception(exc.id)
    assert r.context.exception_type == "payment_mismatch"

def test_no_dup(temp_store):
    exc = _exc()
    temp_store.save_exception(exc)
    temp_store.save_exception(exc)
    assert len(temp_store.list_exceptions()) == 1

def test_policy_upsert(temp_store):
    temp_store.save_policy({"category":"pm","action_type":"fix","success_rate":0.8,"sample_size":10})
    temp_store.save_policy({"category":"pm","action_type":"fix","success_rate":0.9,"sample_size":20})
    assert len(temp_store.get_policies("pm")) == 1
    assert temp_store.get_policies("pm")[0]["success_rate"] == 0.9

def test_stats(temp_store):
    temp_store.save_exception(_exc())
    s = temp_store.get_stats()
    assert s["total_exceptions"] == 1
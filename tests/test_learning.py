"""Tests for learning engine."""

import pytest
from agents.learning_engine import LearningEngine
from models import Decision, DecisionType, ExceptionModel, ExceptionStatus, ExceptionContext


def test_learning_from_approval(temp_store):
    """Test that approving a decision updates policy stats."""
    # Add a policy
    temp_store.save_policy({
        "category": "payment_mismatch",
        "action_type": "three_way_match_recheck",
        "success_rate": 0.8,
        "sample_size": 10,
    })

    # Create and save an exception
    ctx = ExceptionContext(
        case_id="L-001", exception_type="payment_mismatch",
        financial_exposure=50000, severity_score=0.7,
        deviation_point="X", actual_path=["A"], happy_path=["A"],
        assigned_team="T", vendor="V", sla_hours=48,
        compliance_flag=False, timestamp="2024-01-01T00:00:00", raw_data={}
    )
    from models import Classification
    exc = ExceptionModel(
        id="L-001", status=ExceptionStatus.APPROVED, context=ctx,
        classification=Classification(
            category="payment_mismatch", priority=3,
            is_novel=False, routing="auto", confidence=0.85
        ),
        recommended_action="three_way_match_recheck"
    )
    temp_store.save_exception(exc)

    decision = Decision(
        id="", exception_id="L-001",
        decision_type=DecisionType.APPROVED,
        analyst_name="analyst", notes="",
        original_recommendation="three_way_match_recheck",
        final_action="three_way_match_recheck", created_at=""
    )
    temp_store.save_decision(decision)

    engine = LearningEngine(temp_store)
    result = engine.record_feedback(decision)

    assert result["was_approved"] is True

    # Check policy was updated
    policies = temp_store.get_policies("payment_mismatch")
    assert policies[0]["sample_size"] == 11


def test_insights_empty_store(temp_store):
    """Insights should work on empty store."""
    engine = LearningEngine(temp_store)
    insights = engine.get_insights()
    assert insights["total_decisions"] == 0
    assert insights["overall_approval_rate"] == 0
from agents.context_builder import ContextBuilderAgent
from agents.root_cause import RootCauseAgent
from agents.classifier import ClassifierAgent
from agents.action_recommender import ActionRecommenderAgent
import pytest

class TestContextBuilder:
    def test_ok(self, sample_raw):
        ctx = ContextBuilderAgent().build(sample_raw)
        assert ctx.exception_type == "payment_mismatch"
        assert ctx.financial_exposure == 50000

    def test_missing(self, sample_raw):
        del sample_raw["case_id"]
        with pytest.raises(ValueError): ContextBuilderAgent().build(sample_raw)

    def test_empty_log(self, sample_raw):
        sample_raw["event_log"] = []
        with pytest.raises(ValueError): ContextBuilderAgent().build(sample_raw)

class TestRootCause:
    def test_empty(self, sample_raw):
        ctx = ContextBuilderAgent().build(sample_raw)
        rc = RootCauseAgent().analyze(ctx, [])
        assert rc.confidence < 0.5

class TestClassifier:
    def test_auto(self, sample_raw):
        ctx = ContextBuilderAgent().build(sample_raw)
        ctx.financial_exposure = 20000
        from models import RootCauseAnalysis
        rc = RootCauseAnalysis("h", 0.85, [], "", [])
        cls = ClassifierAgent().classify(ctx, rc)
        assert cls.routing == "auto"

    def test_human_novel(self, sample_raw):
        ctx = ContextBuilderAgent().build(sample_raw)
        from models import RootCauseAnalysis
        rc = RootCauseAnalysis("h", 0.3, [], "", [])
        cls = ClassifierAgent().classify(ctx, rc)
        assert cls.routing == "human"

class TestRecommender:
    def test_no_policy(self, sample_raw):
        ctx = ContextBuilderAgent().build(sample_raw)
        from models import Classification
        cls = Classification("novel", 3, True, "human", 0.3)
        a, _, _, erp = ActionRecommenderAgent().recommend(ctx, cls, [])
        assert a == "escalate_to_human"
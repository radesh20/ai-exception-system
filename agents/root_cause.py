import difflib
import logging
from models import ExceptionContext, RootCauseAnalysis

logger = logging.getLogger(__name__)

class RootCauseAgent:
    def analyze(self, context, historical_cases, prompt_package=None):
        matching = [c for c in historical_cases if c.get("exception_type") == context.exception_type]
        scored = [(c, difflib.SequenceMatcher(None, context.actual_path, c.get("actual_path", [])).ratio()) for c in matching]
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:5]
        supporting = [c.get("case_id", "") for c, _ in top if c.get("case_id")]
        deviations = [c.get("deviation_point", "") for c, _ in top]
        common_dev = max(set(deviations), key=deviations.count) if deviations else context.deviation_point
        confidence = self._calc_conf(len(matching), top[0][1] if top else 0)
        hypothesis = self._hypothesis(context, common_dev, len(matching), confidence)
        pattern = f"Found {len(matching)} similar cases. Top similarity: {top[0][1]:.1%}. Common deviation: {common_dev}." if top else "No similar cases."
        causal = [f"Deviation at: {context.deviation_point}"]
        if context.compliance_flag: causal.append("Compliance flag raised")
        if context.financial_exposure > 100000: causal.append("High financial exposure")

        # Append AI guidance when a prompt_package is provided
        if prompt_package and prompt_package.root_cause_prompt:
            hypothesis = f"{hypothesis} [AI guidance: {prompt_package.root_cause_prompt}]"
            logger.info("[INFO] RootCauseAgent: applied prompt_package guidance.")

        return RootCauseAnalysis(hypothesis=hypothesis, confidence=confidence, supporting_cases=supporting[:5], pattern_description=pattern, causal_factors=causal[:5])

    def _calc_conf(self, n, top_sim):
        conf = min(n / 20, 1.0) * 0.4 + top_sim * 0.4 + (0.2 if n >= 5 else 0.1)
        if n < 5: conf = min(conf, 0.49)
        return round(max(0.0, min(1.0, conf)), 3)

    def _hypothesis(self, ctx, dev, n, conf):
        if conf < 0.3:
            return f"Novel {ctx.exception_type} exception. Only {n} similar cases. Deviation at '{ctx.deviation_point}'. Manual investigation recommended."
        return f"Analysis indicates {ctx.exception_type} was likely caused by deviation at '{dev}'. Matches {n} historical cases with {conf:.0%} confidence. Exposure: ${ctx.financial_exposure:,.2f}."
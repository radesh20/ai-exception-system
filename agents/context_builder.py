from celonis.transformer import CelonisTransformer

class ContextBuilderAgent:
    def build(self, raw_input):
        for field in ["case_id", "event_log", "exception_alert"]:
            if field not in raw_input:
                raise ValueError(f"Missing required field: {field}")
        if not raw_input.get("event_log"):
            raise ValueError("event_log cannot be empty")
        return CelonisTransformer.transform(raw_input)
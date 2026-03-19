import uuid
from datetime import datetime
import config.settings as settings
from models import ExceptionModel, ExceptionStatus
from agents.context_builder import ContextBuilderAgent
from agents.root_cause import RootCauseAgent
from agents.classifier import ClassifierAgent
from agents.action_recommender import ActionRecommenderAgent
from mcp_client import MCPClient
import logging

logger = logging.getLogger(__name__)

class ExceptionOrchestrator:
    def __init__(self, store):
        self.store = store
        self.context_builder = ContextBuilderAgent()
        self.root_cause_agent = RootCauseAgent()
        self.classifier = ClassifierAgent()
        self.recommender = ActionRecommenderAgent()
        self.deep_agent = None
        self.mcp_client = MCPClient()
        if settings.AZURE_OPENAI_ENABLED:
            self._init_deep_agent()

    def _init_deep_agent(self):
        try:
            from deepagents import create_deep_agent
            from langchain_openai import AzureChatOpenAI
            model = AzureChatOpenAI(azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                api_key=settings.AZURE_OPENAI_API_KEY, api_version=settings.AZURE_OPENAI_API_VERSION, temperature=0)
            self.deep_agent = create_deep_agent(model=model, tools=[], system_prompt="P2P Exception AI")
            print("✅ Deep Agent initialized")
        except Exception as e:
            print(f"⚠️  Deep Agent failed: {e}. Using rule-based mode.")

    def process(self, raw_input):
        context = self.context_builder.build(raw_input)
        historical = self.store.get_historical_cases(context.exception_type)
        root_cause = self.root_cause_agent.analyze(context, historical)
        classification = self.classifier.classify(context, root_cause)
        policies = self.store.get_policies(classification.category)
        action_type, action_params, reasoning = self.recommender.recommend(context, classification, policies)
        status = ExceptionStatus.PENDING_DECISION if classification.routing == "human" else ExceptionStatus.APPROVED
        exc = ExceptionModel(id=str(uuid.uuid4()), status=status, context=context, root_cause=root_cause,
            classification=classification, recommended_action=action_type,
            recommended_action_params=action_params, ai_reasoning=reasoning)
        self.store.save_exception(exc)

        if classification.routing == "human":
            logger.info(f"📢 Sending Teams notification for {exc.id}")
            try:
                self.mcp_client.notify_teams(
                    case_id=exc.context.case_id,
                    issue=exc.context.exception_type,
                    priority=exc.classification.priority,
                    recommendation=exc.recommended_action,
                    financial_exposure=exc.context.financial_exposure,
                    exception_uuid=exc.id,
                )
            except Exception as e:
                logger.error(f"❌ Failed to send Teams notification: {e}")

        return exc
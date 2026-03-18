import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config.settings as settings

def get_celonis_client():
    if settings.CELONIS_MODE == "live" and settings.CELONIS_ENABLED:
        from celonis.client import CelonisClient
        return CelonisClient(settings.CELONIS_BASE_URL, settings.CELONIS_API_TOKEN,
                              settings.CELONIS_DATA_POOL_ID, settings.CELONIS_DATA_MODEL_ID)
    from celonis.mock_client import MockCelonisClient
    return MockCelonisClient()
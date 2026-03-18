import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config.settings as settings
from store.base import BaseStore

_store_instance = None

def get_store():
    global _store_instance
    if _store_instance is not None:
        return _store_instance
    from store.json_store import JsonStore
    _store_instance = JsonStore(settings.STORAGE_PATH)
    _store_instance.initialize()
    return _store_instance

def reset_store():
    global _store_instance
    _store_instance = None
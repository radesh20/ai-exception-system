from abc import ABC, abstractmethod


class BaseStore(ABC):
    @abstractmethod
    def save_exception(self, exc): pass
    @abstractmethod
    def get_exception(self, exc_id): pass
    @abstractmethod
    def list_exceptions(self, status=None, limit=100): pass
    @abstractmethod
    def update_exception(self, exc): pass
    @abstractmethod
    def save_decision(self, dec): pass
    @abstractmethod
    def get_decisions(self, exception_id): pass
    @abstractmethod
    def list_decisions(self, limit=100): pass
    @abstractmethod
    def save_action(self, action): pass
    @abstractmethod
    def get_actions(self, exception_id): pass
    @abstractmethod
    def list_actions(self, limit=100): pass
    @abstractmethod
    def get_historical_cases(self, exception_type=None): pass
    @abstractmethod
    def save_historical_case(self, case): pass
    @abstractmethod
    def get_policies(self, category=None): pass
    @abstractmethod
    def save_policy(self, policy): pass
    @abstractmethod
    def update_policy_stats(self, category, action, success): pass
    @abstractmethod
    def get_stats(self): pass
    @abstractmethod
    def initialize(self): pass
    def close(self): pass
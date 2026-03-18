from abc import ABC, abstractmethod

class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, action): pass
    @abstractmethod
    def rollback(self, action): pass
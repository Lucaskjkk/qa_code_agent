from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Classe base para agentes."""

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

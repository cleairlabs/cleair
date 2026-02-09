from abc import ABC, abstractmethod
from typing import Any


class Provider(ABC):
    @abstractmethod
    def run_inference(self, model_name: str, prompt: str) -> dict[str, Any]:
        """Run inference via an upstream provider and return a common shape, regardless of vendor."""

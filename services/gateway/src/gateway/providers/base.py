from abc import ABC, abstractmethod
from typing import Any


class Provider(ABC):
    provider_name = "unknown"

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def generate(
        self,
        prompt_messages: list[dict[str, str]],
        tools: list[Any] | None = None,
        images: list[Any] | None = None,
    ) -> str:
        """llmSHAP-compatible generation interface."""

    def run_inference(self, prompt: str) -> dict[str, Any]:
        """Run inference via an upstream provider and return a common shape."""
        response_text = self.generate(prompt_messages=[{"role": "user", "content": prompt}])
        return {
            "provider": self.provider_name,
            "model_name": self.model_name,
            "output_text": response_text,
        }

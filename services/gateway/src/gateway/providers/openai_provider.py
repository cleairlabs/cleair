from typing import Any

from .base import Provider


class OpenAIProvider(Provider):
    """
    TODO

    The first gateway version uses a mock task result so the queueing API can ship
    before external provider wiring and key management are introduced.
    """

    provider_name = "openai"

    def generate(
        self,
        prompt_messages: list[dict[str, str]],
        tools: list[Any] | None = None,
        images: list[Any] | None = None,
    ) -> str:
        del tools, images
        for message in reversed(prompt_messages):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""

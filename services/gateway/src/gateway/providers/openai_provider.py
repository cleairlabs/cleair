from .base import Provider


class OpenAIProvider(Provider):
    """
    TODO

    The first gateway version uses a mock task result so the queueing API can ship
    before external provider wiring and key management are introduced.
    """

    def run_inference(self, model_name: str, prompt: str) -> dict:
        return {
            "provider": "openai",
            "model_name": model_name,
            "echo": prompt,
        }

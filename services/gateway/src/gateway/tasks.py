import time
from typing import Any

from llmSHAP import BasicPromptCodec, DataHandler, ShapleyAttribution
from llmSHAP.llm.openai import OpenAIInterface

from .queue import celery_app


def _build_prompt(prompt: str) -> list[dict[str, str]]:
    return [{"role": "user", "content": prompt}]


def _build_inference_interface(provider_name: str, model_name: str) -> OpenAIInterface:
    if provider_name != "openai":
        raise ValueError(f"Unsupported provider for inference: {provider_name}")
    return OpenAIInterface(model_name=model_name, temperature=0.0, max_tokens=512)


def run_provider_inference(model_name: str, prompt: str, provider: str) -> dict[str, Any]:
    inference_interface = _build_inference_interface(provider_name=provider, model_name=model_name)
    response_text = inference_interface.generate(prompt=_build_prompt(prompt))
    return {
        "provider": provider,
        "model_name": model_name,
        "output_text": response_text,
    }


def run_llmshap_attribution(
    prompt: str,
    provider: str,
    model_name: str,
) -> dict[str, Any]:
    start_time = time.perf_counter()
    try:
        if provider != "openai":
            raise ValueError(f"Unsupported provider for attribution: {provider}")
        attribution_result = ShapleyAttribution(
            model=OpenAIInterface(model_name=model_name, temperature=0.0, max_tokens=512),
            data_handler=DataHandler(prompt),
            prompt_codec=BasicPromptCodec(system=""),
            use_cache=True,
            verbose=True,
            num_threads=50,
        ).attribution()
        return {
            "result": {
                "attribution": attribution_result.attribution,
                "output": attribution_result.output,
            },
            "attribution_meta": {
                "status": "complete",
                "method": "llmshap",
                "latency_ms": int((time.perf_counter() - start_time) * 1000),
            },
        }
    except Exception as exc:
        return {
            "result": None,
            "attribution_meta": {
                "status": "failed",
                "method": "llmshap",
                "num_samples": None,
                "latency_ms": int((time.perf_counter() - start_time) * 1000),
                "error": str(exc),
            },
        }


@celery_app.task(name="gateway.run_llmshap")
def run_llmshap_task(
    request_id: str,
    prompt: str,
    provider: str,
    model_name: str,
) -> dict[str, Any]:
    llmshap_result = run_llmshap_attribution(
        prompt=prompt,
        provider=provider,
        model_name=model_name,
    )
    if llmshap_result["attribution_meta"]["status"] == "failed":
        error_message = llmshap_result["attribution_meta"].get("error", "llmSHAP attribution failed")
        raise RuntimeError(error_message)

    return {
        "request_id": request_id,
        "attribution": llmshap_result["result"],
        "attribution_meta": llmshap_result["attribution_meta"],
    }

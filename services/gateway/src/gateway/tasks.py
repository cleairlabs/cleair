from .queue import celery_app


@celery_app.task(name="gateway.run_inference")
def run_inference_task(model_name: str, prompt: str, provider: str) -> dict:
    return {
        "provider": provider,
        "model_name": model_name,
        "llmshap": {
            "status": "not_implemented",
            "message": "llmSHAP execution pipeline not wired yet",
        },
        "prompt_preview": prompt[:120],
    }

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException

from .config import get_settings
from .queue import celery_app
from .schemas import InferenceAcceptedResponse, InferenceRequest, InferenceStatusResponse
from .tasks import run_inference_task

settings = get_settings()
app = FastAPI(title=settings.gateway_name)


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok", "service": settings.gateway_name}


@app.post("/inferences", response_model=InferenceAcceptedResponse, status_code=202)
def submit_inference(request: InferenceRequest) -> InferenceAcceptedResponse:
    task = run_inference_task.delay(
        model_name=request.model_name,
        prompt=request.prompt,
        provider=request.provider,
    )
    return InferenceAcceptedResponse(job_id=task.id, status="queued")


@app.get("/inferences/{job_id}", response_model=InferenceStatusResponse)
def get_inference(job_id: str) -> InferenceStatusResponse:
    task_result = AsyncResult(job_id, app=celery_app)

    if task_result.state == "PENDING":
        return InferenceStatusResponse(job_id=job_id, status="queued")

    if task_result.state in {"RECEIVED", "STARTED", "RETRY"}:
        return InferenceStatusResponse(job_id=job_id, status="running")

    if task_result.state == "SUCCESS":
        return InferenceStatusResponse(job_id=job_id, status="succeeded", result=task_result.result)

    if task_result.state == "FAILURE":
        return InferenceStatusResponse(job_id=job_id, status="failed", error=str(task_result.result))

    raise HTTPException(status_code=500, detail=f"Unknown task state: {task_result.state}")

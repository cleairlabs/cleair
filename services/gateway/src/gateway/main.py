import uuid
from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException

from .config import get_settings
from .queue import celery_app
from .schemas import (
    AttributionStatusResponse,
    AttributionMeta,
    InferenceRequest,
    SyncInferenceResponse,
)
from .tasks import run_llmshap_attribution, run_llmshap_task, run_provider_inference

settings = get_settings()
app = FastAPI(title=settings.gateway_name)


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok", "service": settings.gateway_name}


@app.post("/v1/inference", response_model=SyncInferenceResponse)
def run_sync_inference(request: InferenceRequest) -> SyncInferenceResponse:
    request_id = str(uuid.uuid4())
    inference_response = run_provider_inference(
        model_name=request.model_name,
        prompt=request.prompt,
        provider=request.provider,
    )

    if request.attribution.delivery_mode == "deferred":
        attribution_task = run_llmshap_task.delay(
            request_id=request_id,
            prompt=request.prompt,
            provider=request.provider,
            model_name=request.model_name,
        )
        attribution_meta = AttributionMeta(
            status="queued",
            method="llmshap",
            latency_ms=0,
            quality="deferred",
            job_id=attribution_task.id,
        )
        return SyncInferenceResponse(
            request_id=request_id,
            response=inference_response,
            attribution=None,
            attribution_meta=attribution_meta,
        )

    llmshap_result = run_llmshap_attribution(
        prompt=request.prompt,
        provider=request.provider,
        model_name=request.model_name,
    )
    return SyncInferenceResponse(
        request_id=request_id,
        response=inference_response,
        attribution=llmshap_result["result"],
        attribution_meta=AttributionMeta(**llmshap_result["attribution_meta"]),
    )


@app.get("/attributions/{job_id}", response_model=AttributionStatusResponse)
def get_attribution(job_id: str) -> AttributionStatusResponse:
    task_result = AsyncResult(job_id, app=celery_app)

    if task_result.state == "PENDING":
        return AttributionStatusResponse(job_id=job_id, status="queued")

    if task_result.state in {"RECEIVED", "STARTED", "RETRY"}:
        return AttributionStatusResponse(job_id=job_id, status="running")

    if task_result.state == "SUCCESS":
        return AttributionStatusResponse(job_id=job_id, status="succeeded", result=task_result.result)

    if task_result.state == "FAILURE":
        return AttributionStatusResponse(job_id=job_id, status="failed", error=str(task_result.result))

    raise HTTPException(status_code=500, detail=f"Unknown task state: {task_result.state}")

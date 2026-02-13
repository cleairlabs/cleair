from typing import Any
from typing import Literal

from pydantic import BaseModel, Field

AttributionDeliveryMode = Literal["full", "fast", "deferred"]


class AttributionOptions(BaseModel):
    delivery_mode: AttributionDeliveryMode = Field(
        default="fast",
        description="Attribution delivery mode",
    )


class InferenceRequest(BaseModel):
    model_name: str = Field(..., description="Model identifier used by the provider")
    prompt: str = Field(..., description="Prompt input for the target model")
    provider: Literal["openai"] = Field(default="openai", description="Inference provider")
    attribution: AttributionOptions = Field(
        default_factory=AttributionOptions,
        description="llmSHAP attribution execution settings",
    )


class AttributionStatusResponse(BaseModel):
    job_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


class AttributionMeta(BaseModel):
    status: Literal["complete", "queued", "failed"]
    method: str = "llmshap"
    num_samples: int | None = None
    latency_ms: int | None = None
    quality: Literal["high", "approximate", "deferred"] | None = None
    job_id: str | None = None
    error: str | None = None


class SyncInferenceResponse(BaseModel):
    request_id: str
    response: dict[str, Any]
    attribution: dict[str, Any] | None = None
    attribution_meta: AttributionMeta

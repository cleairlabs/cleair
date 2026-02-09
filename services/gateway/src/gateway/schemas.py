from typing import Any

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    model_name: str = Field(..., description="Model identifier used by the provider")
    prompt: str = Field(..., description="Prompt input for the target model")
    provider: str = Field(default="mock", description="Inference provider")


class InferenceAcceptedResponse(BaseModel):
    job_id: str
    status: str


class InferenceStatusResponse(BaseModel):
    job_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None

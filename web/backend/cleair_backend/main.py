from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from collections.abc import Mapping

from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.responses import StreamingResponse

from cleair_backend.auth import (
    AUTH_DETAIL,
    clear_authenticated_session,
    is_authenticated,
    load_auth_config,
    require_authenticated_request,
    set_authenticated_session,
    verify_access_code,
)
from cleair_backend.live import live_payload_to_events
from cleair_backend.otlp import otlp_payload_to_run_events
from cleair_backend.store import TraceStore


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="cleAIr backend")
trace_store = TraceStore()
auth_config = load_auth_config()
allowed_origins = [
    origin for origin in os.environ.get("CLEAIR_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)



########################
# HELPERS
########################
def _authenticate_ingestion(request: Request) -> None:
    authorization_parts = request.headers.get("Authorization", "").split()
    if len(authorization_parts) != 2 or authorization_parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid bearer token", headers={"WWW-Authenticate": "Bearer"})
    api_key = authorization_parts[1]
    if not trace_store.has_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid bearer token", headers={"WWW-Authenticate": "Bearer"})


def _otlp_payload(body: bytes, content_type: str) -> dict:
    if "application/json" in content_type:
        return json.loads(body.decode() or "{}")

    request_message = ExportTraceServiceRequest()
    request_message.ParseFromString(body)
    payload = MessageToDict(request_message, preserving_proto_field_name=False)
    return payload if isinstance(payload, Mapping) else {}


async def _generate_sse():
    queue, replay_events = trace_store.subscribe()
    try:
        for event in replay_events:
            yield f"data: {json.dumps(event)}\n\n"
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                yield ":\n\n"
    finally:
        trace_store.unsubscribe(queue)
########################




@app.get("/auth/session")
async def auth_session(request: Request) -> dict:
    return {"authenticated": is_authenticated(request, auth_config)}


@app.post("/auth/verify")
async def auth_verify(request: Request, response: Response) -> dict:
    body = await request.json()
    access_code = str(body.get("code", ""))
    if not verify_access_code(access_code, auth_config):
        raise HTTPException(status_code=401, detail=AUTH_DETAIL)
    set_authenticated_session(response, auth_config)
    return {"authenticated": True}


@app.post("/auth/logout", status_code=204)
async def auth_logout(response: Response) -> Response:
    clear_authenticated_session(response, auth_config)
    return response


@app.post("/api-key", status_code=201)
async def create_api_key(request: Request) -> dict:
    require_authenticated_request(request, auth_config)
    return {"apiKey": trace_store.ensure_api_key()}


@app.get("/agents")
async def list_agents(request: Request) -> list[dict]:
    require_authenticated_request(request, auth_config)
    return trace_store.list_agents()


@app.delete("/agents/{run_id}", status_code=204)
async def delete_agent(request: Request, run_id: str) -> None:
    require_authenticated_request(request, auth_config)
    if not trace_store.delete_run(run_id):
        raise HTTPException(status_code=404, detail="Unknown runId")


@app.post("/v1/traces", status_code=204)
async def ingest_otlp_traces(request: Request) -> None:
    _authenticate_ingestion(request)
    payload = _otlp_payload(await request.body(), request.headers.get("content-type", "application/json"))
    for trace_run in otlp_payload_to_run_events(payload):
        is_new_run = trace_store.start_run(trace_run.service_name, trace_run.trace_id, metadata=trace_run.metadata)
        events_to_emit = [{"type": "run_started", "runId": trace_run.trace_id, "runLabel": trace_run.service_name, "metadata": trace_run.metadata}] if is_new_run else []
        events_to_emit.extend(trace_run.events)
        trace_store.append_events(trace_run.trace_id, events_to_emit)
        if trace_run.is_completed:
            trace_store.mark_completed(trace_run.trace_id)
        logger.info("Ingested %d events for trace %s (%s)", len(events_to_emit), trace_run.trace_id, trace_run.service_name)


@app.post("/v1/live", status_code=204)
async def ingest_live_span_start(request: Request) -> None:
    _authenticate_ingestion(request)
    run_id, service_name, metadata, events = live_payload_to_events(await request.json())
    is_new_run = trace_store.start_run(service_name, run_id, metadata=metadata)
    events_to_emit = [{"type": "run_started", "runId": run_id, "runLabel": service_name, "metadata": metadata}] if is_new_run else []
    events_to_emit.extend(events)
    trace_store.append_events(run_id, events_to_emit)


@app.get("/events")
async def stream_events(request: Request) -> StreamingResponse:
    require_authenticated_request(request, auth_config)
    return StreamingResponse(
        _generate_sse(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def run() -> None:
    parser = argparse.ArgumentParser(description="Run the cleAIr backend.")
    parser.add_argument("--host", default=os.environ.get("CLEAIR_BACKEND_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("CLEAIR_BACKEND_PORT", "8000")))
    parser.add_argument("--reload", action="store_true",
                        default=os.environ.get("CLEAIR_BACKEND_RELOAD", "").lower() in {"1", "true", "yes", "on"},
                        help="Enable autoreload for local development.")
    args = parser.parse_args()
    uvicorn.run("cleair_backend.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    run()

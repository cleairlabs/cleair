from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os

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
from cleair_backend.otlp import otlp_payload_to_run_events
from cleair_backend.store import TraceStore


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="cleAIr backend")
store = TraceStore()
auth_config = load_auth_config()
allowed_origins = [
    origin for origin in os.environ.get("CLEAIR_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _resolve_channel(request: Request) -> None:
    api_key = request.headers.get("X-Channel-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-Channel-API-Key header")
    if not store.has_api_key(api_key):
        raise HTTPException(status_code=404, detail="Unknown API key")


async def _generate_sse():
    queue, replay_events = store.subscribe()
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
        store.unsubscribe(queue)


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


@app.post("/channel", status_code=201)
async def create_channel(request: Request) -> dict:
    require_authenticated_request(request, auth_config)
    return {"apiKey": store.ensure_channel()}


@app.get("/agents")
async def list_agents(request: Request) -> list[dict]:
    require_authenticated_request(request, auth_config)
    return store.list_agents()


@app.post("/v1/traces", status_code=204)
async def ingest_otlp_traces(request: Request) -> None:
    _resolve_channel(request)
    payload = await request.json()
    for trace_id, service_name, span_events in otlp_payload_to_run_events(payload):
        is_new_run = store.start_run(service_name, trace_id)
        events_to_emit = [{"type": "run_started", "runId": trace_id, "runLabel": service_name}] if is_new_run else []
        events_to_emit.extend(span_events)
        store.append_events(service_name, events_to_emit)
        if any(event.get("type") == "run_completed" for event in span_events):
            store.mark_completed(service_name)
        logger.info("Ingested %d events for trace %s (%s)", len(events_to_emit), trace_id, service_name)


@app.post("/v1/events", status_code=204)
async def ingest_events(request: Request) -> None:
    _resolve_channel(request)
    body = await request.json()
    run_id = body["runId"]
    events: list[dict] = body["events"]
    run_label = next((event["runLabel"] for event in events if event.get("type") == "run_started"), None)
    if run_label is not None:
        store.start_run(run_label, run_id)
        service_name = run_label
    else:
        service_name = store.get_service_name_for_run(run_id)
        if service_name is None:
            raise HTTPException(status_code=400, detail="Unknown runId")
    store.append_events(service_name, events)
    if any(event.get("type") == "run_completed" for event in events):
        store.mark_completed(service_name)


@app.get("/channel/stream")
async def stream_channel(request: Request) -> StreamingResponse:
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
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.environ.get("CLEAIR_BACKEND_RELOAD", "").lower() in {"1", "true", "yes", "on"},
        help="Enable autoreload for local development.",
    )
    args = parser.parse_args()
    uvicorn.run("cleair_backend.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    run()

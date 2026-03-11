"""cleAIr backend — trace ingestion and SSE streaming.

Endpoints:
  POST /channels                  — Create a new channel, returns {label, apiKey}
  GET  /channels                  — List all channels
  GET  /channels/{api_key}/stream — SSE stream for a channel's latest run
  POST /v1/traces                 — OTLP/JSON trace ingestion (requires X-Channel-API-Key)
  POST /v1/events                 — Cleair-native event ingestion (requires X-Channel-API-Key)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from cleair_backend.otlp import otlp_payload_to_run_events
from cleair_backend.store import TraceStore




logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="cleAIr backend")
store = TraceStore()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)




####
# Helpers
####
def _resolve_channel(request: Request) -> TraceStore:
    """Resolve the target TraceStore from X-Channel-API-Key, or raise HTTP error."""
    api_key = request.headers.get("X-Channel-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-Channel-API-Key header")
    channel = store.get_channel(api_key)
    if channel is None:
        raise HTTPException(status_code=404, detail="Unknown API key")
    return channel


async def _generate_sse(channel: TraceStore):
    """Yield SSE-formatted events for a TraceStore, following its latest run."""
    seen_run_ids: set[str] = set()
    while True:
        run_id = channel.get_latest_run_id()
        if run_id is None or run_id in seen_run_ids:
            yield ":\n\n"
            await channel.wait_for_new_run()
            continue
        seen_run_ids.add(run_id)
        run = channel.get_run(run_id)
        if run is None: continue
        queue = channel.subscribe(run_id)
        try:
            for event in list(run.events): yield f"data: {json.dumps(event)}\n\n"
            if run.is_completed: continue
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("type") == "run_completed": break
                except asyncio.TimeoutError:
                    yield ":\n\n"
        finally:
            channel.unsubscribe(run_id, queue)




#### API ####

####
# Channel management
####
@app.post("/channels", status_code=201)
async def create_channel() -> dict:
    """Create a new isolated channel. Returns its label and API key."""
    label, api_key = store.create_channel()
    return {"label": label, "apiKey": api_key}


@app.get("/channels")
async def list_channels() -> list[dict]:
    """List all channels with their API keys."""
    return store.list_channels()


@app.delete("/channels/{api_key}", status_code=204)
async def delete_channel(api_key: str) -> None:
    """Delete a channel and all its data."""
    if not store.delete_channel(api_key):
        raise HTTPException(status_code=404, detail="Unknown API key")


####
# Trace ingestion
####
@app.post("/v1/traces", status_code=204)
async def ingest_otlp_traces(request: Request) -> None:
    """Accept an OTLP/JSON ExportTraceServiceRequest.

    Spans arrive only on completion, so the frontend will see all events for a
    span appear at once. Use /v1/events for real-time streaming.
    """
    channel = _resolve_channel(request)
    payload = await request.json()
    for trace_id, service_name, span_events in otlp_payload_to_run_events(payload):
        run = channel.get_or_create_run(trace_id, service_name)
        events_to_emit: list[dict] = []
        if not run.events:
            events_to_emit.append({"type": "run_started", "runId": trace_id, "runLabel": service_name})
        events_to_emit.extend(span_events)
        channel.append_events(trace_id, events_to_emit)
        if any(e.get("type") == "run_completed" for e in span_events):
            channel.mark_completed(trace_id)
        logger.info("Ingested %d events for trace %s", len(events_to_emit), trace_id)


@app.post("/v1/events", status_code=204)
async def ingest_events(request: Request) -> None:
    """Accept a batch of FlowGraphEvents from the cleair-native streaming exporter.

    Events arrive on both span start and span end, enabling real-time running state.
    Body: { "runId": str, "events": FlowGraphEvent[] }
    """
    channel = _resolve_channel(request)
    body = await request.json()
    run_id: str = body["runId"]
    events: list[dict] = body["events"]

    run_label = next((e["runLabel"] for e in events if e.get("type") == "run_started"), None)
    channel.get_or_create_run(run_id, run_label or "unknown")
    channel.append_events(run_id, events)
    if any(e.get("type") == "run_completed" for e in events):
        channel.mark_completed(run_id)


####
# SSE streaming
####
@app.get("/channels/{api_key}/stream")
async def stream_channel(api_key: str) -> StreamingResponse:
    """SSE stream that always follows the latest run in a channel."""
    channel = store.get_channel(api_key)
    if channel is None:
        raise HTTPException(status_code=404, detail="Unknown API key")
    return StreamingResponse(_generate_sse(channel),
                             media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


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

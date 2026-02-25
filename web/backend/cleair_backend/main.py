"""cleAIr backend — trace ingestion and SSE streaming.

Endpoints:
  POST /v1/traces          — OTLP/JSON trace ingestion (batch, spans exported on completion)
  POST /v1/events          — Cleair-native event ingestion (streaming, start + end events)
  GET  /runs/latest/stream — SSE stream of FlowGraphEvents for the latest run
"""
from __future__ import annotations

import asyncio
import json
import logging

import uvicorn
from fastapi import FastAPI, Request
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
    allow_origins=["*"],  # tighten when adding API-key auth
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.post("/v1/traces", status_code=204)
async def ingest_otlp_traces(request: Request) -> None:
    """Accept an OTLP/JSON ExportTraceServiceRequest.

    Spans arrive only on completion, so the frontend will see all events for a
    span appear at once. Use /v1/events for real-time streaming.
    """
    payload = await request.json()
    for trace_id, service_name, span_events in otlp_payload_to_run_events(payload):
        run = store.get_or_create_run(trace_id, service_name)
        events_to_emit: list[dict] = []
        if not run.events:
            events_to_emit.append({"type": "run_started", "runId": trace_id, "runLabel": service_name})
        events_to_emit.extend(span_events)
        store.append_events(trace_id, events_to_emit)
        if any(e.get("type") == "run_completed" for e in span_events):
            store.mark_completed(trace_id)
        logger.info("Ingested %d events for trace %s", len(events_to_emit), trace_id)


@app.post("/v1/events", status_code=204)
async def ingest_events(request: Request) -> None:
    """Accept a batch of FlowGraphEvents from the cleair-native streaming exporter.

    Events arrive on both span start and span end, enabling real-time running state.
    Body: { "runId": str, "events": FlowGraphEvent[] }
    """
    body = await request.json()
    run_id: str = body["runId"]
    events: list[dict] = body["events"]

    run_label = next((e["runLabel"] for e in events if e.get("type") == "run_started"), None)
    store.get_or_create_run(run_id, run_label or "unknown")
    store.append_events(run_id, events)
    if any(e.get("type") == "run_completed" for e in events):
        store.mark_completed(run_id)


@app.get("/runs/latest/stream")
async def stream_latest_run() -> StreamingResponse:
    """SSE stream that always follows the latest run.

    When a new run starts it emits a run_started event which resets the frontend
    graph; the browser reconnects automatically on disconnect.
    """
    async def generate():
        seen_run_ids: set[str] = set()
        while True:
            run_id = store.get_latest_run_id()
            if run_id is None or run_id in seen_run_ids:
                yield ":\n\n"
                await store.wait_for_new_run()
                continue

            seen_run_ids.add(run_id)
            run = store.get_run(run_id)
            if run is None:
                continue

            queue = store.subscribe(run_id)
            try:
                for event in list(run.events):
                    yield f"data: {json.dumps(event)}\n\n"

                if run.is_completed:
                    continue

                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=30)
                        yield f"data: {json.dumps(event)}\n\n"
                        if event.get("type") == "run_completed":
                            break
                    except asyncio.TimeoutError:
                        yield ":\n\n"
            finally:
                store.unsubscribe(run_id, queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def run() -> None:
    uvicorn.run("cleair_backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()

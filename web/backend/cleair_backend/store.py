"""In-memory trace store.

Separates persistent state (events, metadata) from pub/sub state (asyncio queues).
Swap the `_runs` dict storage with DB queries to add persistence without touching
the pub/sub or SSE logic.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RunState:
    run_id: str
    service_name: str
    started_at: datetime

    # Persistent state — the only part that touches storage when adding a DB.
    events: list[dict] = field(default_factory=list)
    is_completed: bool = False

    # In-process pub/sub — always lives in memory regardless of storage backend.
    _subscribers: list[asyncio.Queue] = field(default_factory=list)


class TraceStore:
    def __init__(self) -> None:
        self._runs: dict[str, RunState] = {}
        self._run_order: list[str] = []  # insertion order → latest = last
        self._new_run_event: asyncio.Event = asyncio.Event()

    def get_or_create_run(self, run_id: str, service_name: str) -> RunState:
        if run_id not in self._runs:
            self._runs[run_id] = RunState(
                run_id=run_id,
                service_name=service_name,
                started_at=datetime.now(timezone.utc),
            )
            self._run_order.append(run_id)
            self._new_run_event.set()
        return self._runs[run_id]

    def get_run(self, run_id: str) -> RunState | None:
        return self._runs.get(run_id)

    def get_latest_run_id(self) -> str | None:
        return self._run_order[-1] if self._run_order else None

    async def wait_for_new_run(self) -> None:
        """Block until a new run is created, then reset the signal."""
        await self._new_run_event.wait()
        self._new_run_event.clear()

    def append_events(self, run_id: str, events: list[dict]) -> None:
        """Store events and fan out to all current SSE subscribers."""
        run = self._runs.get(run_id)
        if run is None:
            return
        run.events.extend(events)
        for queue in run._subscribers:
            for event in events:
                queue.put_nowait(event)

    def mark_completed(self, run_id: str) -> None:
        run = self._runs.get(run_id)
        if run:
            run.is_completed = True

    def subscribe(self, run_id: str) -> asyncio.Queue:
        run = self._runs[run_id]
        queue: asyncio.Queue = asyncio.Queue()
        run._subscribers.append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue) -> None:
        run = self._runs.get(run_id)
        if run and queue in run._subscribers:
            run._subscribers.remove(queue)

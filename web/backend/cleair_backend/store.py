from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AgentRunState:
    service_name: str
    run_id: str
    started_at: datetime
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    is_completed: bool = False


class TraceStore:
    def __init__(self) -> None:
        self._api_key: str | None = None
        self._agents: dict[str, AgentRunState] = {}
        self._agent_order: list[str] = []
        self._subscribers: list[asyncio.Queue] = []

    def ensure_channel(self) -> str:
        if self._api_key is None:
            self._api_key = secrets.token_hex(16)
        return self._api_key

    def has_api_key(self, api_key: str) -> bool:
        return api_key == self._api_key

    def list_agents(self) -> list[dict]:
        return [
            {
                "serviceName": self._agents[run_id].service_name,
                "runId": run_id,
                "metadata": dict(self._agents[run_id].metadata),
                "events": list(self._agents[run_id].events),
            }
            for run_id in self._agent_order
        ]

    def start_run(self, service_name: str, run_id: str, metadata: dict[str, str | int | float | bool] | None = None) -> bool:
        existing_run = self._agents.get(run_id)
        if existing_run is not None:
            return False
        self._agents[run_id] = AgentRunState(
            service_name=service_name,
            run_id=run_id,
            started_at=datetime.now(timezone.utc),
            metadata=dict(metadata or {}),
        )
        self._agent_order = [run_id, *[known_run_id for known_run_id in self._agent_order if known_run_id != run_id]]
        return True

    def get_service_name_for_run(self, run_id: str) -> str | None:
        agent_run = self._agents.get(run_id)
        return None if agent_run is None else agent_run.service_name

    def append_events(self, run_id: str, events: list[dict]) -> None:
        agent_run = self._agents.get(run_id)
        if agent_run is None:
            return
        agent_run.events.extend(events)
        self._agent_order = [run_id, *[known_run_id for known_run_id in self._agent_order if known_run_id != run_id]]
        for queue in self._subscribers:
            for event in events:
                queue.put_nowait({"runId": run_id, "serviceName": agent_run.service_name, "event": event})

    def mark_completed(self, run_id: str) -> None:
        agent_run = self._agents.get(run_id)
        if agent_run is not None:
            agent_run.is_completed = True

    def delete_run(self, run_id: str) -> bool:
        if run_id not in self._agents:
            return False
        del self._agents[run_id]
        self._agent_order = [known_run_id for known_run_id in self._agent_order if known_run_id != run_id]
        return True

    def subscribe(self) -> tuple[asyncio.Queue, list[dict]]:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        replay_events = [
            {"runId": run_id, "serviceName": self._agents[run_id].service_name, "event": event}
            for run_id in self._agent_order
            for event in self._agents[run_id].events
        ]
        return queue, replay_events

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

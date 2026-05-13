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
    events: list[dict] = field(default_factory=list)
    is_completed: bool = False


class TraceStore:
    def __init__(self) -> None:
        self._api_key: str | None = None
        self._agents: dict[str, AgentRunState] = {}
        self._agent_order: list[str] = []
        self._run_to_service_name: dict[str, str] = {}
        self._subscribers: list[asyncio.Queue] = []

    def ensure_channel(self) -> str:
        if self._api_key is None:
            self._api_key = secrets.token_hex(16)
        return self._api_key

    def has_api_key(self, api_key: str) -> bool:
        return api_key == self._api_key

    def list_agents(self) -> list[dict]:
        return [
            {"serviceName": service_name, "runId": self._agents[service_name].run_id, "events": list(self._agents[service_name].events)}
            for service_name in self._agent_order
        ]

    def start_run(self, service_name: str, run_id: str) -> bool:
        existing_run = self._agents.get(service_name)
        if existing_run is not None and existing_run.run_id == run_id:
            return False
        for known_run_id, known_service_name in list(self._run_to_service_name.items()):
            if known_service_name == service_name:
                del self._run_to_service_name[known_run_id]
        self._run_to_service_name[run_id] = service_name
        self._agents[service_name] = AgentRunState(service_name=service_name, run_id=run_id, started_at=datetime.now(timezone.utc))
        self._agent_order = [service_name, *[known_service_name for known_service_name in self._agent_order if known_service_name != service_name]]
        return True

    def get_service_name_for_run(self, run_id: str) -> str | None:
        return self._run_to_service_name.get(run_id)

    def append_events(self, service_name: str, events: list[dict]) -> None:
        agent_run = self._agents.get(service_name)
        if agent_run is None:
            return
        agent_run.events.extend(events)
        self._agent_order = [service_name, *[known_service_name for known_service_name in self._agent_order if known_service_name != service_name]]
        for queue in self._subscribers:
            for event in events:
                queue.put_nowait({"serviceName": service_name, "event": event})

    def mark_completed(self, service_name: str) -> None:
        agent_run = self._agents.get(service_name)
        if agent_run is not None:
            agent_run.is_completed = True

    def subscribe(self) -> tuple[asyncio.Queue, list[dict]]:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        replay_events = [
            {"serviceName": service_name, "event": event}
            for service_name in self._agent_order
            for event in self._agents[service_name].events
        ]
        return queue, replay_events

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

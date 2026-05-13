import { useEffect, useRef, useState } from "react";
import { applyTraceTreeEvent, createEmptyTraceTree } from "../traceTree";
import type { TraceTreeEvent, TraceTreeState } from "../types";

const EMPTY_RUN_ID = "—";
const EMPTY_RUN_LABEL = "Waiting for trace…";

type ConnectionStatus = "connecting" | "connected" | "offline";

type AgentSnapshot = {
  serviceName: string;
  runId: string;
  events: TraceTreeEvent[];
};

type StreamedAgentEvent = {
  serviceName: string;
  event: TraceTreeEvent;
};

export type AgentTrace = {
  serviceName: string;
  traceTree: TraceTreeState;
  selectedNodeId: string | null;
};

function hydrateTraceTree(runId: string, serviceName: string, events: TraceTreeEvent[]): TraceTreeState {
  let traceTree = createEmptyTraceTree(runId, serviceName);
  for (const event of events) {
    traceTree = applyTraceTreeEvent(traceTree, event);
  }
  return traceTree;
}

function upsertAgent(previousAgents: AgentTrace[], serviceName: string, update: (agent: AgentTrace) => AgentTrace): AgentTrace[] {
  const existingAgent = previousAgents.find((agent) => agent.serviceName === serviceName);
  const baseAgent = existingAgent ?? {
    serviceName,
    traceTree: createEmptyTraceTree(EMPTY_RUN_ID, EMPTY_RUN_LABEL),
    selectedNodeId: null,
  };
  return [update(baseAgent), ...previousAgents.filter((agent) => agent.serviceName !== serviceName)];
}

export function useAgents(backendUrl: string, enabled: boolean, refreshAccessState: () => Promise<void>) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentTrace[]>([]);
  const [selectedAgentName, setSelectedAgentName] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled) {
      sourceRef.current?.close();
      sourceRef.current = null;
      setApiKey(null);
      setAgents([]);
      setSelectedAgentName(null);
      setConnectionStatus("connecting");
      return;
    }

    let cancelled = false;

    async function load() {
      try {
        setConnectionStatus("connecting");
        const channelResponse = await fetch(`${backendUrl}/channel`, { method: "POST", credentials: "include" });
        if (channelResponse.status === 401) {
          await refreshAccessState();
          return;
        }
        if (!channelResponse.ok) {
          throw new Error(`Server returned ${channelResponse.status}`);
        }
        const channel = (await channelResponse.json()) as { apiKey: string };
        const agentsResponse = await fetch(`${backendUrl}/agents`, { credentials: "include" });
        if (agentsResponse.status === 401) {
          await refreshAccessState();
          return;
        }
        if (!agentsResponse.ok) {
          throw new Error(`Server returned ${agentsResponse.status}`);
        }
        const agentSnapshots = (await agentsResponse.json()) as AgentSnapshot[];
        if (cancelled) {
          return;
        }
        setApiKey(channel.apiKey);
        setAgents(
          agentSnapshots.map((agentSnapshot) => ({
            serviceName: agentSnapshot.serviceName,
            traceTree: hydrateTraceTree(agentSnapshot.runId, agentSnapshot.serviceName, agentSnapshot.events),
            selectedNodeId: null,
          }))
        );
        setSelectedAgentName((currentSelectedAgentName) => currentSelectedAgentName ?? agentSnapshots[0]?.serviceName ?? null);
      } catch (error) {
        console.error("[cleair] Failed to load agents:", error);
        setConnectionStatus("offline");
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [backendUrl, enabled, refreshAccessState]);

  useEffect(() => {
    if (!enabled || apiKey === null) {
      return;
    }
    sourceRef.current?.close();
    const source = new EventSource(`${backendUrl}/channel/stream`, { withCredentials: true });
    sourceRef.current = source;

    source.onopen = () => setConnectionStatus("connected");
    source.onmessage = (messageEvent) => {
      const streamedEvent = JSON.parse(messageEvent.data as string) as StreamedAgentEvent;
      setAgents((previousAgents) =>
        upsertAgent(previousAgents, streamedEvent.serviceName, (agent) => ({
          ...agent,
          traceTree: applyTraceTreeEvent(agent.traceTree, streamedEvent.event),
          selectedNodeId: streamedEvent.event.type === "run_started" ? null : agent.selectedNodeId,
        }))
      );
      setSelectedAgentName((currentSelectedAgentName) => currentSelectedAgentName ?? streamedEvent.serviceName);
    };
    source.onerror = () => {
      void refreshAccessState();
      setConnectionStatus("offline");
    };

    return () => {
      source.close();
      if (sourceRef.current === source) {
        sourceRef.current = null;
      }
    };
  }, [apiKey, backendUrl, enabled, refreshAccessState]);

  const setSelectedNodeId = (nodeId: string | null) => {
    if (selectedAgentName === null) {
      return;
    }
    setAgents((previousAgents) =>
      previousAgents.map((agent) => agent.serviceName === selectedAgentName ? { ...agent, selectedNodeId: nodeId } : agent)
    );
  };

  return { apiKey, agents, selectedAgentName, setSelectedAgentName, connectionStatus, setSelectedNodeId };
}

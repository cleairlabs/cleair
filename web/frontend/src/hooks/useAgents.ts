import { useEffect, useRef, useState } from "react";
import { applyTraceTreeEvent, createEmptyTraceTree } from "../traceTree";
import type { TraceTreeEvent, TraceTreeState } from "../types";

const EMPTY_RUN_ID = "—";
const EMPTY_RUN_LABEL = "Waiting for trace…";

type ConnectionStatus = "connecting" | "connected" | "offline";

type AgentSnapshot = {
  serviceName: string;
  runId: string;
  metadata: Record<string, string | number | boolean>;
  events: TraceTreeEvent[];
};

type StreamedAgentEvent = {
  runId: string;
  serviceName: string;
  event: TraceTreeEvent;
};

export type AgentTrace = {
  runId: string;
  serviceName: string;
  displayName: string;
  batchId: string | null;
  traceTree: TraceTreeState;
  selectedNodeId: string | null;
};

function readAgentMetadata(metadata: Record<string, string | number | boolean> | undefined, serviceName: string) {
  return {
    displayName: String(metadata?.["agent.id"] ?? serviceName),
    batchId: metadata?.["batch.id"] === undefined ? null : String(metadata["batch.id"]),
  };
}

function hydrateTraceTree(runId: string, serviceName: string, events: TraceTreeEvent[]): TraceTreeState {
  let traceTree = createEmptyTraceTree(runId, serviceName);
  for (const event of events) {
    traceTree = applyTraceTreeEvent(traceTree, event);
  }
  return traceTree;
}

function upsertAgent(previousAgents: AgentTrace[], runId: string, update: (agent: AgentTrace) => AgentTrace): AgentTrace[] {
  const existingAgent = previousAgents.find((agent) => agent.runId === runId);
  const baseAgent = existingAgent ?? {
    runId,
    serviceName: EMPTY_RUN_LABEL,
    displayName: EMPTY_RUN_LABEL,
    batchId: null,
    traceTree: createEmptyTraceTree(EMPTY_RUN_ID, EMPTY_RUN_LABEL),
    selectedNodeId: null,
  };
  return [update(baseAgent), ...previousAgents.filter((agent) => agent.runId !== runId)];
}

export function useAgents(backendUrl: string, enabled: boolean, refreshAccessState: () => Promise<void>) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentTrace[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled) {
      sourceRef.current?.close();
      sourceRef.current = null;
      setApiKey(null);
      setAgents([]);
      setSelectedRunId(null);
      setConnectionStatus("connecting");
      return;
    }

    let cancelled = false;

    async function load() {
      try {
        setConnectionStatus("connecting");
        const apiKeyResponse = await fetch(`${backendUrl}/api-key`, { method: "POST", credentials: "include" });
        if (apiKeyResponse.status === 401) {
          await refreshAccessState();
          return;
        }
        if (!apiKeyResponse.ok) {
          throw new Error(`Server returned ${apiKeyResponse.status}`);
        }
        const apiKeyPayload = (await apiKeyResponse.json()) as { apiKey: string };
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
        setApiKey(apiKeyPayload.apiKey);
        setAgents(
          agentSnapshots.map((agentSnapshot) => ({
            runId: agentSnapshot.runId,
            serviceName: agentSnapshot.serviceName,
            ...readAgentMetadata(agentSnapshot.metadata, agentSnapshot.serviceName),
            traceTree: hydrateTraceTree(agentSnapshot.runId, agentSnapshot.serviceName, agentSnapshot.events),
            selectedNodeId: null,
          }))
        );
        setSelectedRunId((currentSelectedRunId) => currentSelectedRunId ?? agentSnapshots[0]?.runId ?? null);
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
    const source = new EventSource(`${backendUrl}/events`, { withCredentials: true });
    sourceRef.current = source;

    source.onopen = () => setConnectionStatus("connected");
    source.onmessage = (messageEvent) => {
      const streamedEvent = JSON.parse(messageEvent.data as string) as StreamedAgentEvent;
      setAgents((previousAgents) =>
        upsertAgent(previousAgents, streamedEvent.runId, (agent) => {
          const metadata = streamedEvent.event.type === "run_started"
            ? readAgentMetadata(streamedEvent.event.metadata, streamedEvent.serviceName)
            : agent;
          return {
            ...agent,
            serviceName: streamedEvent.serviceName,
            displayName: metadata.displayName,
            batchId: metadata.batchId,
            traceTree: applyTraceTreeEvent(agent.traceTree, streamedEvent.event),
            selectedNodeId: streamedEvent.event.type === "run_started" ? null : agent.selectedNodeId,
          };
        })
      );
      setSelectedRunId((currentSelectedRunId) => currentSelectedRunId ?? streamedEvent.runId);
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
    if (selectedRunId === null) {
      return;
    }
    setAgents((previousAgents) =>
      previousAgents.map((agent) => agent.runId === selectedRunId ? { ...agent, selectedNodeId: nodeId } : agent)
    );
  };

  const deleteRun = async (runId: string) => {
    const response = await fetch(`${backendUrl}/agents/${runId}`, { method: "DELETE", credentials: "include" });
    if (response.status === 401) {
      await refreshAccessState()
      return;
    }
    if (response.status === 404) {
      setAgents((previousAgents) => previousAgents.filter((agent) => agent.runId !== runId));
      setSelectedRunId((currentSelectedRunId) => currentSelectedRunId === runId ? null : currentSelectedRunId);
      return;
    }
    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }
    setAgents((previousAgents) => previousAgents.filter((agent) => agent.runId !== runId));
    setSelectedRunId((currentSelectedRunId) => currentSelectedRunId === runId ? null : currentSelectedRunId);
  };

  return { apiKey, agents, selectedRunId, setSelectedRunId, connectionStatus, setSelectedNodeId, deleteRun };
}

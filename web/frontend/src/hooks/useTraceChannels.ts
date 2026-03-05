import { useEffect, useMemo, useRef, useState } from "react";
import { applyTraceTreeEvent, createEmptyTraceTree } from "../traceTree";
import type { TraceTreeEvent, TraceTreeState } from "../types";

const EMPTY_RUN_ID = "—";
const EMPTY_RUN_LABEL = "Waiting for trace…";

type ConnectionStatus = "connecting" | "connected" | "offline";

export type Pane = {
  id: string;
  label: string;
  apiKey: string;
  traceTree: TraceTreeState;
  selectedNodeId: string | null;
  connectionStatus: ConnectionStatus;
};

function makePane(label: string, apiKey: string): Pane {
  return {
    id: apiKey,
    label,
    apiKey,
    traceTree: createEmptyTraceTree(EMPTY_RUN_ID, EMPTY_RUN_LABEL),
    selectedNodeId: null,
    connectionStatus: "connecting",
  };
}

export function useTraceChannels(backendUrl: string) {
  const [panes, setPanes] = useState<Pane[]>([]);
  const [activePaneId, setActivePaneId] = useState<string | null>(null);
  const sourcesRef = useRef<Map<string, EventSource>>(new Map());

  useEffect(() => {
    fetch(`${backendUrl}/channels`)
      .then((response) => response.json())
      .then((channels: Array<{ apiKey: string; label: string }>) => {
        if (channels.length === 0) return;
        const restoredPanes = channels.map((channel) => makePane(channel.label, channel.apiKey));
        setPanes(restoredPanes);
        setActivePaneId(restoredPanes[0].id);
      })
      .catch(() => {});
  }, [backendUrl]);

  const paneKeys = useMemo(() => panes.map((pane) => pane.apiKey).join(","), [panes]);

  useEffect(() => {
    const currentKeys = new Set(panes.map((pane) => pane.apiKey));

    for (const [key, source] of sourcesRef.current) {
      if (!currentKeys.has(key)) {
        source.close();
        sourcesRef.current.delete(key);
      }
    }

    for (const pane of panes) {
      if (sourcesRef.current.has(pane.apiKey)) continue;
      const { apiKey } = pane;
      const source = new EventSource(`${backendUrl}/channels/${apiKey}/stream`);

      source.onopen = () =>
        setPanes((previousPanes) =>
          previousPanes.map((previousPane) =>
            previousPane.apiKey === apiKey ? { ...previousPane, connectionStatus: "connected" } : previousPane
          )
        );

      source.onmessage = (messageEvent) => {
        const event = JSON.parse(messageEvent.data as string) as TraceTreeEvent;
        setPanes((previousPanes) =>
          previousPanes.map((previousPane) => {
            if (previousPane.apiKey !== apiKey) return previousPane;
            return {
              ...previousPane,
              traceTree: applyTraceTreeEvent(previousPane.traceTree, event),
              selectedNodeId: event.type === "run_started" ? null : previousPane.selectedNodeId,
            };
          })
        );
      };

      source.onerror = () =>
        setPanes((previousPanes) =>
          previousPanes.map((previousPane) =>
            previousPane.apiKey === apiKey ? { ...previousPane, connectionStatus: "offline" } : previousPane
          )
        );

      sourcesRef.current.set(apiKey, source);
    }
  }, [backendUrl, paneKeys, panes]);

  useEffect(() => {
    return () => {
      for (const source of sourcesRef.current.values()) source.close();
    };
  }, []);

  const addPane = async () => {
    try {
      const response = await fetch(`${backendUrl}/channels`, { method: "POST" });
      if (!response.ok) throw new Error(`Server returned ${response.status}`);
      const { label, apiKey } = (await response.json()) as { label: string; apiKey: string };
      const newPane = makePane(label, apiKey);
      setPanes((previousPanes) => [...previousPanes, newPane]);
      setActivePaneId(apiKey);
    } catch (error) {
      console.error("[cleair] Failed to create channel:", error);
      alert(`Could not reach backend at ${backendUrl}.\nMake sure the server is running.`);
    }
  };

  const setSelectedNodeId = (nodeId: string | null) => {
    if (!activePaneId) return;
    setPanes((previousPanes) =>
      previousPanes.map((previousPane) =>
        previousPane.apiKey === activePaneId ? { ...previousPane, selectedNodeId: nodeId } : previousPane
      )
    );
  };

  return {
    panes,
    activePaneId,
    setActivePaneId,
    addPane,
    setSelectedNodeId,
  };
}

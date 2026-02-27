import { useEffect, useRef, useState } from "react";
import { TraceTree } from "./components/TraceTree";
import { applyTraceTreeEvent, countNodesByStatus, createEmptyTraceTree, formatDuration } from "./traceTree";
import { kindColors } from "./kinds";
import type { TraceTreeState, TraceTreeEvent, FlowNode } from "./types";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";
const EMPTY_RUN_ID = "—";
const EMPTY_RUN_LABEL = "Waiting for trace…";

type ConnectionStatus = "connecting" | "connected" | "offline";

type Pane = {
  id: string;
  label: string;
  apiKey: string;
  traceTree: TraceTreeState;
  selectedNodeId: string | null;
  connectionStatus: ConnectionStatus;
};

function ConnectionIndicator({ status }: { status: ConnectionStatus }) {
  return (
    <span className={`connection-indicator connection-${status}`}>
      {status === "connecting" && "connecting"}
      {status === "connected" && "live"}
      {status === "offline" && "offline"}
    </span>
  );
}

function ApiKeyBadge({ apiKey }: { apiKey: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button className="api-key-badge" onClick={copy} title={apiKey}>
      <span className="api-key-label">KEY</span>
      <span className="api-key-value">{apiKey.slice(0, 8)}…</span>
      <span className="api-key-copy">{copied ? "✓ copied" : "copy"}</span>
    </button>
  );
}

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

export default function App() {
  const [panes, setPanes] = useState<Pane[]>([]);
  const [activePaneId, setActivePaneId] = useState<string | null>(null);
  const sourcesRef = useRef<Map<string, EventSource>>(new Map());

  // Restore existing channels on mount.
  useEffect(() => {
    fetch(`${BACKEND_URL}/channels`)
      .then((r) => r.json())
      .then((channels: Array<{ apiKey: string; label: string }>) => {
        if (channels.length === 0) return;
        const restored = channels.map((ch) => makePane(ch.label, ch.apiKey));
        setPanes(restored);
        setActivePaneId(restored[0].id);
      })
      .catch(() => {});
  }, []);

  // Open / close EventSource connections as panes change.
  const paneKeys = panes.map((p) => p.apiKey).join(",");
  useEffect(() => {
    const currentKeys = new Set(panes.map((p) => p.apiKey));

    // Close sources for removed panes.
    for (const [key, source] of sourcesRef.current) {
      if (!currentKeys.has(key)) {
        source.close();
        sourcesRef.current.delete(key);
      }
    }

    // Open sources for new panes.
    for (const pane of panes) {
      if (sourcesRef.current.has(pane.apiKey)) continue;
      const { apiKey } = pane;
      const source = new EventSource(`${BACKEND_URL}/channels/${apiKey}/stream`);

      source.onopen = () =>
        setPanes((prev) =>
          prev.map((p) => (p.apiKey === apiKey ? { ...p, connectionStatus: "connected" } : p))
        );

      source.onmessage = (msgEvent) => {
        const event = JSON.parse(msgEvent.data as string) as TraceTreeEvent;
        setPanes((prev) =>
          prev.map((p) => {
            if (p.apiKey !== apiKey) return p;
            return {
              ...p,
              traceTree: applyTraceTreeEvent(p.traceTree, event),
              selectedNodeId: event.type === "run_started" ? null : p.selectedNodeId,
            };
          })
        );
      };

      source.onerror = () =>
        setPanes((prev) =>
          prev.map((p) => (p.apiKey === apiKey ? { ...p, connectionStatus: "offline" } : p))
        );

      sourcesRef.current.set(apiKey, source);
    }
  }, [paneKeys]); // eslint-disable-line react-hooks/exhaustive-deps

  // Close all sources on unmount.
  useEffect(() => {
    return () => {
      for (const source of sourcesRef.current.values()) source.close();
    };
  }, []);

  const addPane = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/channels`, { method: "POST" });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const { label, apiKey } = (await res.json()) as { label: string; apiKey: string };
      const newPane = makePane(label, apiKey);
      setPanes((prev) => [...prev, newPane]);
      setActivePaneId(apiKey);
    } catch (err) {
      console.error("[cleair] Failed to create channel:", err);
      alert(`Could not reach backend at ${BACKEND_URL}.\nMake sure the server is running.`);
    }
  };

  const setSelectedNodeId = (nodeId: string | null) => {
    if (!activePaneId) return;
    const key = activePaneId;
    setPanes((prev) => prev.map((p) => (p.apiKey === key ? { ...p, selectedNodeId: nodeId } : p)));
  };

  const activePane = panes.find((p) => p.id === activePaneId) ?? null;
  const traceTree = activePane?.traceTree ?? createEmptyTraceTree(EMPTY_RUN_ID, EMPTY_RUN_LABEL);

  const resolvedSelectedNodeId =
    activePane?.selectedNodeId !== null &&
    activePane?.selectedNodeId !== undefined &&
    traceTree.nodesById[activePane.selectedNodeId] !== undefined
      ? activePane.selectedNodeId
      : (traceTree.nodeIdsInOrder[0] ?? null);

  const selectedNode: FlowNode | null = resolvedSelectedNodeId
    ? (traceTree.nodesById[resolvedSelectedNodeId] ?? null)
    : null;

  const doneCount = countNodesByStatus(traceTree, "done");
  const errorCount = countNodesByStatus(traceTree, "error");

  return (
    <div className="app-root">
      <div className="tab-bar">
        {panes.map((pane) => (
          <button
            key={pane.id}
            className={`tab${pane.id === activePaneId ? " tab-active" : ""}`}
            onClick={() => setActivePaneId(pane.id)}
          >
            {pane.label}
          </button>
        ))}
        <button className="tab-add" onClick={addPane} title="Add pane">
          +
        </button>
      </div>

      {activePane === null ? (
        <div className="empty-state">
          <p>
            Click <strong>+</strong> to create a pane, then paste its API key into your SDK init.
          </p>
        </div>
      ) : (
        <main className="app-layout">
          <section className="panel">
            <header className="panel-header">
              <span className="panel-label">Trace</span>
              <span className="panel-header-title">{traceTree.runLabel}</span>
              <div className="spacer" />
              <ApiKeyBadge apiKey={activePane.apiKey} />
              <ConnectionIndicator status={activePane.connectionStatus} />
            </header>
            {traceTree.nodeIdsInOrder.length === 0 ? (
              <p className="trace-empty">No trace data yet. Run your agent to see a trace here.</p>
            ) : (
              <TraceTree
                traceTree={traceTree}
                selectedNodeId={resolvedSelectedNodeId}
                onSelectNode={setSelectedNodeId}
              />
            )}
          </section>

          <section className="panel details-panel">
            <header className="panel-header">
              <span className="panel-label">Details</span>
            </header>
            <div className="details-content">
              {selectedNode ? (
                <>
                  <div className="detail-section">
                    <span className="detail-label">Step</span>
                    <div className="detail-step-name">
                      <span className="detail-kind-dot" style={{ background: kindColors[selectedNode.kind] }} />
                      <span className="detail-value">{selectedNode.label}</span>
                    </div>
                    <span className="detail-value detail-muted">{selectedNode.subtitle}</span>
                  </div>
                  {selectedNode.durationMs !== null && (
                    <div className="detail-section">
                      <span className="detail-label">Duration</span>
                      <span className="detail-value">{formatDuration(selectedNode.durationMs)}</span>
                    </div>
                  )}
                  <div className="detail-section">
                    <span className="detail-label">What</span>
                    <p className="detail-body">{selectedNode.whatDescription}</p>
                  </div>
                  <div className="detail-section">
                    <span className="detail-label">Why</span>
                    <p className="detail-body">{selectedNode.whyDescription}</p>
                  </div>
                  {selectedNode.output !== null && (
                    <div className="detail-section">
                      <span className="detail-label">Output</span>
                      <pre className="detail-output">{selectedNode.output}</pre>
                    </div>
                  )}
                </>
              ) : (
                <p className="detail-empty">Select a step to inspect it.</p>
              )}
            </div>
            <footer className="run-summary">
              <span className="run-summary-item">{traceTree.runId}</span>
              <span className="run-summary-item">
                {doneCount}/{traceTree.nodeIdsInOrder.length} done
              </span>
              {errorCount > 0 && (
                <span className="run-summary-item run-summary-error">
                  {errorCount} error{errorCount !== 1 ? "s" : ""}
                </span>
              )}
              {traceTree.isCompleted && (
                <span className="run-summary-item run-summary-complete">complete</span>
              )}
            </footer>
          </section>
        </main>
      )}
    </div>
  );
}

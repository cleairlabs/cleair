import { useState } from "react";
import { DetailsPanel } from "./components/DetailsPanel";
import { TraceTree } from "./components/TraceTree";
import { useTraceChannels } from "./hooks/useTraceChannels";
import { countNodesByStatus, createEmptyTraceTree } from "./traceTree";
import type { FlowNode, TraceTreeState } from "./types";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";
const EMPTY_RUN_ID = "—";
const EMPTY_RUN_LABEL = "Waiting for trace…";

type ConnectionStatus = "connecting" | "connected" | "offline";

function resolveSelectedNodeId(traceTree: TraceTreeState, selectedNodeId: string | null): string | null {
  if (selectedNodeId !== null && traceTree.nodesById[selectedNodeId] !== undefined) {
    return selectedNodeId;
  }
  return traceTree.nodeIdsInOrder[0] ?? null;
}

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

export default function App() {
  const { panes, activePaneId, setActivePaneId, addPane, setSelectedNodeId } = useTraceChannels(BACKEND_URL);

  const activePane = panes.find((pane) => pane.id === activePaneId) ?? null;
  const traceTree = activePane?.traceTree ?? createEmptyTraceTree(EMPTY_RUN_ID, EMPTY_RUN_LABEL);
  const resolvedSelectedNodeId = resolveSelectedNodeId(traceTree, activePane?.selectedNodeId ?? null);
  const selectedNode: FlowNode | null = resolvedSelectedNodeId ? traceTree.nodesById[resolvedSelectedNodeId] : null;

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

          <DetailsPanel
            selectedNode={selectedNode}
            traceTree={traceTree}
            doneCount={doneCount}
            errorCount={errorCount}
          />
        </main>
      )}
    </div>
  );
}

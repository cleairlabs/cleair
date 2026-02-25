import { useEffect, useState } from "react";
import { TraceTree } from "./components/TraceTree";
import { applyFlowGraphEvent, countNodesByStatus, createEmptyFlowGraph, formatDuration } from "./flowGraph";
import { kindColors } from "./kinds";
import type { FlowGraph, FlowGraphEvent, FlowNode } from "./types";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";
const EMPTY_RUN_ID = "—";
const EMPTY_RUN_LABEL = "Waiting for trace…";

type ConnectionStatus = "connecting" | "connected" | "offline";

function ConnectionIndicator({ status }: { status: ConnectionStatus }) {
  return (
    <span className={`connection-indicator connection-${status}`}>
      {status === "connecting" && "connecting"}
      {status === "connected" && "live"}
      {status === "offline" && "offline"}
    </span>
  );
}

export default function App() {
  const [flowGraph, setFlowGraph] = useState<FlowGraph>(() =>
    createEmptyFlowGraph(EMPTY_RUN_ID, EMPTY_RUN_LABEL)
  );
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");

  useEffect(() => {
    const source = new EventSource(`${BACKEND_URL}/runs/latest/stream`);

    source.onopen = () => setConnectionStatus("connected");

    source.onmessage = (messageEvent) => {
      const event = JSON.parse(messageEvent.data as string) as FlowGraphEvent;
      if (event.type === "run_started") setSelectedNodeId(null);
      setFlowGraph((prev) => applyFlowGraphEvent(prev, event));
    };

    source.onerror = () => setConnectionStatus("offline");
    // Do not call source.close() on error — the browser auto-reconnects.

    return () => source.close();
  }, []);

  // Fall back to the first node when nothing is selected or the selection disappears.
  const resolvedSelectedNodeId =
    selectedNodeId !== null && flowGraph.nodesById[selectedNodeId] !== undefined
      ? selectedNodeId
      : (flowGraph.nodeIdsInOrder[0] ?? null);

  const selectedNode: FlowNode | null = resolvedSelectedNodeId
    ? (flowGraph.nodesById[resolvedSelectedNodeId] ?? null)
    : null;

  const doneCount = countNodesByStatus(flowGraph, "done");
  const errorCount = countNodesByStatus(flowGraph, "error");

  return (
    <main className="app-layout">
      <section className="panel">
        <header className="panel-header">
          <span className="panel-label">Trace</span>
          <span className="panel-header-title">{flowGraph.runLabel}</span>
          <div className="spacer" />
          <ConnectionIndicator status={connectionStatus} />
        </header>
        {flowGraph.nodeIdsInOrder.length === 0 ? (
          <p className="trace-empty">No trace data yet. Run your agent to see a trace here.</p>
        ) : (
          <TraceTree flowGraph={flowGraph} selectedNodeId={resolvedSelectedNodeId} onSelectNode={setSelectedNodeId} />
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
          <span className="run-summary-item">{flowGraph.runId}</span>
          <span className="run-summary-item">{doneCount}/{flowGraph.nodeIdsInOrder.length} done</span>
          {errorCount > 0 && <span className="run-summary-item run-summary-error">{errorCount} error{errorCount !== 1 ? "s" : ""}</span>}
          {flowGraph.isCompleted && <span className="run-summary-item run-summary-complete">complete</span>}
        </footer>
      </section>
    </main>
  );
}

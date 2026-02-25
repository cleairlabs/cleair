import { useEffect, useMemo, useState } from "react";
import { TraceTree, kindColors } from "./components/TraceTree";
import { agentRagRunEvents } from "./data/agentRagRunEvents";
import { applyFlowGraphEvent, countNodesByStatus, createEmptyFlowGraph, formatDuration } from "./flowGraph";
import type { FlowGraph, FlowNode } from "./types";

const DEMO_RUN_ID = "run-retrieval-001";
const DEMO_RUN_LABEL = "RetrievalAgent";
const EVENT_REPLAY_INTERVAL_MS = 350;

export default function App() {
  const [flowGraph, setFlowGraph] = useState<FlowGraph>(() => createEmptyFlowGraph(DEMO_RUN_ID, DEMO_RUN_LABEL));
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [nextEventIndex, setNextEventIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  useEffect(() => {
    if (!isPlaying || nextEventIndex >= agentRagRunEvents.length) return;
    const timer = window.setInterval(() => {
      const event = agentRagRunEvents[nextEventIndex];
      if (!event) { window.clearInterval(timer); return; }
      setFlowGraph((prev) => applyFlowGraphEvent(prev, event));
      setNextEventIndex((prev) => prev + 1);
    }, EVENT_REPLAY_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [isPlaying, nextEventIndex]);

  useEffect(() => {
    if (selectedNodeId && flowGraph.nodesById[selectedNodeId]) return;
    setSelectedNodeId(flowGraph.nodeIdsInOrder[0] ?? null);
  }, [flowGraph, selectedNodeId]);

  function resetRun() {
    setFlowGraph(createEmptyFlowGraph(DEMO_RUN_ID, DEMO_RUN_LABEL));
    setSelectedNodeId(null);
    setNextEventIndex(0);
    setIsPlaying(true);
  }

  const selectedNode: FlowNode | null = selectedNodeId ? (flowGraph.nodesById[selectedNodeId] ?? null) : null;
  const doneCount = useMemo(() => countNodesByStatus(flowGraph, "done"), [flowGraph]);
  const errorCount = useMemo(() => countNodesByStatus(flowGraph, "error"), [flowGraph]);
  const totalCount = flowGraph.nodeIdsInOrder.length;

  return (
    <main className="app-layout">
      <section className="panel">
        <header className="panel-header">
          <span className="panel-label">Trace</span>
          <span className="panel-header-title">{flowGraph.runLabel}</span>
          <div className="spacer" />
          <div className="controls">
            <button type="button" onClick={() => setIsPlaying(true)} disabled={isPlaying}>▶</button>
            <button type="button" onClick={() => setIsPlaying(false)} disabled={!isPlaying}>⏸</button>
            <button type="button" onClick={resetRun}>↺</button>
          </div>
        </header>
        <TraceTree flowGraph={flowGraph} selectedNodeId={selectedNodeId} onSelectNode={setSelectedNodeId} />
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
            </>
          ) : (
            <p className="detail-empty">Select a step to inspect it.</p>
          )}
        </div>
        <footer className="run-summary">
          <span className="run-summary-item">{flowGraph.runId}</span>
          <span className="run-summary-item">{doneCount}/{totalCount} done</span>
          {errorCount > 0 && <span className="run-summary-item run-summary-error">{errorCount} error{errorCount !== 1 ? "s" : ""}</span>}
          {flowGraph.isCompleted && <span className="run-summary-item run-summary-complete">complete</span>}
        </footer>
      </section>
    </main>
  );
}

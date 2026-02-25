import { useEffect, useMemo, useState } from "react";
import { FlowPane } from "./components/FlowPane";
import { agentRagRunEvents } from "./data/agentRagRunEvents";
import { applyFlowGraphEvent, countNodesByStatus, createEmptyFlowGraph } from "./flowGraph";
import type { FlowGraph, FlowNode } from "./types";

const runId = "run-agent-rag-001";
const runLabel = "Agent + RAG";

function createInitialFlowGraph(): FlowGraph {
  return createEmptyFlowGraph(runId, runLabel);
}

export default function App() {
  const [flowGraph, setFlowGraph] = useState<FlowGraph>(createInitialFlowGraph);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [nextEventIndex, setNextEventIndex] = useState<number>(0);
  const [isStreaming, setIsStreaming] = useState<boolean>(true);

  useEffect(() => {
    if (!isStreaming || nextEventIndex >= agentRagRunEvents.length) {
      return;
    }
    const intervalHandle = window.setInterval(() => {
      const nextFlowGraphEvent = agentRagRunEvents[nextEventIndex];
      if (nextFlowGraphEvent === undefined) {
        window.clearInterval(intervalHandle);
        return;
      }
      setFlowGraph((previousFlowGraph) => applyFlowGraphEvent(previousFlowGraph, nextFlowGraphEvent));
      setNextEventIndex((previousEventIndex) => previousEventIndex + 1);
    }, 350);
    return () => window.clearInterval(intervalHandle);
  }, [isStreaming, nextEventIndex]);

  useEffect(() => {
    if (selectedNodeId !== null && flowGraph.nodesById[selectedNodeId] !== undefined) {
      return;
    }
    setSelectedNodeId(flowGraph.nodeIdsInRenderOrder[0] ?? null);
  }, [flowGraph, selectedNodeId]);

  const selectedNode: FlowNode | null = selectedNodeId === null ? null : flowGraph.nodesById[selectedNodeId] ?? null;
  const doneCount = useMemo(() => countNodesByStatus(flowGraph, "done"), [flowGraph]);
  const warningCount = useMemo(() => countNodesByStatus(flowGraph, "warn"), [flowGraph]);
  const errorCount = useMemo(() => countNodesByStatus(flowGraph, "error"), [flowGraph]);

  function resetRun(): void {
    setFlowGraph(createInitialFlowGraph());
    setSelectedNodeId(null);
    setNextEventIndex(0);
    setIsStreaming(true);
  }

  return (
    <main className="app-layout">
      <FlowPane flowGraph={flowGraph} selectedNodeId={selectedNodeId} onSelectNode={setSelectedNodeId} />
      <section className="panel">
        <header className="panel-header">
          <h2 className="panel-title">Details</h2>
        </header>
        <div className="details">
          <div className="details-controls">
            <button type="button" onClick={() => setIsStreaming(true)} disabled={isStreaming}>
              Start
            </button>
            <button type="button" onClick={() => setIsStreaming(false)} disabled={!isStreaming}>
              Pause
            </button>
            <button type="button" onClick={resetRun}>
              Reset
            </button>
          </div>
          <div className="detail-card">
            <h3>Run</h3>
            <p>{flowGraph.runLabel}</p>
            <p className="muted">{flowGraph.runId}</p>
          </div>
          <div className="detail-card">
            <h3>Status</h3>
            <p>
              {doneCount}/{flowGraph.nodeIdsInRenderOrder.length} done
            </p>
            <p className="muted">warn={warningCount}, error={errorCount}, complete={String(flowGraph.isCompleted)}</p>
          </div>
          <div className="detail-card">
            <h3>What</h3>
            <p>{selectedNode?.whatDescription ?? "Select a step"}</p>
          </div>
          <div className="detail-card">
            <h3>Why</h3>
            <p>{selectedNode?.whyDescription ?? "Select a step"}</p>
          </div>
        </div>
      </section>
    </main>
  );
}

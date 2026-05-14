import { typeColors } from "../nodeTypes";
import { formatDuration } from "../traceTree";
import type { FlowNode, TraceTreeState } from "../types";

type DetailsPanelProps = {
  selectedNode: FlowNode | null;
  traceTree: TraceTreeState;
  doneCount: number;
  errorCount: number;
};

export function DetailsPanel({ selectedNode, traceTree, doneCount, errorCount }: DetailsPanelProps) {
  return (
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
                <span className="detail-type-dot" style={{ background: typeColors[selectedNode.type] }} />
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
        {traceTree.isCompleted && <span className="run-summary-item run-summary-complete">complete</span>}
      </footer>
    </section>
  );
}

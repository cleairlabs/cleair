import type { FlowGraph, FlowNode } from "../types";

type FlowPaneProps = {
  flowGraph: FlowGraph;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
};

type EdgeLine = {
  startX: number;
  startY: number;
  length: number;
  rotationInDegrees: number;
};

function calculateEdgeLine(fromNode: FlowNode, toNode: FlowNode): EdgeLine {
  const fromCenterX = fromNode.x + 100;
  const fromCenterY = fromNode.y + 28;
  const toCenterX = toNode.x + 100;
  const toCenterY = toNode.y + 28;
  const deltaX = toCenterX - fromCenterX;
  const deltaY = toCenterY - fromCenterY;
  return {
    startX: fromCenterX,
    startY: fromCenterY,
    length: Math.sqrt(deltaX * deltaX + deltaY * deltaY),
    rotationInDegrees: (Math.atan2(deltaY, deltaX) * 180) / Math.PI
  };
}

function statusClassName(status: FlowNode["status"]): string {
  return `flow-node-${status}`;
}

function kindLabel(kind: FlowNode["kind"]): string {
  if (kind === "tool") return "Tool";
  if (kind === "rag") return "RAG";
  return "Agent";
}

export function FlowPane({ flowGraph, selectedNodeId, onSelectNode }: FlowPaneProps) {
  return (
    <section className="panel">
      <header className="panel-header">
        <h2 className="panel-title">Flow</h2>
      </header>
      <div className="flow-canvas">
        {flowGraph.flowEdges.map((flowEdge) => {
          const fromNode = flowGraph.nodesById[flowEdge.fromNodeId];
          const toNode = flowGraph.nodesById[flowEdge.toNodeId];
          if (fromNode === undefined || toNode === undefined) return null;
          const edgeLine = calculateEdgeLine(fromNode, toNode);
          return (
            <div
              key={flowEdge.id}
              className="flow-edge"
              style={{
                left: `${edgeLine.startX}px`,
                top: `${edgeLine.startY}px`,
                width: `${edgeLine.length}px`,
                transform: `rotate(${edgeLine.rotationInDegrees}deg)`
              }}
            />
          );
        })}
        {flowGraph.nodeIdsInRenderOrder.map((nodeId) => {
          const flowNode = flowGraph.nodesById[nodeId];
          if (flowNode === undefined) return null;
          const isSelected = selectedNodeId === flowNode.id;
          return (
            <button
              key={flowNode.id}
              type="button"
              className={`flow-node ${statusClassName(flowNode.status)} ${isSelected ? "flow-node-selected" : ""}`}
              style={{ left: `${flowNode.x}px`, top: `${flowNode.y}px` }}
              onClick={() => onSelectNode(flowNode.id)}
            >
              <div className="flow-node-header">
                <span>{flowNode.label}</span>
                <span className="flow-node-kind-chip">{kindLabel(flowNode.kind)}</span>
              </div>
              <div className="flow-node-subtitle">{flowNode.subtitle}</div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

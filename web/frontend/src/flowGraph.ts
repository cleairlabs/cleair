import type { FlowEdge, FlowGraph, FlowGraphEvent, FlowNode, FlowNodeStatus } from "./types";

function createFlowEdgeId(fromNodeId: string, toNodeId: string): string {
  return `${fromNodeId}->${toNodeId}`;
}

function createNodeWithIdleStatus(node: Omit<FlowNode, "status">): FlowNode {
  return { ...node, status: "idle" };
}

export function createEmptyFlowGraph(runId: string, runLabel: string): FlowGraph {
  return {
    runId,
    runLabel,
    nodesById: {},
    nodeIdsInRenderOrder: [],
    flowEdges: [],
    isCompleted: false
  };
}

export function applyFlowGraphEvent(flowGraph: FlowGraph, flowGraphEvent: FlowGraphEvent): FlowGraph {
  if (flowGraphEvent.type === "node_added") {
    const nodeWithIdleStatus = createNodeWithIdleStatus(flowGraphEvent.node);
    if (flowGraph.nodesById[nodeWithIdleStatus.id] !== undefined) {
      return flowGraph;
    }
    return {
      ...flowGraph,
      nodesById: { ...flowGraph.nodesById, [nodeWithIdleStatus.id]: nodeWithIdleStatus },
      nodeIdsInRenderOrder: [...flowGraph.nodeIdsInRenderOrder, nodeWithIdleStatus.id]
    };
  }

  if (flowGraphEvent.type === "edge_added") {
    const flowEdgeId = createFlowEdgeId(flowGraphEvent.edge.fromNodeId, flowGraphEvent.edge.toNodeId);
    if (flowGraph.flowEdges.some((flowEdge) => flowEdge.id === flowEdgeId)) {
      return flowGraph;
    }
    const flowEdgeToAdd: FlowEdge = { id: flowEdgeId, ...flowGraphEvent.edge };
    return { ...flowGraph, flowEdges: [...flowGraph.flowEdges, flowEdgeToAdd] };
  }

  if (flowGraphEvent.type === "node_status_changed") {
    const existingFlowNode = flowGraph.nodesById[flowGraphEvent.nodeId];
    if (existingFlowNode === undefined || existingFlowNode.status === flowGraphEvent.status) {
      return flowGraph;
    }
    return {
      ...flowGraph,
      nodesById: {
        ...flowGraph.nodesById,
        [flowGraphEvent.nodeId]: { ...existingFlowNode, status: flowGraphEvent.status }
      }
    };
  }

  return { ...flowGraph, isCompleted: true };
}

export function countNodesByStatus(flowGraph: FlowGraph, status: FlowNodeStatus): number {
  return flowGraph.nodeIdsInRenderOrder.filter((nodeId) => flowGraph.nodesById[nodeId]?.status === status).length;
}

import type { FlowGraph, FlowGraphEvent, FlowNode, FlowNodeStatus } from "./types";

export function createEmptyFlowGraph(runId: string, runLabel: string): FlowGraph {
  return { runId, runLabel, nodesById: {}, nodeIdsInOrder: [], isCompleted: false };
}

export function applyFlowGraphEvent(graph: FlowGraph, event: FlowGraphEvent): FlowGraph {
  switch (event.type) {
    case "node_added": {
      if (graph.nodesById[event.node.id]) return graph;
      const newNode: FlowNode = { ...event.node, status: "idle", durationMs: null };
      return {
        ...graph,
        nodesById: { ...graph.nodesById, [newNode.id]: newNode },
        nodeIdsInOrder: [...graph.nodeIdsInOrder, newNode.id],
      };
    }
    case "node_status_changed": {
      const node = graph.nodesById[event.nodeId];
      if (!node || node.status === event.status) return graph;
      return {
        ...graph,
        nodesById: { ...graph.nodesById, [event.nodeId]: { ...node, status: event.status } },
      };
    }
    case "node_finished": {
      const node = graph.nodesById[event.nodeId];
      if (!node) return graph;
      return {
        ...graph,
        nodesById: { ...graph.nodesById, [event.nodeId]: { ...node, durationMs: event.durationMs } },
      };
    }
    case "run_completed":
      return { ...graph, isCompleted: true };
  }
}

export function countNodesByStatus(graph: FlowGraph, status: FlowNodeStatus): number {
  return graph.nodeIdsInOrder.filter((id) => graph.nodesById[id]?.status === status).length;
}

export function formatDuration(ms: number): string {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(2)}s`;
}

import type { TraceTreeState, TraceTreeEvent, FlowNode, FlowNodeStatus } from "./types";

export function createEmptyTraceTree(runId: string, runLabel: string): TraceTreeState {
  return { runId, runLabel, nodesById: {}, nodeIdsInOrder: [], isCompleted: false };
}

export function applyTraceTreeEvent(graph: TraceTreeState, event: TraceTreeEvent): TraceTreeState {
  switch (event.type) {
    case "run_started":
      return createEmptyTraceTree(event.runId, event.runLabel);
    case "node_added": {
      const existingNode = graph.nodesById[event.node.id];
      if (existingNode) {
        if (existingNode.input !== null || event.node.input === undefined) return graph;
        return {
          ...graph,
          nodesById: { ...graph.nodesById, [event.node.id]: { ...existingNode, input: event.node.input } },
        };
      }
      const newNode: FlowNode = { ...event.node, input: event.node.input ?? null, status: "idle", durationMs: null, output: null };
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
        nodesById: { ...graph.nodesById, [event.nodeId]: { ...node, durationMs: event.durationMs, output: event.output ?? null } },
      };
    }
    case "run_completed":
      return { ...graph, isCompleted: true };
  }
}

export function countNodesByStatus(graph: TraceTreeState, status: FlowNodeStatus): number {
  return graph.nodeIdsInOrder.filter((id) => graph.nodesById[id]?.status === status).length;
}

export function formatDuration(ms: number): string {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(2)}s`;
}

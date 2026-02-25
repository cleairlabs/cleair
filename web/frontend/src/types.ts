export type FlowNodeStatus = "idle" | "running" | "done" | "warn" | "error";

export type FlowNodeKind = "agent" | "rag" | "tool";

export type FlowNode = {
  id: string;
  label: string;
  subtitle: string;
  x: number;
  y: number;
  kind: FlowNodeKind;
  status: FlowNodeStatus;
  whatDescription: string;
  whyDescription: string;
};

export type FlowEdge = {
  id: string;
  fromNodeId: string;
  toNodeId: string;
};

export type FlowGraph = {
  runId: string;
  runLabel: string;
  nodesById: Record<string, FlowNode>;
  nodeIdsInRenderOrder: string[];
  flowEdges: FlowEdge[];
  isCompleted: boolean;
};

export type FlowGraphEvent =
  | {
      type: "node_added";
      node: Omit<FlowNode, "status">;
    }
  | {
      type: "edge_added";
      edge: Omit<FlowEdge, "id">;
    }
  | {
      type: "node_status_changed";
      nodeId: string;
      status: FlowNodeStatus;
    }
  | {
      type: "run_completed";
    };

export type FlowNodeStatus = "idle" | "running" | "done" | "warn" | "error";
export type FlowNodeKind = "agent" | "rag" | "tool";

export type FlowNode = {
  id: string;
  parentId: string | null;
  label: string;
  subtitle: string;
  kind: FlowNodeKind;
  status: FlowNodeStatus;
  durationMs: number | null;
  whatDescription: string;
  whyDescription: string;
};

export type FlowGraph = {
  runId: string;
  runLabel: string;
  nodesById: Record<string, FlowNode>;
  nodeIdsInOrder: string[];
  isCompleted: boolean;
};

export type FlowGraphEvent =
  | { type: "run_started"; runId: string; runLabel: string }
  | { type: "node_added"; node: Omit<FlowNode, "status" | "durationMs"> }
  | { type: "node_status_changed"; nodeId: string; status: FlowNodeStatus }
  | { type: "node_finished"; nodeId: string; durationMs: number }
  | { type: "run_completed" };

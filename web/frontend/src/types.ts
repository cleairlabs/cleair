export type FlowNodeStatus = "idle" | "running" | "done" | "warn" | "error";
export type FlowNodeKind = "trace" | "agent" | "search" | "tool" | "human";

export type FlowNode = {
  id: string;
  parentId: string | null;
  label: string;
  subtitle: string;
  kind: FlowNodeKind;
  status: FlowNodeStatus;
  durationMs: number | null;
  output: string | null;
  whatDescription: string;
  whyDescription: string;
};

export type TraceTreeState = {
  runId: string;
  runLabel: string;
  nodesById: Record<string, FlowNode>;
  nodeIdsInOrder: string[];
  isCompleted: boolean;
};

export type TraceTreeEvent =
  | { type: "run_started"; runId: string; runLabel: string }
  | { type: "node_added"; node: Omit<FlowNode, "status" | "durationMs" | "output"> }
  | { type: "node_status_changed"; nodeId: string; status: FlowNodeStatus }
  | { type: "node_finished"; nodeId: string; durationMs: number; output?: string }
  | { type: "run_completed" };

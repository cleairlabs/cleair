export type FlowNodeStatus = "idle" | "running" | "done" | "warn" | "error";
export type FlowNodeType = "trace" | "agent" | "intelligence" | "search" | "tool" | "human";

export type FlowNode = {
  id: string;
  parentId: string | null;
  label: string;
  subtitle: string;
  type: FlowNodeType;
  status: FlowNodeStatus;
  durationMs: number | null;
  input: string | null;
  output: string | null;
};

export type TraceTreeState = {
  runId: string;
  runLabel: string;
  nodesById: Record<string, FlowNode>;
  nodeIdsInOrder: string[];
  isCompleted: boolean;
};

export type TraceTreeEvent =
  | { type: "run_started"; runId: string; runLabel: string; metadata?: Record<string, string | number | boolean> }
  | { type: "node_added"; node: Omit<FlowNode, "status" | "durationMs" | "input" | "output"> & { input?: string } }
  | { type: "node_status_changed"; nodeId: string; status: FlowNodeStatus }
  | { type: "node_finished"; nodeId: string; durationMs: number; output?: string }
  | { type: "run_completed" };

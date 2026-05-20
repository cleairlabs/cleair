import type { TraceTreeState } from "../types";

export type TraceViewName = "tree" | "graph";

export type TraceViewProps = {
  traceTree: TraceTreeState;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
};

import type { TraceTreeState } from "../types";

export type TraceViewName = "tree";

export type TraceViewProps = {
  traceTree: TraceTreeState;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
};

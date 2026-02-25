import type { FlowNodeKind } from "./types";

/** Visual color for each node kind. Used in badges and selection accents. */
export const kindColors: Record<FlowNodeKind, string> = {
  agent: "#7c3aed",
  rag: "#2563eb",
  tool: "#c2410c",
};

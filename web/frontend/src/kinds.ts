import type { FlowNodeKind } from "./types";

/** Visual color for each node kind. Used in badges and selection accents. */
export const kindColors: Record<FlowNodeKind, string> = {
  trace: "#0891b2",
  agent: "#7c3aed",
  search: "#2563eb",
  tool: "#c2410c",
};

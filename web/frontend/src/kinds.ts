import type { FlowNodeKind } from "./types";

/** Visual color for each node kind. Used in badges and selection accents. */
export const kindColors: Record<FlowNodeKind, string> = {
  trace: "#ffffff",
  agent: "#2563eb",
  search: "#c2410c",
  tool: "#c2410c",
  human: "#16a34a",
};

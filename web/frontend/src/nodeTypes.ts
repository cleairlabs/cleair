import type { FlowNodeType } from "./types";

/** Visual color for each node type. Used in badges and selection accents. */
export const typeColors: Record<FlowNodeType, string> = {
  trace:         "var(--type-trace)",
  agent:         "var(--type-agent)",
  intelligence:  "var(--type-tool)",
  search:        "var(--type-tool)",
  tool:          "var(--type-tool)",
  human:         "var(--type-human)",
};

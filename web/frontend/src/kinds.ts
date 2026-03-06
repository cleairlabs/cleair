import type { FlowNodeKind } from "./types";

/** Visual color for each node kind. Used in badges and selection accents. */
export const kindColors: Record<FlowNodeKind, string> = {
  trace:         "var(--kind-trace)",
  agent:         "var(--kind-agent)",
  intelligence:  "var(--kind-tool)",
  search:        "var(--kind-tool)",
  tool:          "var(--kind-tool)",
  human:         "var(--kind-human)",
};

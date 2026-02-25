import type { FlowGraphEvent } from "../types";

export const agentRagRunEvents: FlowGraphEvent[] = [
  { type: "node_added", node: { id: "root", parentId: null, label: "RetrievalAgent", subtitle: "main pipeline", kind: "agent", whatDescription: "Top-level agent run.", whyDescription: "Entry point for the user request." } },
  { type: "node_added", node: { id: "plan", parentId: "root", label: "plan", subtitle: "reason about approach", kind: "agent", whatDescription: "Agent decides retrieval is needed.", whyDescription: "The question requires factual grounding." } },
  { type: "node_added", node: { id: "retrieve", parentId: "root", label: "retrieve", subtitle: "fetch context", kind: "search", whatDescription: "Retrieval pipeline runs.", whyDescription: "Grounds the answer in evidence." } },
  { type: "node_added", node: { id: "vector_search", parentId: "retrieve", label: "vector_search", subtitle: "find candidates", kind: "tool", whatDescription: "Queries the vector store for relevant documents.", whyDescription: "Broadens the candidate pool before reranking." } },
  { type: "node_added", node: { id: "rerank", parentId: "retrieve", label: "rerank", subtitle: "score by relevance", kind: "tool", whatDescription: "Cross-encoder scores each candidate document.", whyDescription: "Surfaces the highest-signal context first." } },
  { type: "node_added", node: { id: "compose", parentId: "root", label: "compose", subtitle: "synthesize answer", kind: "agent", whatDescription: "LLM writes the final answer using retrieved context.", whyDescription: "Combines retrieved evidence with chain-of-thought reasoning." } },

  { type: "node_status_changed", nodeId: "root", status: "running" },
  { type: "node_status_changed", nodeId: "plan", status: "running" },
  { type: "node_status_changed", nodeId: "plan", status: "done" },
  { type: "node_finished", nodeId: "plan", durationMs: 120 },

  { type: "node_status_changed", nodeId: "retrieve", status: "running" },
  { type: "node_status_changed", nodeId: "vector_search", status: "running" },
  { type: "node_status_changed", nodeId: "vector_search", status: "done" },
  { type: "node_finished", nodeId: "vector_search", durationMs: 810 },

  { type: "node_status_changed", nodeId: "rerank", status: "running" },
  { type: "node_status_changed", nodeId: "rerank", status: "done" },
  { type: "node_finished", nodeId: "rerank", durationMs: 290 },

  { type: "node_status_changed", nodeId: "retrieve", status: "done" },
  { type: "node_finished", nodeId: "retrieve", durationMs: 1100 },

  { type: "node_status_changed", nodeId: "compose", status: "running" },
  { type: "node_status_changed", nodeId: "compose", status: "done" },
  { type: "node_finished", nodeId: "compose", durationMs: 1420 },

  { type: "node_status_changed", nodeId: "root", status: "done" },
  { type: "node_finished", nodeId: "root", durationMs: 2830 },
  { type: "run_completed" },
];

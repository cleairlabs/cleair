import type { FlowGraphEvent } from "../types";

export const agentRagRunEvents: FlowGraphEvent[] = [
  {
    type: "node_added",
    node: {
      id: "agent.start",
      label: "Start",
      subtitle: "User asks question",
      x: 80,
      y: 50,
      kind: "agent",
      whatDescription: "The run starts.",
      whyDescription: "A new request enters the pipeline."
    }
  },
  {
    type: "node_added",
    node: {
      id: "agent.plan",
      label: "Plan",
      subtitle: "Need retrieval",
      x: 80,
      y: 180,
      kind: "agent",
      whatDescription: "The agent decides to use retrieval.",
      whyDescription: "The question requires factual context."
    }
  },
  { type: "edge_added", edge: { fromNodeId: "agent.start", toNodeId: "agent.plan" } },
  {
    type: "node_added",
    node: {
      id: "rag.retrieve",
      label: "RAG",
      subtitle: "Enter retrieval lane",
      x: 370,
      y: 180,
      kind: "rag",
      whatDescription: "The flow moves into retrieval.",
      whyDescription: "Grounding improves answer quality."
    }
  },
  { type: "edge_added", edge: { fromNodeId: "agent.plan", toNodeId: "rag.retrieve" } },
  {
    type: "node_added",
    node: {
      id: "tool.search",
      label: "Tool: Search",
      subtitle: "Find documents",
      x: 370,
      y: 310,
      kind: "tool",
      whatDescription: "Search finds candidate docs.",
      whyDescription: "The answer needs relevant evidence."
    }
  },
  { type: "edge_added", edge: { fromNodeId: "rag.retrieve", toNodeId: "tool.search" } },
  {
    type: "node_added",
    node: {
      id: "tool.rerank",
      label: "Tool: Re-rank",
      subtitle: "Sort by relevance",
      x: 370,
      y: 440,
      kind: "tool",
      whatDescription: "The best evidence is ranked to the top.",
      whyDescription: "The model should use high-signal context first."
    }
  },
  { type: "edge_added", edge: { fromNodeId: "tool.search", toNodeId: "tool.rerank" } },
  {
    type: "node_added",
    node: {
      id: "agent.answer",
      label: "Compose",
      subtitle: "Write answer",
      x: 80,
      y: 440,
      kind: "agent",
      whatDescription: "The agent writes the answer.",
      whyDescription: "It combines reasoning with retrieved context."
    }
  },
  { type: "edge_added", edge: { fromNodeId: "tool.rerank", toNodeId: "agent.answer" } },
  {
    type: "node_added",
    node: {
      id: "agent.finish",
      label: "Finish",
      subtitle: "Return response",
      x: 80,
      y: 570,
      kind: "agent",
      whatDescription: "The run returns output to the user.",
      whyDescription: "The workflow ends after response generation."
    }
  },
  { type: "edge_added", edge: { fromNodeId: "agent.answer", toNodeId: "agent.finish" } },
  { type: "node_status_changed", nodeId: "agent.start", status: "running" },
  { type: "node_status_changed", nodeId: "agent.start", status: "done" },
  { type: "node_status_changed", nodeId: "agent.plan", status: "running" },
  { type: "node_status_changed", nodeId: "agent.plan", status: "done" },
  { type: "node_status_changed", nodeId: "rag.retrieve", status: "running" },
  { type: "node_status_changed", nodeId: "rag.retrieve", status: "done" },
  { type: "node_status_changed", nodeId: "tool.search", status: "running" },
  { type: "node_status_changed", nodeId: "tool.search", status: "done" },
  { type: "node_status_changed", nodeId: "tool.rerank", status: "running" },
  { type: "node_status_changed", nodeId: "tool.rerank", status: "done" },
  { type: "node_status_changed", nodeId: "agent.answer", status: "running" },
  { type: "node_status_changed", nodeId: "agent.answer", status: "done" },
  { type: "node_status_changed", nodeId: "agent.finish", status: "running" },
  { type: "node_status_changed", nodeId: "agent.finish", status: "done" },
  { type: "run_completed" }
];

import { useState } from "react";
import type { AgentTrace } from "../hooks/useAgents";

type AgentListProps = {
  agents: AgentTrace[];
  selectedRunId: string | null;
  onSelectAgent: (runId: string) => void;
  onDeleteAgent: (runId: string) => void;
};

export function AgentList({ agents, selectedRunId, onSelectAgent, onDeleteAgent }: AgentListProps) {
  const [pendingDeleteRunId, setPendingDeleteRunId] = useState<string | null>(null);

  if (agents.length === 0) {
    return <p className="agent-list-empty">Run your agent to see it here.</p>;
  }

  return (
    <div className="agent-list">
      {agents.map((agent) => (
        <div key={agent.runId} className={`agent-list-item${agent.runId === selectedRunId ? " agent-list-item-selected" : ""}`}>
          <button className="agent-list-select" onClick={() => onSelectAgent(agent.runId)}>
            <span className="agent-list-copy">
              <span className="agent-list-name">{agent.displayName}</span>
              {agent.batchId !== null && <span className="agent-list-subtitle">{agent.batchId}</span>}
            </span>
            <span className="agent-list-meta">{agent.traceTree.isCompleted ? "complete" : "running"}</span>
          </button>
          {pendingDeleteRunId === agent.runId ? (
            <div className="agent-list-confirm">
              <span className="agent-list-confirm-copy">Delete?</span>
              <button
                className="agent-list-confirm-button"
                onClick={() => {
                  setPendingDeleteRunId(null);
                  void onDeleteAgent(agent.runId);
                }}
              >
                Yes
              </button>
              <button className="agent-list-confirm-button" onClick={() => setPendingDeleteRunId(null)}>
                No
              </button>
            </div>
          ) : (
            <button
              className="agent-list-delete"
              onClick={() => setPendingDeleteRunId(agent.runId)}
              title="Delete run"
            >
              ×
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

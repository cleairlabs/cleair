import type { AgentTrace } from "../hooks/useAgents";

type AgentListProps = {
  agents: AgentTrace[];
  selectedAgentName: string | null;
  onSelectAgent: (serviceName: string) => void;
};

export function AgentList({ agents, selectedAgentName, onSelectAgent }: AgentListProps) {
  if (agents.length === 0) {
    return <p className="agent-list-empty">Run your agent to see it here.</p>;
  }

  return (
    <div className="agent-list">
      {agents.map((agent) => (
        <button
          key={agent.serviceName}
          className={`agent-list-item${agent.serviceName === selectedAgentName ? " agent-list-item-selected" : ""}`}
          onClick={() => onSelectAgent(agent.serviceName)}
        >
          <span className="agent-list-name">{agent.serviceName}</span>
          <span className="agent-list-meta">{agent.traceTree.isCompleted ? "complete" : "running"}</span>
        </button>
      ))}
    </div>
  );
}

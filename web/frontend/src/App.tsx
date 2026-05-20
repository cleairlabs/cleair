import { useEffect, useState } from "react";
import { AccessGate } from "./components/AccessGate";
import { AgentList } from "./components/AgentList";
import { DetailsPanel } from "./components/DetailsPanel";
import { TraceTree } from "./components/TraceTree";
import { useAccessGate } from "./hooks/useAccessGate";
import { useAgents } from "./hooks/useAgents";
import { countNodesByStatus, createEmptyTraceTree } from "./traceTree";
import type { FlowNode, TraceTreeState } from "./types";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";
const EMPTY_RUN_ID = "—";
const EMPTY_RUN_LABEL = "Waiting for trace…";

type ConnectionStatus = "connecting" | "connected" | "offline";

function useTheme() {
  const [dark, setDark] = useState(() => window.matchMedia("(prefers-color-scheme: dark)").matches);

  useEffect(() => {
    const systemDarkModeQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const onSystemThemeChange = (event: MediaQueryListEvent) => setDark(event.matches);
    systemDarkModeQuery.addEventListener("change", onSystemThemeChange);
    return () => systemDarkModeQuery.removeEventListener("change", onSystemThemeChange);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }, [dark]);

  return { dark, toggle: () => setDark((currentDark) => !currentDark) };
}

function resolveSelectedNodeId(traceTree: TraceTreeState, selectedNodeId: string | null): string | null {
  if (selectedNodeId !== null && traceTree.nodesById[selectedNodeId] !== undefined) {
    return selectedNodeId;
  }
  return traceTree.nodeIdsInOrder[0] ?? null;
}

function ConnectionIndicator({ status }: { status: ConnectionStatus }) {
  return (
    <span className={`connection-indicator connection-${status}`}>
      {status === "connecting" && "connecting"}
      {status === "connected" && "live"}
      {status === "offline" && "offline"}
    </span>
  );
}

function ApiKeyBadge({ apiKey }: { apiKey: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button className="api-key-badge" onClick={copy} title={apiKey}>
      <span className="api-key-label">KEY</span>
      <span className="api-key-value">{apiKey.slice(0, 8)}…</span>
      <span className="api-key-copy">{copied ? "copied" : "copy"}</span>
    </button>
  );
}

export default function App() {
  const [batchFilter, setBatchFilter] = useState("");
  const { dark, toggle: toggleTheme } = useTheme();
  const { accessState, accessCode, setAccessCode, errorMessage, isSubmitting, refreshAccessState, submitAccessCode } =
    useAccessGate(BACKEND_URL);
  const { apiKey, agents, selectedRunId, setSelectedRunId, connectionStatus, setSelectedNodeId, deleteRun } =
    useAgents(BACKEND_URL, accessState === "open", refreshAccessState);

  const batchIds = [...new Set(agents.flatMap((agent) => agent.batchId === null ? [] : [agent.batchId]))];
  const filteredAgents = batchFilter === "" ? agents : agents.filter((agent) => agent.batchId === batchFilter);
  const selectedAgent = filteredAgents.find((agent) => agent.runId === selectedRunId) ?? filteredAgents[0] ?? null;
  const traceTree = selectedAgent?.traceTree ?? createEmptyTraceTree(EMPTY_RUN_ID, EMPTY_RUN_LABEL);
  const resolvedSelectedNodeId = resolveSelectedNodeId(traceTree, selectedAgent?.selectedNodeId ?? null);
  const selectedNode: FlowNode | null = resolvedSelectedNodeId ? traceTree.nodesById[resolvedSelectedNodeId] : null;
  const doneCount = countNodesByStatus(traceTree, "done");
  const errorCount = countNodesByStatus(traceTree, "error");

  useEffect(() => {
    if (selectedAgent !== null && selectedAgent.runId !== selectedRunId) {
      setSelectedRunId(selectedAgent.runId);
    }
  }, [selectedAgent, selectedRunId, setSelectedRunId]);

  return (
    <div className="app-root">
      {accessState !== "open" && (
        <AccessGate
          accessCode={accessCode}
          errorMessage={accessState === "checking" ? null : errorMessage}
          isSubmitting={isSubmitting || accessState === "checking"}
          onAccessCodeChange={setAccessCode}
          onSubmit={submitAccessCode}
        />
      )}
      <header className="top-bar">
        <div className="top-bar-copy">
          <span className="panel-label">Trace</span>
          <span className="top-bar-title">{selectedAgent?.displayName ?? EMPTY_RUN_LABEL}</span>
        </div>
        <div className="top-bar-actions">
          {apiKey !== null && <ApiKeyBadge apiKey={apiKey} />}
          <ConnectionIndicator status={connectionStatus} />
          <button className="theme-toggle" onClick={toggleTheme} title="Toggle theme">
            {dark ? "☀" : "☽"}
          </button>
        </div>
      </header>
      <main className="app-layout">
        <section className="panel agent-panel">
          <header className="panel-header">
            <span className="panel-label">Agents</span>
            <select className="batch-filter" value={batchFilter} onChange={(event) => setBatchFilter(event.target.value)}>
              <option value="">All batches</option>
              {batchIds.map((batchId) => (
                <option key={batchId} value={batchId}>
                  {batchId}
                </option>
              ))}
            </select>
          </header>
          <AgentList
            agents={filteredAgents}
            selectedRunId={selectedAgent?.runId ?? null}
            onSelectAgent={setSelectedRunId}
            onDeleteAgent={(runId) => void deleteRun(runId)}
          />
        </section>

        <section className="panel trace-panel">
          <header className="panel-header">
            <span className="panel-label">Trace</span>
            <span className="panel-header-title">{traceTree.runLabel}</span>
          </header>
          {traceTree.nodeIdsInOrder.length === 0 ? (
            <p className="trace-empty">No trace data yet. Run your agent to see a trace here.</p>
          ) : (
            <TraceTree traceTree={traceTree} selectedNodeId={resolvedSelectedNodeId} onSelectNode={setSelectedNodeId} />
          )}
        </section>

        <DetailsPanel selectedNode={selectedNode} traceTree={traceTree} doneCount={doneCount} errorCount={errorCount} />
      </main>
    </div>
  );
}

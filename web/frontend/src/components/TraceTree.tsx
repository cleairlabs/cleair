import type { CSSProperties, ReactElement } from "react";
import { kindColors } from "../kinds";
import { formatDuration } from "../flowGraph";
import type { FlowGraph, FlowNode, FlowNodeKind, FlowNodeStatus } from "../types";

type TraceTreeProps = {
  flowGraph: FlowGraph;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
};

/** A node ready for rendering, annotated with tree structure metadata. */
type TreeEntry = {
  node: FlowNode;
  depth: number;
  isLastChild: boolean;
  /**
   * ancestorContinues[i] = does the ancestor at depth i have more siblings below it?
   * Used in rendering: column j (pass-through) draws │ when ancestorContinues[j+1] is true.
   */
  ancestorContinues: boolean[];
};

function buildChildrenMap(graph: FlowGraph): Record<string, string[]> {
  const childrenByParentId: Record<string, string[]> = {};
  for (const nodeId of graph.nodeIdsInOrder) {
    const node = graph.nodesById[nodeId];
    if (!node) continue;
    const parentKey = node.parentId ?? "";
    childrenByParentId[parentKey] ??= [];
    childrenByParentId[parentKey].push(nodeId);
  }
  return childrenByParentId;
}

/** Depth-first traversal producing a flat list of nodes with tree metadata. */
function buildTreeEntries(graph: FlowGraph): TreeEntry[] {
  const childrenByParentId = buildChildrenMap(graph);
  const rootNodeIds = childrenByParentId[""] ?? [];
  const entries: TreeEntry[] = [];

  function visit(nodeId: string, depth: number, ancestorContinues: boolean[]) {
    const node = graph.nodesById[nodeId];
    if (!node) return;
    const siblings = node.parentId ? (childrenByParentId[node.parentId] ?? []) : rootNodeIds;
    const isLastChild = siblings[siblings.length - 1] === nodeId;
    entries.push({ node, depth, isLastChild, ancestorContinues });
    for (const childId of childrenByParentId[nodeId] ?? []) {
      visit(childId, depth + 1, [...ancestorContinues, !isLastChild]);
    }
  }

  for (const rootId of rootNodeIds) {
    visit(rootId, 0, []);
  }
  return entries;
}

/** Sparkle — represents intelligence and orchestration. */
function AgentIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="white">
      <path d="M5 0 L6.2 3.8 L10 5 L6.2 6.2 L5 10 L3.8 6.2 L0 5 L3.8 3.8 Z" />
    </svg>
  );
}

/** Magnifying glass — represents search and retrieval. */
function SearchIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round">
      <circle cx="4.2" cy="4.2" r="2.8" />
      <line x1="6.2" y1="6.2" x2="9.5" y2="9.5" />
    </svg>
  );
}

/** Terminal prompt — represents function/tool execution. */
function ToolIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1,2.5 4.5,5 1,7.5" />
      <line x1="5.5" y1="7.5" x2="9" y2="7.5" />
    </svg>
  );
}

const kindIcons: Record<FlowNodeKind, () => ReactElement> = {
  agent: AgentIcon,
  search: SearchIcon,
  tool: ToolIcon,
};

function KindBadge({ kind }: { kind: FlowNodeKind }) {
  const Icon = kindIcons[kind];
  return (
    <span className="kind-badge" style={{ background: kindColors[kind] }}>
      <Icon />
    </span>
  );
}

function StatusIcon({ status }: { status: FlowNodeStatus }) {
  if (status === "running") return <span className="status-icon status-running">◌</span>;
  if (status === "done") return <span className="status-icon status-done">✓</span>;
  if (status === "warn") return <span className="status-icon status-warn">!</span>;
  if (status === "error") return <span className="status-icon status-error">✕</span>;
  return <span className="status-icon" />;
}

function TreeConnectors({ depth, isLastChild, ancestorContinues }: Omit<TreeEntry, "node">) {
  return (
    <div className="tree-connectors">
      {Array.from({ length: depth }, (_, columnIndex) => {
        const isImmediateConnector = columnIndex === depth - 1;
        if (isImmediateConnector) {
          return <div key={columnIndex} className={isLastChild ? "connector-last" : "connector-mid"} />;
        }
        const ancestorAtThisColumnContinues = ancestorContinues[columnIndex + 1] ?? false;
        return <div key={columnIndex} className={ancestorAtThisColumnContinues ? "connector-pass" : "connector-empty"} />;
      })}
    </div>
  );
}

function TraceRow({ entry, isSelected, onSelect }: { entry: TreeEntry; isSelected: boolean; onSelect: () => void }) {
  const { node, depth, isLastChild, ancestorContinues } = entry;
  return (
    <button
      type="button"
      className={`trace-row${isSelected ? " trace-row-selected" : ""}`}
      style={{ "--kind-color": kindColors[node.kind] } as CSSProperties}
      onClick={onSelect}
    >
      <TreeConnectors depth={depth} isLastChild={isLastChild} ancestorContinues={ancestorContinues} />
      <KindBadge kind={node.kind} />
      <span className="trace-row-label">{node.label}</span>
      {node.durationMs !== null && (
        <span className="trace-row-duration">{formatDuration(node.durationMs)}</span>
      )}
      <StatusIcon status={node.status} />
    </button>
  );
}

/** Waterfall trace tree — renders the flow graph as an indented, hierarchical list. */
export function TraceTree({ flowGraph, selectedNodeId, onSelectNode }: TraceTreeProps) {
  const treeEntries = buildTreeEntries(flowGraph);
  return (
    <div className="trace-list">
      {treeEntries.map((entry) => (
        <TraceRow
          key={entry.node.id}
          entry={entry}
          isSelected={entry.node.id === selectedNodeId}
          onSelect={() => onSelectNode(entry.node.id)}
        />
      ))}
    </div>
  );
}

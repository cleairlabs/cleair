import type { CSSProperties, ReactElement } from "react";
import { kindColors } from "../kinds";
import { formatDuration } from "../traceTree";
import type { TraceTreeState, FlowNode, FlowNodeKind, FlowNodeStatus } from "../types";

type TraceTreeProps = {
  traceTree: TraceTreeState;
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

function buildChildrenMap(graph: TraceTreeState): Record<string, string[]> {
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
function buildTreeEntries(graph: TraceTreeState): TreeEntry[] {
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

/** Eclipse — represents a top-level trace. */
function TraceIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10">
      <path fill="#000000" fillRule="evenodd" d="M9,5 A4,4,0,1,0,1,5 A4,4,0,1,0,9,5 M9.5,5 A3,3,0,1,0,3.5,5 A3,3,0,1,0,9.5,5"/>
      <circle cx="5" cy="5" r="4" fill="none" stroke="#000000" strokeWidth="1"/>
    </svg>
  );
}

/** Agent/robot — represents AI/agent/robot. */
function AgentIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <line x1="6" y1="0.2" x2="6" y2="1.7" stroke="#fff" strokeWidth="1.1" strokeLinecap="round" />
      <circle cx="6" cy="0.2" r="0.85" fill="#fff" />
      <rect x="0.3" y="1.6" width="11.4" height="10.2" rx="1.8" fill="#fff" />
      <circle cx="3.9" cy="6.4" r="1.05" fill="#000" />
      <circle cx="8.1" cy="6.4" r="1.05" fill="#000" />
    </svg>
  );
}

/** Sparkle — represents intelligence. */
function IntelligenceIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="#ffffff">
      <path d="M5 0 L6.2 3.8 L10 5 L6.2 6.2 L5 10 L3.8 6.2 L0 5 L3.8 3.8 Z" />
    </svg>
  );
}

/** Magnifying glass — represents search and retrieval. */
function SearchIcon() {
  return (
    <svg
      width="10"
      height="10"
      viewBox="0 0 10 10"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    >
      <circle cx="4.2" cy="4.2" r="2.8" />
      <line x1="6.2" y1="6.2" x2="9.5" y2="9.5" />
    </svg>
  );
}

/** Terminal prompt — represents function/tool execution. */
function ToolIcon() {
  return (
    <svg
      width="10"
      height="10"
      viewBox="0 0 10 10"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="1,2.5 4.5,5 1,7.5" />
      <line x1="5.5" y1="7.5" x2="9" y2="7.5" />
    </svg>
  );
}

/** Person silhouette — represents a human action. */
function HumanIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
      <circle cx="5" cy="2.7" r="1.8" />
      <path d="M1.8 9c0-2 1.6-3.5 3.2-3.5s3.2 1.5 3.2 3.5H1.8z" />
    </svg>
  );
}

const kindIcons: Record<FlowNodeKind, () => ReactElement> = {
  trace:        TraceIcon,
  agent:        AgentIcon,
  intelligence: IntelligenceIcon,
  search:       SearchIcon,
  tool:         ToolIcon,
  human:        HumanIcon,
};

function KindBadge({ kind }: { kind: FlowNodeKind }) {
  const Icon = kindIcons[kind];
  return (
    <span className={`kind-badge kind-badge-${kind}`} style={{ background: kindColors[kind] }}>
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

export function getConnectorClasses(
  depth: number,
  isLastChild: boolean,
  ancestorContinues: boolean[]
): string[] {
  return Array.from({ length: depth }, (_, columnIndex) => {
    const isImmediateConnector = columnIndex === depth - 1;
    if (isImmediateConnector) {
      return isLastChild ? "connector-last" : "connector-mid";
    }
    const ancestorAtThisColumnContinues = ancestorContinues[columnIndex + 1] ?? false;
    return ancestorAtThisColumnContinues ? "connector-pass" : "connector-empty";
  });
}

function TreeConnectors({ depth, isLastChild, ancestorContinues }: Omit<TreeEntry, "node">) {
  const connectorClasses = getConnectorClasses(depth, isLastChild, ancestorContinues);
  return (
    <div className="tree-connectors">
      {connectorClasses.map((connectorClass, columnIndex) => (
        <div key={columnIndex} className={connectorClass} />
      ))}
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
export function TraceTree({ traceTree, selectedNodeId, onSelectNode }: TraceTreeProps) {
  const treeEntries = buildTreeEntries(traceTree);
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

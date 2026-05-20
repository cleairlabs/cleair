import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type UIEvent } from "react";
import { typeColors } from "../nodeTypes";
import { formatDuration } from "../traceTree";
import type { TraceTreeState, FlowNode, FlowNodeStatus } from "../types";
import { TypeBadge } from "./FlowNodeBadge";
import type { TraceViewProps } from "./traceViewTypes";

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

export function isScrolledToBottom(scrollContainer: Pick<HTMLElement, "scrollHeight" | "clientHeight" | "scrollTop">): boolean {
  return scrollContainer.scrollHeight - scrollContainer.clientHeight - scrollContainer.scrollTop <= 4;
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
      style={{ "--type-color": typeColors[node.type] } as CSSProperties}
      onClick={onSelect}
    >
      <TreeConnectors depth={depth} isLastChild={isLastChild} ancestorContinues={ancestorContinues} />
      <TypeBadge type={node.type} />
      <span className="trace-row-label">{node.label}</span>
      {node.durationMs !== null && (
        <span className="trace-row-duration">{formatDuration(node.durationMs)}</span>
      )}
      <StatusIcon status={node.status} />
    </button>
  );
}

/** Waterfall trace tree — renders the flow graph as an indented, hierarchical list. */
export function TraceTree({ traceTree, selectedNodeId, onSelectNode }: TraceViewProps) {
  const traceListRef = useRef<HTMLDivElement | null>(null);
  const [isFollowingBottom, setIsFollowingBottom] = useState(true);
  const treeEntries = buildTreeEntries(traceTree);

  useEffect(() => {
    setIsFollowingBottom(true);
  }, [traceTree.runId]);

  useLayoutEffect(() => {
    if (!isFollowingBottom || traceListRef.current === null) {
      return;
    }
    traceListRef.current.scrollTop = traceListRef.current.scrollHeight;
  }, [isFollowingBottom, treeEntries.length]);

  const onTraceListScroll = (event: UIEvent<HTMLDivElement>) => {
    setIsFollowingBottom(isScrolledToBottom(event.currentTarget));
  };

  return (
    <div ref={traceListRef} className="trace-list" onScroll={onTraceListScroll}>
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

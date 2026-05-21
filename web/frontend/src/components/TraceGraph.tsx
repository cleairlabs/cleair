import { useEffect, useMemo, useRef, useState } from "react";
import { DataSet, Network } from "vis-network/standalone";
import { typeColors } from "../nodeTypes";
import type { FlowNode, TraceTreeState } from "../types";
import type { TraceViewProps } from "./traceViewTypes";

type GraphNodeType = FlowNode["type"] | "start" | "end";

type GraphNode = {
  id: string;
  label: string;
  type: GraphNodeType;
  flowNodeIds: string[];
  x?: number;
  y?: number;
  fixed?: boolean;
};

type GraphEdge = {
  id: string;
  from: string;
  to: string;
};

type ExecutionStep = {
  id: string;
  label: string;
  type: GraphNodeType;
  flowNodeId: string | null;
};

const GRAPH_START_NODE_POSITION = { x: -220, y: -40 };
const GRAPH_END_NODE_POSITION = { x: 0, y: -220 };
const GRAPH_NODE_MARGIN = { top: 16, right: 16, bottom: 16, left: 16 };
const GRAPH_NODE_BORDER_WIDTH = 1.5;
const GRAPH_NODE_BORDER_WIDTH_SELECTED = 3;
const GRAPH_NODE_FONT_SIZE = 16;
const GRAPH_EDGE_WIDTH = 1.8;
const GRAPH_EDGE_WIDTH_SELECTED = 3.2;
const GRAPH_EDGE_COLOR = "rgba(110, 110, 110, 0.72)";
const GRAPH_EDGE_ROUNDNESS = 0.16;
const GRAPH_LAYOUT_RANDOM_SEED = 4;
const GRAPH_PHYSICS_GRAVITATIONAL_CONSTANT = -2800;
const GRAPH_PHYSICS_SPRING_LENGTH = 140;
const GRAPH_PHYSICS_SPRING_CONSTANT = 0.04;
const GRAPH_PHYSICS_DAMPING = 0.2;
const GRAPH_PHYSICS_STABILIZATION_ITERATIONS = 250;
const GRAPH_START_NODE_BACKGROUND_LIGHT = "#d7ead7";
const GRAPH_START_NODE_BACKGROUND_DARK = "#1e2a1e";
const GRAPH_START_NODE_BORDER = "#69b26b";
const GRAPH_END_NODE_BACKGROUND_LIGHT = "#f2dddd";
const GRAPH_END_NODE_BACKGROUND_DARK = "#2b1f1f";
const GRAPH_END_NODE_BORDER = "#d48484";
const GRAPH_SELECTED_BACKGROUND_LIGHT = "#d9dde3";
const GRAPH_SELECTED_BACKGROUND_DARK = "#2a2f36";

type GraphNodeAppearance = {
  background: string;
  border: string;
};

function buildChildrenMap(traceTree: TraceTreeState): Record<string, string[]> {
  const childrenByParentId: Record<string, string[]> = {};
  for (const nodeId of traceTree.nodeIdsInOrder) {
    const node = traceTree.nodesById[nodeId];
    if (!node) continue;
    const parentKey = node.parentId ?? "";
    childrenByParentId[parentKey] ??= [];
    childrenByParentId[parentKey].push(nodeId);
  }
  return childrenByParentId;
}

function isTemporaryRootNode(traceTree: TraceTreeState, node: FlowNode): boolean {
  return node.parentId === null || traceTree.nodesById[node.parentId] === undefined;
}

function graphNodeId(type: GraphNodeType, label: string) {
  return `${type}:${label}`;
}

function cssVariableColor(name: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function isDarkTheme() {
  return document.documentElement.dataset.theme === "dark";
}

function buildExecutionSequence(traceTree: TraceTreeState) {
  const childrenByParentId = buildChildrenMap(traceTree);
  const executionSequence: ExecutionStep[] = [{ id: "__start__", label: "__start__", type: "start", flowNodeId: null }];
  const rootNodeIds = traceTree.nodeIdsInOrder.filter((nodeId) => {
    const node = traceTree.nodesById[nodeId];
    return node !== undefined && isTemporaryRootNode(traceTree, node);
  });

  function visit(nodeId: string) {
    const node = traceTree.nodesById[nodeId];
    if (!node) return;
    const currentGraphNodeId = graphNodeId(node.type, node.label);
    executionSequence.push({ id: currentGraphNodeId, label: node.label, type: node.type, flowNodeId: node.id });
    for (const childNodeId of childrenByParentId[nodeId] ?? []) {
      visit(childNodeId);
      executionSequence.push({ id: currentGraphNodeId, label: node.label, type: node.type, flowNodeId: node.id });
    }
  }

  for (const rootNodeId of rootNodeIds) {
    visit(rootNodeId);
  }
  executionSequence.push({ id: "__end__", label: "__end__", type: "end", flowNodeId: null });
  return executionSequence;
}

export function buildGraphData(traceTree: TraceTreeState): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const executionSequence = buildExecutionSequence(traceTree);
  const graphNodesById: Record<string, GraphNode> = {
    __start__: { id: "__start__", label: "__start__", type: "start", flowNodeIds: [], x: GRAPH_START_NODE_POSITION.x, y: GRAPH_START_NODE_POSITION.y, fixed: true },
    __end__: { id: "__end__", label: "__end__", type: "end", flowNodeIds: [], x: GRAPH_END_NODE_POSITION.x, y: GRAPH_END_NODE_POSITION.y, fixed: true },
  };
  const graphEdgesById: Record<string, GraphEdge> = {};

  for (const executionStep of executionSequence) {
    graphNodesById[executionStep.id] ??= {
      id: executionStep.id,
      label: executionStep.label,
      type: executionStep.type,
      flowNodeIds: [],
    };
    if (executionStep.flowNodeId && !graphNodesById[executionStep.id].flowNodeIds.includes(executionStep.flowNodeId)) {
      graphNodesById[executionStep.id].flowNodeIds.push(executionStep.flowNodeId);
    }
  }

  for (let stepIndex = 0; stepIndex < executionSequence.length - 1; stepIndex++) {
    const [fromNodeId, toNodeId] = [executionSequence[stepIndex].id, executionSequence[stepIndex + 1].id].sort();
    const edgeId = `${fromNodeId}:${toNodeId}`;
    graphEdgesById[edgeId] ??= {
      id: edgeId,
      from: fromNodeId,
      to: toNodeId,
    };
  }

  return { nodes: Object.values(graphNodesById), edges: Object.values(graphEdgesById) };
}

function graphNodeColor(type: GraphNodeType) {
  if (type === "start") return { background: isDarkTheme() ? GRAPH_START_NODE_BACKGROUND_DARK : GRAPH_START_NODE_BACKGROUND_LIGHT, border: GRAPH_START_NODE_BORDER };
  if (type === "end") return { background: isDarkTheme() ? GRAPH_END_NODE_BACKGROUND_DARK : GRAPH_END_NODE_BACKGROUND_LIGHT, border: GRAPH_END_NODE_BORDER };
  const borderColor = cssVariableColor(typeColors[type].slice(4, -1));
  return { background: cssVariableColor("--surface"), border: borderColor };
}

function graphSelectedBackground() {
  return isDarkTheme() ? GRAPH_SELECTED_BACKGROUND_DARK : GRAPH_SELECTED_BACKGROUND_LIGHT;
}

function graphSelectedNodeColor(type: GraphNodeType): GraphNodeAppearance {
  return { ...graphNodeColor(type), background: graphSelectedBackground() };
}

function selectedGraphNodeId(graphNodes: GraphNode[], selectedNodeId: string | null) {
  if (selectedNodeId === null) return null;
  return graphNodes.find((graphNode) => graphNode.flowNodeIds.includes(selectedNodeId))?.id ?? null;
}

export function TraceGraph({ traceTree, selectedNodeId, onSelectNode }: TraceViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const networkRef = useRef<Network | null>(null);
  const graphNodesRef = useRef<DataSet<any> | null>(null);
  const graphEdgesRef = useRef<DataSet<any> | null>(null);
  const [themeName, setThemeName] = useState(document.documentElement.dataset.theme ?? "light");
  const graphData = useMemo(() => buildGraphData(traceTree), [traceTree]);
  const selectedGraphNode = useMemo(() => selectedGraphNodeId(graphData.nodes, selectedNodeId), [graphData.nodes, selectedNodeId]);

  useEffect(() => {
    const observer = new MutationObserver(() => setThemeName(document.documentElement.dataset.theme ?? "light"));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    const textColor = cssVariableColor("--text");
    const graphNodeColorsById = Object.fromEntries(graphData.nodes.map((graphNode) => [graphNode.id, graphNodeColor(graphNode.type)]));
    const graphNodes = new DataSet<any>(graphData.nodes.map((graphNode) => ({
      ...graphNode,
      shape: "box",
      margin: GRAPH_NODE_MARGIN,
      borderWidth: GRAPH_NODE_BORDER_WIDTH,
      color: graphNodeColorsById[graphNode.id],
      font: { face: "Geist Mono, JetBrains Mono, monospace", size: GRAPH_NODE_FONT_SIZE, color: textColor },
      chosen: false,
    })));
    const graphEdges = new DataSet<any>(graphData.edges.map((graphEdge) => ({
      ...graphEdge,
      width: GRAPH_EDGE_WIDTH,
      color: GRAPH_EDGE_COLOR,
      smooth: { enabled: true, type: "curvedCW", roundness: GRAPH_EDGE_ROUNDNESS },
    })));
    const network = new Network(containerRef.current, { nodes: graphNodes, edges: graphEdges }, {
      autoResize: true,
      interaction: { dragNodes: false },
      layout: { randomSeed: GRAPH_LAYOUT_RANDOM_SEED },
      nodes: { shape: "box", borderWidthSelected: GRAPH_NODE_BORDER_WIDTH_SELECTED },
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: GRAPH_PHYSICS_GRAVITATIONAL_CONSTANT,
          springLength: GRAPH_PHYSICS_SPRING_LENGTH,
          springConstant: GRAPH_PHYSICS_SPRING_CONSTANT,
          damping: GRAPH_PHYSICS_DAMPING,
        },
        stabilization: { enabled: true, iterations: GRAPH_PHYSICS_STABILIZATION_ITERATIONS, fit: true },
      },
    });
    network.on("click", (event) => {
      const clickedNodeId = typeof event.nodes[0] === "string" ? event.nodes[0] : null;
      if (!clickedNodeId) return;
      const clickedNode = graphData.nodes.find((graphNode) => graphNode.id === clickedNodeId);
      const selectedFlowNodeId = clickedNode?.flowNodeIds[0];
      if (selectedFlowNodeId) {
        onSelectNode(selectedFlowNodeId);
      }
    });
    graphNodesRef.current = graphNodes;
    graphEdgesRef.current = graphEdges;
    networkRef.current = network;
    return () => {
      network.destroy();
      graphNodesRef.current = null;
      graphEdgesRef.current = null;
      networkRef.current = null;
    };
  }, [graphData, onSelectNode, themeName]);

  useEffect(() => {
    const graphNodes = graphNodesRef.current;
    const graphEdges = graphEdgesRef.current;
    if (!graphNodes || !graphEdges) return;
    graphNodes.update(graphData.nodes.map((graphNode) => ({
      id: graphNode.id,
      borderWidth: graphNode.id === selectedGraphNode ? GRAPH_NODE_BORDER_WIDTH_SELECTED : GRAPH_NODE_BORDER_WIDTH,
      color: graphNode.id === selectedGraphNode ? graphSelectedNodeColor(graphNode.type) : graphNodeColor(graphNode.type),
    })));
    graphEdges.update(graphData.edges.map((graphEdge) => ({
      id: graphEdge.id,
      width: selectedGraphNode && (graphEdge.from === selectedGraphNode || graphEdge.to === selectedGraphNode) ? GRAPH_EDGE_WIDTH_SELECTED : GRAPH_EDGE_WIDTH,
    })));
  }, [graphData.nodes, selectedGraphNode, themeName]);

  return (
    <div className="trace-graph">
      <div ref={containerRef} className="trace-graph-canvas" />
    </div>
  );
}

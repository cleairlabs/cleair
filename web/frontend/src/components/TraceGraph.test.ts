import { describe, expect, test } from "vitest";
import { buildGraphData } from "./TraceGraph";
import type { TraceTreeState } from "../types";

function createTraceTreeState(): TraceTreeState {
  return {
    runId: "run-1",
    runLabel: "Agent",
    isCompleted: true,
    nodeIdsInOrder: ["root", "child"],
    nodesById: {
      root: { id: "root", parentId: null, label: "agent", subtitle: "Agent", type: "agent", status: "done", durationMs: 20, output: null },
      child: { id: "child", parentId: "root", label: "tool", subtitle: "Agent", type: "tool", status: "done", durationMs: 10, output: null },
    },
  };
}

describe("buildGraphData", () => {
  test("deduplicates repeated steps and collapses connections between nodes", () => {
    const graphData = buildGraphData(createTraceTreeState());

    expect(graphData.nodes.map((graphNode) => graphNode.label).sort()).toEqual(["__end__", "__start__", "agent", "tool"]);
    expect(graphData.nodes.find((graphNode) => graphNode.id === "agent:agent")?.flowNodeIds).toEqual(["root"]);
    expect(graphData.edges.map((graphEdge) => [graphEdge.from, graphEdge.to]).sort()).toEqual([
      ["__end__", "agent:agent"],
      ["__start__", "agent:agent"],
      ["agent:agent", "tool:tool"],
    ]);
  });
});

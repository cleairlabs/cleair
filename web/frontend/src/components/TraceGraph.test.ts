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
      root: {
        id: "root",
        parentId: null,
        label: "agent",
        subtitle: "Agent",
        type: "agent",
        status: "done",
        durationMs: 20,
        input: null,
        output: null,
      },
      child: {
        id: "child",
        parentId: "root",
        label: "tool",
        subtitle: "Agent",
        type: "tool",
        status: "done",
        durationMs: 10,
        input: null,
        output: null,
      },
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

  test("treats nodes with missing parents as temporary roots", () => {
    const graphData = buildGraphData({
      runId: "run-1",
      runLabel: "Agent",
      isCompleted: false,
      nodeIdsInOrder: ["research", "call-llm"],
      nodesById: {
        research: {
          id: "research",
          parentId: "main",
          label: "research",
          subtitle: "Agent",
          type: "agent",
          status: "done",
          durationMs: 20,
          input: null,
          output: null,
        },
        "call-llm": {
          id: "call-llm",
          parentId: "research",
          label: "tool",
          subtitle: "Agent",
          type: "tool",
          status: "done",
          durationMs: 10,
          input: null,
          output: null,
        },
      },
    });

    expect(graphData.nodes.map((graphNode) => graphNode.label).sort()).toEqual(["__end__", "__start__", "research", "tool"]);
    expect(graphData.edges.map((graphEdge) => [graphEdge.from, graphEdge.to]).sort()).toEqual([
      ["__end__", "agent:research"],
      ["__start__", "agent:research"],
      ["agent:research", "tool:tool"],
    ]);
  });
});

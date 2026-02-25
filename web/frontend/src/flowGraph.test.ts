import { describe, expect, test } from "vitest";
import { applyFlowGraphEvent, createEmptyFlowGraph, formatDuration } from "./flowGraph";

describe("flow graph reducer", () => {
  test("applies core events", () => {
    let graph = createEmptyFlowGraph("run-1", "test run");

    graph = applyFlowGraphEvent(graph, {
      type: "node_added",
      node: { id: "a", parentId: null, label: "A", subtitle: "start", kind: "agent", whatDescription: "start", whyDescription: "begin" },
    });

    graph = applyFlowGraphEvent(graph, {
      type: "node_added",
      node: { id: "b", parentId: "a", label: "B", subtitle: "end", kind: "tool", whatDescription: "end", whyDescription: "done" },
    });

    graph = applyFlowGraphEvent(graph, { type: "node_status_changed", nodeId: "b", status: "running" });
    graph = applyFlowGraphEvent(graph, { type: "node_status_changed", nodeId: "b", status: "done" });
    graph = applyFlowGraphEvent(graph, { type: "node_finished", nodeId: "b", durationMs: 420 });
    graph = applyFlowGraphEvent(graph, { type: "run_completed" });

    expect(graph.nodeIdsInOrder).toEqual(["a", "b"]);
    expect(graph.nodesById.b.status).toBe("done");
    expect(graph.nodesById.b.durationMs).toBe(420);
    expect(graph.isCompleted).toBe(true);
  });

  test("ignores duplicate node_added", () => {
    let graph = createEmptyFlowGraph("run-1", "test");
    const nodeEvent = {
      type: "node_added" as const,
      node: { id: "x", parentId: null, label: "X", subtitle: "", kind: "agent" as const, whatDescription: "", whyDescription: "" },
    };
    graph = applyFlowGraphEvent(graph, nodeEvent);
    graph = applyFlowGraphEvent(graph, nodeEvent);
    expect(graph.nodeIdsInOrder).toHaveLength(1);
  });

  test("ignores status change to same status", () => {
    let graph = createEmptyFlowGraph("run-1", "test");
    graph = applyFlowGraphEvent(graph, {
      type: "node_added",
      node: { id: "x", parentId: null, label: "X", subtitle: "", kind: "agent", whatDescription: "", whyDescription: "" },
    });
    const before = graph;
    graph = applyFlowGraphEvent(graph, { type: "node_status_changed", nodeId: "x", status: "idle" });
    expect(graph).toBe(before);
  });
});

describe("formatDuration", () => {
  test("formats milliseconds below 1000", () => {
    expect(formatDuration(0)).toBe("0ms");
    expect(formatDuration(420)).toBe("420ms");
    expect(formatDuration(999)).toBe("999ms");
  });

  test("formats seconds at 1000ms and above", () => {
    expect(formatDuration(1000)).toBe("1.00s");
    expect(formatDuration(2830)).toBe("2.83s");
  });
});

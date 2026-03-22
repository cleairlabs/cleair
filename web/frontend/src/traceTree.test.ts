import { describe, expect, test } from "vitest";
import { applyTraceTreeEvent, createEmptyTraceTree, formatDuration } from "./traceTree";

describe("flow graph reducer", () => {
  test("run_started resets graph to a new empty graph", () => {
    let graph = createEmptyTraceTree("old-run", "OldAgent");
    graph = applyTraceTreeEvent(graph, {
      type: "node_added",
      node: { id: "x", parentId: null, label: "X", subtitle: "", kind: "agent", whatDescription: "" },
    });
    graph = applyTraceTreeEvent(graph, { type: "run_started", runId: "new-run", runLabel: "NewAgent" });
    expect(graph.runId).toBe("new-run");
    expect(graph.runLabel).toBe("NewAgent");
    expect(graph.nodeIdsInOrder).toHaveLength(0);
    expect(graph.isCompleted).toBe(false);
  });

  test("applies core events", () => {
    let graph = createEmptyTraceTree("run-1", "test run");

    graph = applyTraceTreeEvent(graph, {
      type: "node_added",
      node: { id: "a", parentId: null, label: "A", subtitle: "start", kind: "agent", whatDescription: "start" },
    });

    graph = applyTraceTreeEvent(graph, {
      type: "node_added",
      node: { id: "b", parentId: "a", label: "B", subtitle: "end", kind: "tool", whatDescription: "end" },
    });

    graph = applyTraceTreeEvent(graph, { type: "node_status_changed", nodeId: "b", status: "running" });
    graph = applyTraceTreeEvent(graph, { type: "node_status_changed", nodeId: "b", status: "done" });
    graph = applyTraceTreeEvent(graph, { type: "node_finished", nodeId: "b", durationMs: 420 });
    graph = applyTraceTreeEvent(graph, { type: "run_completed" });

    expect(graph.nodeIdsInOrder).toEqual(["a", "b"]);
    expect(graph.nodesById.b.status).toBe("done");
    expect(graph.nodesById.b.durationMs).toBe(420);
    expect(graph.isCompleted).toBe(true);
  });

  test("ignores duplicate node_added", () => {
    let graph = createEmptyTraceTree("run-1", "test");
    const nodeEvent = {
      type: "node_added" as const,
      node: { id: "x", parentId: null, label: "X", subtitle: "", kind: "agent" as const, whatDescription: "" },
    };
    graph = applyTraceTreeEvent(graph, nodeEvent);
    graph = applyTraceTreeEvent(graph, nodeEvent);
    expect(graph.nodeIdsInOrder).toHaveLength(1);
  });

  test("ignores status change to same status", () => {
    let graph = createEmptyTraceTree("run-1", "test");
    graph = applyTraceTreeEvent(graph, {
      type: "node_added",
      node: { id: "x", parentId: null, label: "X", subtitle: "", kind: "agent", whatDescription: "" },
    });
    const before = graph;
    graph = applyTraceTreeEvent(graph, { type: "node_status_changed", nodeId: "x", status: "idle" });
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

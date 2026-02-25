import { describe, expect, test } from "vitest";
import { applyFlowGraphEvent, createEmptyFlowGraph } from "./flowGraph";

describe("flow graph reducer", () => {
  test("applies core events", () => {
    let flowGraph = createEmptyFlowGraph("run-1", "test run");

    flowGraph = applyFlowGraphEvent(flowGraph, {
      type: "node_added",
      node: {
        id: "a",
        label: "A",
        subtitle: "start",
        x: 0,
        y: 0,
        kind: "agent",
        whatDescription: "start",
        whyDescription: "begin"
      }
    });

    flowGraph = applyFlowGraphEvent(flowGraph, {
      type: "node_added",
      node: {
        id: "b",
        label: "B",
        subtitle: "end",
        x: 0,
        y: 100,
        kind: "agent",
        whatDescription: "end",
        whyDescription: "done"
      }
    });

    flowGraph = applyFlowGraphEvent(flowGraph, {
      type: "edge_added",
      edge: { fromNodeId: "a", toNodeId: "b" }
    });

    flowGraph = applyFlowGraphEvent(flowGraph, {
      type: "node_status_changed",
      nodeId: "b",
      status: "done"
    });

    flowGraph = applyFlowGraphEvent(flowGraph, { type: "run_completed" });

    expect(flowGraph.nodeIdsInRenderOrder).toEqual(["a", "b"]);
    expect(flowGraph.flowEdges).toHaveLength(1);
    expect(flowGraph.nodesById.b.status).toBe("done");
    expect(flowGraph.isCompleted).toBe(true);
  });
});

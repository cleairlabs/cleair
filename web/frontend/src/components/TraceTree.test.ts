import { describe, expect, test } from "vitest";
import { buildTreeEntries, getConnectorClasses, isScrolledToBottom } from "./TraceTree";

describe("getConnectorClasses", () => {
  test("uses the parent-continuation flag for the first pass-through column", () => {
    const connectorClasses = getConnectorClasses(2, true, [false, true]);
    expect(connectorClasses).toEqual(["connector-pass", "connector-last"]);
  });

  test("renders an empty pass-through when parent branch does not continue", () => {
    const connectorClasses = getConnectorClasses(2, false, [true, false]);
    expect(connectorClasses).toEqual(["connector-empty", "connector-mid"]);
  });

  test("supports deeper nesting with mixed ancestor continuation", () => {
    const connectorClasses = getConnectorClasses(4, true, [false, true, false, true]);
    expect(connectorClasses).toEqual([
      "connector-pass",
      "connector-empty",
      "connector-pass",
      "connector-last",
    ]);
  });
});

describe("isScrolledToBottom", () => {
  test("returns true when the scroll position is at the bottom", () => {
    expect(isScrolledToBottom({ scrollHeight: 400, clientHeight: 100, scrollTop: 300 })).toBe(true);
  });

  test("returns true when the scroll position is within the bottom tolerance", () => {
    expect(isScrolledToBottom({ scrollHeight: 400, clientHeight: 100, scrollTop: 297 })).toBe(true);
  });

  test("returns false when the user has scrolled away from the bottom", () => {
    expect(isScrolledToBottom({ scrollHeight: 400, clientHeight: 100, scrollTop: 280 })).toBe(false);
  });
});

describe("buildTreeEntries", () => {
  test("treats nodes with missing parents as temporary roots", () => {
    const entries = buildTreeEntries({
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
          durationMs: 10,
          output: null,
        },
        "call-llm": {
          id: "call-llm",
          parentId: "research",
          label: "call_llm",
          subtitle: "Agent",
          type: "tool",
          status: "done",
          durationMs: 5,
          output: null,
        },
      },
    });

    expect(entries.map((entry) => [entry.node.id, entry.depth])).toEqual([
      ["research", 0],
      ["call-llm", 1],
    ]);
  });
});
